# FastAPI API エンドポイント定義

FastAPI 側で実装すべき主要なエンドポイントを定義します。

## 1. 思考ダンプ関連 (Dump Phase)

### `POST /entries/process-audio`

音声データを受け取り、文字起こし、構造化、要約生成、ベクトル化を一括で行う。

- **Request**:
  - `file`: 音声ファイル (multipart/form-data)
  - `user_id`: ユーザーID
- **Processing**:
  1. OpenAI Whisper API による文字起こし
  2. Gemini 1.5 Flash による構造化 (Topic, Sentiment, Actionable, Summary)
  3. Gemini Embedding によるベクトル化
- **Response**:
  - `status`: "success"
  - `data`: 構造化されたエントリ情報 (Firestore 保存用)

### `POST /entries/process-text`

テキストデータを受け取り、構造化、要約生成、ベクトル化を行う。

- **Request**:
  - `content`: 思考原本
  - `user_id`: ユーザーID
- **Response**:
  - `data`: 構造化されたエントリ情報

---

## 2. リフレクション関連 (Reflect Phase)

### `POST /chat/generate-answer`

ベクトル検索結果（コンテキスト）に基づき、Gemini Pro が回答を生成する。

- **Request**:
  - `query`: ユーザーの質問
  - `contexts`: 検索された過去の記録リスト (原本と要約のセット)
- **Response**:
  - `answer`: 生成された回答
  - `sources`: 回答の根拠となったエントリIDのリスト

---

## 3. ユーティリティ

### `POST /embeddings`

任意のテキストからベクトルデータを生成する（再ベクトル化用など）。

- **Request**:
  - `text`: 対象テキスト
- **Response**:
  - `embedding`: 浮動小数点配列

---

## 4. ヘルスチェック

### `GET /health`

サーバーの稼働状況を確認。

- **Response**:
  - `status`: "ok"
