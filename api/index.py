import os
import json
import tempfile
import traceback
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

# Initialize Firebase Admin
# Vercelなどの本番環境では、環境変数 FIREBASE_SERVICE_ACCOUNT_JSON に JSON 文字列を直接入れることを推奨
firebase_creds_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

if firebase_creds_json:
    try:
        if firebase_creds_json.strip().startswith('{'):
            # JSON文字列として処理
            print("Initializing Firebase Admin with JSON string from environment variable...")
            creds_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(creds_dict)
        else:
            # ファイルパスとして処理
            print(f"Initializing Firebase Admin with file: {firebase_creds_json}...")
            cred = credentials.Certificate(firebase_creds_json)
            
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        print(f"Error initializing Firebase Admin: {e}")
        db = None
else:
    print("Warning: FIREBASE_SERVICE_ACCOUNT_JSON is not set. Firestore saving will be skipped.")
    db = None

# Initialize Gemini Client (new SDK)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY is not set.")
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI(title="BrainDump AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 本番環境では適切にドメインを指定してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
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
# 新しい google-genai SDK では最新の安定版モデル名を指定する必要があります。
# （現時点で API として最も安定している最新の gemini-2.5-flash またはそれ以降）
MODEL_NAME = "gemini-2.5-flash"
# RAGなど高い推論能力が求められる対話には Pro モデルを使用
CHAT_MODEL_NAME = "gemini-2.5-pro" 
# 新 SDK で対応している最新の Embedding モデルを指定
EMBEDDING_MODEL_NAME = "gemini-embedding-001" 

@app.get("/")
async def root():
    return {"message": "BrainDump AI Engine is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...)
):
    if not file.filename.endswith(('.webm', '.mp3', '.wav', '.m4a')):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    try:
        # 1. Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            content = await file.read()
            temp_audio.write(content)
            temp_audio_path = temp_audio.name
            
        file_size = os.path.getsize(temp_audio_path)
        print(f"Received audio file size: {file_size} bytes")
        if file_size == 0:
            raise Exception("Uploaded audio file is empty (0 bytes).")

        # 2. Upload to Gemini
        print(f"Uploading {temp_audio_path} to Gemini...")
        audio_file = client.files.upload(
            file=temp_audio_path,
            config={'mime_type': 'audio/webm'}
        )

        import time
        while audio_file.state.name == "PROCESSING":
            time.sleep(2)
            audio_file = client.files.get(name=audio_file.name)
            
        if audio_file.state.name == "FAILED":
            error_details = getattr(audio_file, 'error', 'Unknown Error')
            raise Exception(f"Gemini failed to process the uploaded audio file. Error details: {error_details}")

        # 3. Process with Gemini
        prompt = """
        あなたは高精度な音声認識アシスタントです。
        提供された音声ファイルの内容を正確に文字起こししてください。
        以下のJSONフォーマットで文字起こし結果のみを出力してください。
        
        {
            "content": "音声の完全な文字起こしテキスト"
        }
        """

        print("Waiting for Gemini response...")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt, audio_file],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=TranscribeResponse,
            )
        )

        # 4. Cleanup
        try:
            os.unlink(temp_audio_path)
            client.files.delete(name=audio_file.name)
        except Exception as cleanup_err:
            print(f"Warning: Cleanup failed: {cleanup_err}")

        result_json = response.text
        structured_data = json.loads(result_json)

        return {
            "status": "success",
            "data": structured_data
        }

    except Exception as e:
        print("====== ERROR OCCurred IN TRANSCRIBE_AUDIO ======")
        traceback.print_exc()
        print("=============================================")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/entries")
async def get_entries(
    user_id: str,
    limit: int = Query(50, description="最大取得件数"),
    tag: Optional[str] = Query(None, description="タグによるフィルタリング")
):
    if db is None:
        raise HTTPException(status_code=500, detail="Firestore is not initialized")
    
    try:
        collection_ref = db.collection("entries")
        query = collection_ref.where(filter=firestore.FieldFilter("user_id", "==", user_id))
        
        if tag:
            query = query.where(filter=firestore.FieldFilter("topic", "array_contains", tag))
            
        # 複合インデックスエラーを避けるため、Python側でソートして返す
        docs = query.stream()
        entries = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if "embedding" in data:
                del data["embedding"]
            entries.append(data)
            
        # created_atで降順ソート
        entries.sort(key=lambda x: x.get("created_at", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        
        # limit適用
        if limit:
            entries = entries[:limit]
            
        return {"status": "success", "data": entries}
    except Exception as e:
        print("====== ERROR IN GET_ENTRIES ======")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/entries/{entry_id}")
async def delete_entry(entry_id: str, user_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Firestore is not initialized")
        
    try:
        doc_ref = db.collection("entries").document(entry_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Entry not found")
            
        data = doc.to_dict()
        if data.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")
            
        doc_ref.delete()
        return {"status": "success", "message": "Entry deleted"}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/export")
async def export_entries(user_id: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Firestore is not initialized")
        
    try:
        docs = db.collection("entries").where(filter=firestore.FieldFilter("user_id", "==", user_id)).stream()
        entries = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            if "embedding" in data:
                del data["embedding"]
            if "created_at" in data:
                data["created_at"] = data["created_at"].isoformat()
            entries.append(data)
            
        return JSONResponse(
            content={"status": "success", "data": entries}, 
            headers={"Content-Disposition": f"attachment; filename=braindump_export_{user_id}.json"}
        )
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/dump")
async def process_dump(request: DumpRequest):
    try:
        # 1. 思考データの構造化 (Gemini Flash)
        prompt = f"""
        あなたはユーザーの思考を整理する優秀なアシスタントです。
        以下のテキスト内容を分析し、JSONフォーマットで分析結果を出力してください。

        【ユーザーの入力テキスト】
        {request.content}

        【出力JSONスキーマ】
        {{
            "content": "{request.content}",
            "summary": "内容の短い要約（1〜2文）",
            "topic": ["関連するタグやトピック（例: 仕事, 悩み, アイデア）の配列"],
            "sentiment": {{
                "score": -1.0 から 1.0 までの数値（ネガティブが-1.0、ポジティブが1.0）,
                "label": "Positive", "Neutral", または "Negative"
            }},
            "is_actionable": true または false (具体的なタスクや行動が含まれているか)
        }}
        """

        print("Waiting for Gemini structure response...")
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EntryData,
            )
        )

        result_json = response.text
        structured_data = json.loads(result_json)

        # contentが失われないよう明示的にセット
        structured_data["content"] = request.content

        # 2. Embedding生成
        text_to_embed = f"Summary: {structured_data.get('summary', '')}\n\nContent: {structured_data.get('content', '')}"
        print("Generating embedding...")
        embedding_response = client.models.embed_content(
            model=EMBEDDING_MODEL_NAME,
            contents=text_to_embed,
            config=types.EmbedContentConfig(
                output_dimensionality=768
            )
        )
        embedding_vector = embedding_response.embeddings[0].values

        # 3. Firestoreへ保存
        if db is not None:
            entry_doc = {
                "user_id": request.user_id,
                "content": structured_data.get("content", ""),
                "summary": structured_data.get("summary", ""),
                "topic": structured_data.get("topic", []),
                "sentiment": structured_data.get("sentiment", {}),
                "is_actionable": structured_data.get("is_actionable", False),
                "created_at": datetime.now(timezone.utc),
                "embedding": embedding_vector 
            }
            _, doc_ref = db.collection("entries").add(entry_doc)
            structured_data["id"] = doc_ref.id
        else:
            print("Firestore is not initialized. Skipping save.")

        return {
            "status": "success",
            "data": structured_data
        }

    except Exception as e:
        print("====== ERROR OCCurred IN PROCESS_DUMP ======")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights")
async def get_insights(
    user_id: str,
    days: int = Query(30, description="集計対象の日数")
):
    if db is None:
        raise HTTPException(status_code=500, detail="Firestore is not initialized")
        
    try:
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        collection_ref = db.collection("entries")
        query = collection_ref.where(filter=firestore.FieldFilter("user_id", "==", user_id))
        docs = query.stream()
        
        entries = []
        for doc in docs:
            data = doc.to_dict()
            # Python側で日付フィルタ
            created_at = data.get("created_at")
            if created_at and created_at >= cutoff_date:
                entries.append(data)
                
        # 感情推移（日別平均）
        daily_sentiment = {}
        topic_counts = {}
        actionable_count = 0
        
        for entry in entries:
            dt = entry.get("created_at")
            if dt:
                date_str = dt.strftime("%Y-%m-%d")
                score = entry.get("sentiment", {}).get("score", 0)
                if date_str not in daily_sentiment:
                    daily_sentiment[date_str] = {"sum": 0, "count": 0}
                daily_sentiment[date_str]["sum"] += score
                daily_sentiment[date_str]["count"] += 1
                
            for t in entry.get("topic", []):
                topic_counts[t] = topic_counts.get(t, 0) + 1
                
            if entry.get("is_actionable"):
                actionable_count += 1
                
        # 成形
        sentiment_trend = []
        for d in sorted(daily_sentiment.keys()):
            sentiment_trend.append({
                "date": d,
                "score": round(daily_sentiment[d]["sum"] / daily_sentiment[d]["count"], 2)
            })
            
        top_topics = [{"topic": k, "count": v} for k, v in sorted(topic_counts.items(), key=lambda item: item[1], reverse=True)[:5]]
        
        return {
            "status": "success",
            "data": {
                "sentiment_trend": sentiment_trend,
                "top_topics": top_topics,
                "total_entries": len(entries),
                "actionable_ratio": round(actionable_count / len(entries) * 100, 1) if entries else 0
            }
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/generate-answer")
async def generate_answer(request: ChatRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Firestore is not initialized")

    try:
        # 1. ユーザーの質問をベクトル化
        print(f"Generating embedding for query: {request.query}")
        query_embedding_response = client.models.embed_content(
            model=EMBEDDING_MODEL_NAME,
            contents=request.query,
            config=types.EmbedContentConfig(
                output_dimensionality=768
            )
        )
        query_vector = query_embedding_response.embeddings[0].values

        # 2. Firestore Vector Search で類似する過去の思考を検索
        print("Searching relevant entries in Firestore...")
        # Note: Vector Search を Firestore で実行するには、
        # 事前に GCP コンソール等でベクトルのインデックスを作成しておく必要があります。
        # ここでは Firestore の Python SDK (v2) のベクトル検索機能を使用します。
        from google.cloud.firestore_v1.vector import Vector
        from google.cloud.firestore_v1.base_vector_query import DistanceMeasure

        collection_ref = db.collection("entries")
        
        # 該当ユーザーのドキュメントを絞り込む (要複合インデックス)
        user_filter = firestore.FieldFilter("user_id", "==", request.user_id)
        
        # ベクトル検索クエリの作成（上位5件の類似思考を取得）
        vector_query = collection_ref.where(filter=user_filter).find_nearest(
            vector_field="embedding",
            query_vector=Vector(query_vector),
            distance_measure=DistanceMeasure.COSINE,
            limit=5
        )
        
        docs = vector_query.stream()
        
        contexts = []
        source_ids = []
        for doc in docs:
            data = doc.to_dict()
            # 類似度の高い順にコンテキストを作成
            context_text = f"[ID: {doc.id}]\nDate: {data.get('created_at')}\nSummary: {data.get('summary')}\nContent: {data.get('content')}"
            contexts.append(context_text)
            source_ids.append(doc.id)

        print(f"Found {len(contexts)} relevant entries.")

        # 3. Gemini Pro を使って回答を生成 (RAG)
        if not contexts:
            return {
                "answer": "ごめんなさい、あなたの過去の記録に該当する思考が見つかりませんでした。",
                "sources": []
            }

        context_block = "\n\n---\n\n".join(contexts)
        prompt = f"""
        あなたはユーザーの「第2の脳」として機能する、優しく知的なAIアシスタントです。
        以下の【ユーザーの過去の思考記録】のみを根拠として、ユーザーの質問に答えてください。
        
        もし記録の中に質問に答えるのに十分な情報がない場合は、嘘（ハルシネーション）をつかず、「過去の記録からは分かりませんでした」と正直に答えてください。
        
        【ユーザーの過去の思考記録】
        {context_block}
        
        【ユーザーの質問】
        {request.query}
        """

        print("Generating answer with Gemini Pro...")
        response = client.models.generate_content(
            model=CHAT_MODEL_NAME,
            contents=prompt,
        )

        return {
            "answer": response.text,
            "sources": source_ids
        }

    except Exception as e:
        print("====== ERROR OCCurred IN GENERATE_ANSWER ======")
        traceback.print_exc()
        print("=============================================")
        raise HTTPException(status_code=500, detail=str(e))
