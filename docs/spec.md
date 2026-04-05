# BrainDump External Memory - アプリケーション仕様書 (Spec)

## 1. プロジェクトコンセプト

「思考の外部出力による認知負荷の軽減」と「蓄積データのオンデマンド活用」。
就寝前などの反芻思考を物理的に外部へ書き出し、脳のメモリを解放する。記録したデータはAIが整理し、必要な時にだけ対話を通じて引き出せる「第2の脳」を目指す。

## 2. 設計思想

- **入力時 (Dump Phase)**: 「無反応（記録のみ）」。ユーザーへのフィードバックを最小限にし、思考を止めることなく出力させる。
- **活用時 (Reflect Phase)**: 「高精度（RAG）」。過去の膨大な記録から関連情報を抽出し、Gemini 1.5 Pro が深い洞察を提供する。

## 3. 機能要件

### 3.1. 思考ダンプ (入力フェーズ)

- **音声入力**: ブラウザから直接録音し、FastAPI（Whisper API）経由で高精度にテキスト化。
- **テキスト入力**: シンプルなテキストエリアからの入力。
- **自動メタデータ抽出 (Background)**:
  - Gemini 1.5 Flash を使用し、以下の項目を自動生成。
    - **Topic**: 内容のカテゴリ（仕事、家庭、アイデア、悩み等）。
    - **Sentiment**: 感情のトーン（ポジティブ、ネガティブ、中立）と強度。
    - **Actionable**: 具体的なタスクが含まれているか（Yes/No）。
    - **Summary**: 短い要約。
- **ベクトル化 (Embedding)**: RAG用のベクトルデータを生成し保存。

### 3.2. オンデマンド・リフレクション (活用フェーズ)

- **AIチャット**: ユーザーの問いかけに対し、過去の記録のみをソースとして回答。
- **RAG プロセス**:
  - 問いかけに関連する過去のエントリをベクトル検索で抽出。
  - 抽出されたコンテキストを Gemini 1.5 Pro に渡し、根拠に基づいた回答を生成。
  - 該当する記録がない場合は「記録がありません」と回答し、ハルシネーション（嘘）を防止。

### 3.3. UI/UX 要件 (Simple & Low Stimulus)

- **Home**: 巨大な録音ボタンと、最小限のテキスト入力。
- **History**: カレンダービューまたはリストビュー。日付ごとに振り返りが可能。
- **Chat**: ユーザーが意識的に開くサブ画面。

## 4. 技術スタック

- **Frontend**: Next.js 16+ (App Router), Tailwind CSS, shadcn/ui
- **Backend (AI Engine)**: FastAPI (Python 3.10+)
- **Database/Auth**: Firebase (Firestore, Auth, Storage)
- **Vector Search**: Firestore Vector Search (Firebase Extensions)
- **AI Models**:
  - Speech-to-Text: OpenAI Whisper API
  - Structuring: Gemini 1.5 Flash
  - Analysis/RAG: Gemini 1.5 Pro

## 5. データ構造 (Firestore Schema)

### Collection: `entries`

```typescript
{
  id: string,
  user_id: string,
  content: string,        // 原本（テキストまたは文字起こし結果）
  summary: string,        // Geminiが生成した要約
  topic: string[],        // カテゴリタグ
  sentiment: {
    score: number,        // -1.0 to 1.0
    label: string
  },
  is_actionable: boolean,
  created_at: Timestamp,
  embedding: number[]     // ベクトルデータ（1536次元または768次元）
}
```

## 6. 実装フェーズ

- [ ] **Phase 1: 基盤構築**: プロジェクト構成、Firebase連携、FastAPI 疎通。
- [ ] **Phase 2: 思考ダンプの実装**: 音声録音 -> Whisper -> Gemini 構造化 -> 保存フロー。
- [ ] **Phase 3: RAG の実装**: ベクトル検索設定 -> Gemini Pro 対話機能。
- [ ] **Phase 4: UI ブラッシュアップ**: ダークモード、カレンダー表示、PWA化。

## 7. 現在のステータス

- 【計画中】プロジェクトディレクトリ構成と基本ドキュメントの準備
