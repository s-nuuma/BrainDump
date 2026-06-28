# 技術スタック共通ルール (tech_stack_rules.md)

本プロジェクトにおける技術スタックの制約事項を定義します。AIエージェントによる古いライブラリの採用や、非推奨な技術の選択を防止するために、以下の構成を標準とし、厳守してください。

---

## 1. コア技術スタック
本プロジェクトで採用する技術スタックは以下の通りです。これら以外のフレームワークやライブラリを追加する際は、必ず事前に人間の承認を得てください。

- **Frontend**:
  - **Next.js (App Router)**: ルーティング、SSR/SSG、API Routesを含むNext.js最新機能を使用。
  - **Tailwind CSS (v4.0+)**: スタイリングにはTailwind CSSを原則使用。従来のレガシーCSSの多用やインラインスタイルの直書きは避けてください。
  - **shadcn/ui (Radix UI)**: コンポーネントの再利用には shadcn/ui を標準とし、スタイリングの統一を図ります。
- **Backend / Authentication**:
  - **Firebase Web SDK (v12+) & Admin SDK (v13+)**:
    - **Cloud Firestore**: データベースにはFirestoreを使用。
    - **Firebase Authentication**: ユーザー認証。
    - **Cloud Functions for Firebase (Gen 2)**: バックグラウンド処理およびカスタムAPI。非推奨となった Gen 1 (v1) の関数は記述しないでください。
- **Language**:
  - **TypeScript**: 厳格な型定義（`strict: true`）のもと、すべての関数・変数に適切な型を定義します。
- **AI / LLM Integration**:
  - **Gemini API (Google Gen AI SDK / `@google/genai`)**:
    - AI連携を行う際は、Googleの公式最新SDKである `@google/genai` をデフォルトとして使用してください。
    - 古い `@google/generative-ai` や他のサードパーティ製ラッパー（LangChain等）を人間の明示的な指示なしに使用することは禁止します。

---

## 2. 実装および品質基準
- **非推奨機能の排除**:
  - Firebase v9 Web SDK の互換モード（`compat` パッケージなど）の読み込みは禁止します。モダンなモジュール型記述（`getDoc`, `setDoc` など）を徹底してください。
  - Next.js (App Router) における `pages` ディレクトリ用のレガシーAPI（`getStaticProps`, `getServerSideProps` など）の混入を避けてください。
- **TypeScript 厳格化**:
  - any型の使用を原則禁止します。型定義が困難な場合は、ジェネリクスや union type、または `unknown` 型を用いた型ガードを実装してください。
- **パッケージ管理のルール**:
  - パッケージマネージャーには `npm` を統一して使用します。異なるマネージャー（pnpm, yarn）のコマンドを混同させず、常に `package-lock.json` が唯一のロックファイルとして機能するようにしてください。
