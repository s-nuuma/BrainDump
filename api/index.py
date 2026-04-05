import os
import json
import tempfile
import traceback
import time
import sys
from typing import List, Optional
from datetime import datetime, timezone

# FastAPI関連のみインポート（これが失敗する場合はランタイムの問題）
try:
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
except ImportError as e:
    print(f"CRITICAL: Failed to import FastAPI core: {e}")
    raise

app = FastAPI(title="BrainDump AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# --- Lazy Initialization Helpers ---

def get_gemini_client():
    from google import genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set.")
    return genai.Client(api_key=api_key)

def get_db():
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    creds_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not creds_json:
        return None
    try:
        try:
            firebase_admin.get_app()
        except ValueError:
            if creds_json.strip().startswith('{'):
                creds_dict = json.loads(creds_json)
                cred = credentials.Certificate(creds_dict)
            else:
                cred = credentials.Certificate(creds_json)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"Firebase Init Error: {e}")
        return None

# --- Routes ---

@app.get("/")
@app.get("/api")
@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok", 
        "python": sys.version,
        "api": "BrainDump AI Engine"
    }

@app.post("/transcribe")
@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    from google.genai import types
    client = get_gemini_client()
    
    if not file.filename.endswith(('.webm', '.mp3', '.wav', '.m4a')):
        raise HTTPException(status_code=400, detail="Unsupported format")
        
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp:
            content = await file.read()
            temp.write(content)
            temp_path = temp.name
            
        audio_file = client.files.upload(file=temp_path, config={'mime_type': 'audio/webm'})
        while audio_file.state.name == "PROCESSING":
            time.sleep(2)
            audio_file = client.files.get(name=audio_file.name)
            
        if audio_file.state.name == "FAILED":
            raise Exception("Gemini process failed")

        prompt = "文字起こし結果のみをJSON {'content': '...'} で出力してください。"
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, audio_file],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TranscribeResponse,
            )
        )
        try:
            os.unlink(temp_path)
            client.files.delete(name=audio_file.name)
        except: pass

        return {"status": "success", "data": json.loads(response.text)}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/entries")
@app.get("/api/entries")
async def get_entries(user_id: str, limit: int = 50, tag: Optional[str] = None):
    from firebase_admin import firestore
    db = get_db()
    if db is None: raise HTTPException(status_code=500, detail="DB Error")
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

@app.post("/dump")
@app.post("/api/dump")
async def process_dump(request: DumpRequest):
    from google.genai import types
    client = get_gemini_client()
    db = get_db()
    try:
        prompt = f"分析結果をJSONで出力: {request.content}"
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EntryData,
            )
        )
        data = json.loads(response.text)
        data["content"] = request.content
        
        emb = client.models.embed_content(
            model="gemini-embedding-001",
            contents=f"{data.get('summary')}\n{request.content}",
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        
        if db is not None:
            doc = {
                "user_id": request.user_id,
                "content": request.content,
                "summary": data.get("summary", ""),
                "topic": data.get("topic", []),
                "sentiment": data.get("sentiment", {}),
                "is_actionable": data.get("is_actionable", False),
                "created_at": datetime.now(timezone.utc),
                "embedding": emb.embeddings[0].values
            }
            _, ref = db.collection("entries").add(doc)
            data["id"] = ref.id
            
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/insights")
@app.get("/api/insights")
async def get_insights(user_id: str, days: int = 30):
    from firebase_admin import firestore
    from datetime import timedelta
    db = get_db()
    if db is None: raise HTTPException(status_code=500, detail="DB Error")
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        docs = db.collection("entries").where(filter=firestore.FieldFilter("user_id", "==", user_id)).stream()
        entries = []
        for doc in docs:
            d = doc.to_dict()
            if d.get("created_at") and d["created_at"] >= cutoff:
                entries.append(d)
        
        # 集計ロジック...
        return {"status": "success", "data": {"total": len(entries)}} # ひとまず
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/generate-answer")
@app.post("/api/chat/generate-answer")
async def generate_answer(request: ChatRequest):
    client = get_gemini_client()
    db = get_db()
    from google.cloud.firestore_v1.vector import Vector
    from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
    from firebase_admin import firestore
    
    if db is None: raise HTTPException(status_code=500)
    try:
        q_emb = client.models.embed_content(
            model="gemini-embedding-001",
            contents=request.query,
            config={"output_dimensionality": 768}
        )
        
        query = db.collection("entries").where(filter=firestore.FieldFilter("user_id", "==", request.user_id)).find_nearest(
            vector_field="embedding",
            query_vector=Vector(q_emb.embeddings[0].values),
            distance_measure=DistanceMeasure.COSINE,
            limit=3
        )
        docs = query.stream()
        ctx = [d.to_dict().get('summary') for d in docs]
        
        res = client.models.generate_content(model="gemini-2.5-pro", contents=f"記録: {ctx}\n質問: {request.query}")
        return {"answer": res.text, "sources": []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
