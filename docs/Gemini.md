# 役割定義 (Role Definition)

あなたは自律型開発AIエージェントです。本プロジェクトにおいて、以下のドキュメントを「プロジェクトの憲法」として絶対遵守してください。

1. `Gemini.md`: コーディング規約、AIレビュー基準、ディレクトリ構成ルール
2. `AI_DEVELOPMENT_GUIDE.md`: 開発プロセス（要件定義 -> テスト -> 実装 -> 最適化）
3. `spec.md`: 現在のアプリケーション仕様と実装状況（Status）

指示を受けた際は、まずこれらのファイルを参照し、現在のコンテキスト（文脈）とルールを理解した上で行動してください。

# 基本指示 (General Instructions)

- 言語: 全ての回答、Artifacts、コードコメント、PRのタイトル・説明文まで含め、必ず日本語とする。
- スタイルとトーン: 簡潔かつ丁寧な日本語を用い、冗長な解説は避ける。特定の職業（QAエンジニア等）に例えたり、過度な配慮や忖度を行わないこと。
- 客観性と中立性: フラットに、事実と根拠を独立させて述べること。

# 開発ルール

- **PR運用ポリシーと自動作成**: タスク開始前に `git pull`、完了時に `git status` を徹底すること。ソースコード、テスト、またはドキュメントのいずれかに有意な差分（変更）が加わった場合は、必ず GitHub CLI を用いて自動でPull Requestを作成すること。
- **プッシュ時の注意**: 初めてプッシュするブランチの場合は、`git push -u origin HEAD` (または現在のブランチ名) を使用して、リモートのアップストリームを設定すること。
- **PR作成時のルール**: AIエージェントとしてPull Requestを作成する際は、タイトルと説明文（Description）を日本語で正確に反映すること。ユーザーの学習やコード理解の助けとなるよう、「どのような意図で実装したか（Why）」「どこを改善したか（What）」「レビュアーはどこに注目すべきか（Review Points）」を日本語で詳細に記載すること。
- **【最重要】WSL環境におけるコマンド実行**: カレントディレクトリがWSL上のパス (`\\wsl.localhost\...`) であり、かつWindows側のシェルで実行されている場合、Git (`git`), GitHub CLI (`gh`), npm, python, pip コマンドなどはWSL環境側で実行する必要があります。必ず **`wsl` プレフィックスを付けて実行** （例: `wsl git push`, `wsl gh pr create`, `wsl npm run lint`, `wsl python3 main.py`）してください。
- **【最重要】PR作成時の改行バグ防止**: PRを作成する際は必ず **一時ファイル（例: `pr_body.md`）に説明文を書き出し、`gh pr create --body-file pr_body.md` のようにファイルから読み込ませる** 手法を徹底してください。

# 設計パターン・コーディング規約 (Design Patterns & Coding Standards)

## Frontend: Next.js (App Router) & Firebase

- **Firebase SDKの活用**: クライアントサイドでの認証、Firestoreへの直接データ取得には Firebase SDK を積極的に利用する。
- **Server Actionsの利用**: AI Engine (FastAPI) へのリクエストや、秘密鍵が必要な処理は Server Actions (`app/actions/`) を経由する。
- **UI / UX (shadcn/ui & Tailwind CSS)**: モバイルファーストで、就寝前の利用を想定した「目に優しい・低刺激」なデザイン（ダークモード推奨）を採用する。

## Backend: FastAPI (Python)

- **非同期処理 (async/await)**: FastAPI の利点を活かし、AI API呼出やDB操作は非同期で行う。
- **型ヒント (Type Hints)**: Pydantic モデルを使用した厳格なリクエスト/レスポンスの型定義を徹底する。
- **責務の分離**: FastAPI は「AI処理（Whisper/Gemini）のエージェント」として振る舞い、複雑な状態管理は極力 Firestore に委ねる。

# AIレビュー・自動修正ガイドライン

(Personal Archive の基準を継承)

# プロジェクト概要

「BrainDump External Memory - 思考の外部出力による認知負荷の軽減と蓄積データのオンデマンド活用」
入力時は「無反応（記録のみ）」、活用時は「高精度（RAG）」という非同期的な体験を提供する。

# 技術スタック

- Frontend: Next.js (App Router), Tailwind CSS, shadcn/ui
- Backend: FastAPI (Python 3.10+), OpenAI Whisper API, Gemini 1.5 API
- Database/Auth: Firebase (Firestore, Firebase Auth, Storage)
- Vector Search: Firestore Vector Search (Firebase Extensions)
- Language: TypeScript (Frontend), Python (Backend)

# ディレクトリ構成ルール (Directory Structure & Rules)

- `frontend/`: Next.js プロジェクト
  - `app/`: App Router
  - `components/`: UIコンポーネント
  - `hooks/`, `lib/`: ロジック、ユーティリティ
- `backend/`: FastAPI プロジェクト
  - `app/`: FastAPI アプリケーション
  - `models/`: Pydantic モデル
  - `services/`: AI処理ロジック
- `docs/`: プロジェクトドキュメント (`spec.md`, `Gemini.md` 等)

# 開発プロセス・品質基準

(Personal Archive の基準を継承。テスト駆動開発、視覚的検証を徹底。)
