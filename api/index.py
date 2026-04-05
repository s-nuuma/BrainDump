import os
import json
import tempfile
import traceback
import time
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

app = FastAPI(title="BrainDump AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Lazy Initialization ---
_gemini_client = None
_db = None

def get_gemini_client():
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client

def get_db():
    global _db
    if _db is not None:
        return _db
    creds_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        return None
    try:
        if creds_json.strip().startswith('{'):
            creds_dict = json.loads(creds_json)
            cred = credentials.Certificate(creds_dict)
        else:
            cred = credentials.Certificate(creds_json)
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
        return _db
    except Exception as e:
        print(f"Firebase Init Error: {e}")
        return None

# --- Models ---
class Sentiment(BaseModel):
    score: float
    label: str

class EntryData(BaseModel):
    content: str
    summary: str
    topic: List[str]
    sentiment: Sentiment
    is_actionable: bool

class ChatRequest(BaseModel):
    query: str
    user_id: str

class TranscribeResponse(BaseModel):
    content: str

class DumpRequest(BaseModel):
    content: str
    user_id: str

# Gemini Configuration
MODEL_NAME = "gemini-2.5-flash"
CHAT_MODEL_NAME = "gemini-2.5-pro" 
EMBEDDING_MODEL_NAME = "gemini-embedding-001" 

# --- Routes ---

@app.get("/")
@app.get("/api")
async def root():
    return {"message": "BrainDump AI Engine is running"}

@app.get("/health")
@app.get("/api/health")
async def health():
    # ヘルスチェックは外部接続なしで即答
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/transcribe")
@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    client = get_gemini_client()
    if not file.filename.endswith(('.webm', '.mp3', '.wav', '.m4a')):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            content = await file.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
            
        audio_file = client.files.upload(file=temp_audio_path, config={'mime_type': 'audio/webm'})
        while audio_file.state.name == "PROCESSING":
            time.sleep(2)
            audio_file = client.files.get(name=audio_file.name)
            
        if audio_file.state.name == "FAILED":
            raise Exception("Gemini failed to process audio.")

        prompt = "音声内容を正確に文字起こしし、JSON形式で {'content': '...'} と出力してください。"
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt, audio_file],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TranscribeResponse,
            )
        )
        try:
            os.unlink(temp_audio_path)
            client.files.delete(name=audio_file.name)
        except: pass

        return {"status": "success", "data": json.loads(response.text)}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entries")
@app.get("/api/entries")
async def get_entries(user_id: str, limit: int = 50, tag: Optional[str] = None):
    db = get_db()
    if db is None: raise HTTPException(status_code=500, detail="DB not initialized")
    try:
        query = db.collection("entries").where(filter=firestore.FieldFilter("user_id", "==", user_id))
        if tag: query = query.where(filter=firestore.FieldFilter("topic", "array_contains", tag))
        docs = query.stream()
        entries = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if "embedding" in data: del data["embedding"]
            entries.append(data)
        entries.sort(key=lambda x: x.get("created_at", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        return {"status": "success", "data": entries[:limit]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/entries/{entry_id}")
@app.delete("/api/entries/{entry_id}")
async def delete_entry(entry_id: str, user_id: str):
    db = get_db()
    if db is None: raise HTTPException(status_code=500, detail="DB not initialized")
    try:
        doc_ref = db.collection("entries").document(entry_id)
        doc = doc_ref.get()
        if not doc.exists: raise HTTPException(status_code=404, detail="Not found")
        if doc.to_dict().get("user_id") != user_id: raise HTTPException(status_code=403)
        doc_ref.delete()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/export")
@app.get("/api/export")
async def export_entries(user_id: str):
    db = get_db()
    if db is None: raise HTTPException(status_code=500, detail="DB not initialized")
    try:
        docs = db.collection("entries").where(filter=firestore.FieldFilter("user_id", "==", user_id)).stream()
        entries = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if "embedding" in data: del data["embedding"]
            if "created_at" in data: data["created_at"] = data["created_at"].isoformat()
            entries.append(data)
        return JSONResponse(content={"data": entries})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/dump")
@app.post("/api/dump")
async def process_dump(request: DumpRequest):
    client = get_gemini_client()
    db = get_db()
    try:
        prompt = f"分析結果をJSON形式で出力してください: {request.content}"
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EntryData,
            )
        )
        structured_data = json.loads(response.text)
        structured_data["content"] = request.content
        
        emb_res = client.models.embed_content(
            model=EMBEDDING_MODEL_NAME,
            contents=f"{structured_data.get('summary')}\n{request.content}",
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        
        if db is not None:
            entry_doc = {
                "user_id": request.user_id,
                "content": request.content,
                "summary": structured_data.get("summary", ""),
                "topic": structured_data.get("topic", []),
                "sentiment": structured_data.get("sentiment", {}),
                "is_actionable": structured_data.get("is_actionable", False),
                "created_at": datetime.now(timezone.utc),
                "embedding": emb_res.embeddings[0].values
            }
            _, doc_ref = db.collection("entries").add(entry_doc)
            structured_data["id"] = doc_ref.id
            
        return {"status": "success", "data": structured_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights")
@app.get("/api/insights")
async def get_insights(user_id: str, days: int = 30):
    db = get_db()
    if db is None: raise HTTPException(status_code=500, detail="DB not initialized")
    try:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        docs = db.collection("entries").where(filter=firestore.FieldFilter("user_id", "==", user_id)).stream()
        
        entries = []
        for doc in docs:
            data = doc.to_dict()
            if data.get("created_at") and data["created_at"] >= cutoff:
                entries.append(data)
                
        daily_sentiment = {}
        topic_counts = {}
        action_count = 0
        
        for entry in entries:
            dt = entry["created_at"].strftime("%Y-%m-%d")
            score = entry.get("sentiment", {}).get("score", 0)
            if dt not in daily_sentiment: daily_sentiment[dt] = {"s": 0, "c": 0}
            daily_sentiment[dt]["s"] += score
            daily_sentiment[dt]["c"] += 1
            for t in entry.get("topic", []):
                topic_counts[t] = topic_counts.get(t, 0) + 1
            if entry.get("is_actionable"): action_count += 1
                
        sentiment_trend = [{"date": d, "score": round(daily_sentiment[d]["s"]/daily_sentiment[d]["c"], 2)} for d in sorted(daily_sentiment.keys())]
        top_topics = [{"topic": k, "count": v} for k, v in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        return {
            "status": "success",
            "data": {
                "sentiment_trend": sentiment_trend,
                "top_topics": top_topics,
                "total_entries": len(entries),
                "actionable_ratio": round(action_count / len(entries) * 100, 1) if entries else 0
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/generate-answer")
@app.post("/api/chat/generate-answer")
async def generate_answer(request: ChatRequest):
    client = get_gemini_client()
    db = get_db()
    if db is None: raise HTTPException(status_code=500, detail="DB not initialized")
    try:
        q_emb = client.models.embed_content(
            model=EMBEDDING_MODEL_NAME,
            contents=request.query,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        
        from google.cloud.firestore_v1.vector import Vector
        from google.cloud.firestore_v1.base_vector_query import DistanceMeasure

        vector_query = db.collection("entries").where(filter=firestore.FieldFilter("user_id", "==", user_id)).find_nearest(
            vector_field="embedding",
            query_vector=Vector(q_emb.embeddings[0].values),
            distance_measure=DistanceMeasure.COSINE,
            limit=5
        )
        docs = vector_query.stream()
        contexts = [f"Summary: {d.to_dict().get('summary')}\nContent: {d.to_dict().get('content')}" for d in docs]
        
        if not contexts:
            return {"answer": "該当する記録が見つかりませんでした。", "sources": []}

        prompt = f"以下の過去記録を元に答えてください:\n\n" + "\n---\n".join(contexts) + f"\n\n質問: {request.query}"
        response = client.models.generate_content(model=CHAT_MODEL_NAME, contents=prompt)
        return {"answer": response.text, "sources": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
