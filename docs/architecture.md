# BrainDump システムアーキテクチャ

## 全体構成図

```mermaid
graph TD
    subgraph Client [Frontend: Next.js]
        UI[User Interface]
        Rec[Voice Recording / Input]
        FSDK[Firebase SDK]
    end

    subgraph Server [Backend AI Engine: FastAPI]
        API[FastAPI Endpoints]
        WH[Whisper Service]
        GM[Gemini Service]
        EM[Embedding Service]
    end

    subgraph Cloud [Managed Services]
        Auth[Firebase Auth]
        FS[Firestore]
        VS[Vector Search Extension]
        ST[Firebase Storage]
    end

    subgraph AI_APIs [External AI APIs]
        OpenAI[OpenAI Whisper API]
        Gemini[Google Gemini 1.5 Flash/Pro]
    end

    %% Dump Phase Flow
    Rec -->|Voice Data| API
    API -->|Audio| OpenAI
    OpenAI -->|Text| API
    API -->|Text| GM
    GM -->|Metadata| Gemini
    Gemini -->|JSON| GM
    GM -->|Structured Data| API
    API -->|Vectorize| EM
    EM -->|Embedding| Gemini
    API -->|Save Entry| FS
    API -->|Save Audio| ST

    %% Reflect Phase Flow
    UI -->|Query| FSDK
    FSDK -->|Search| VS
    VS -->|Relevant Docs| FS
    FS -->|Context| UI
    UI -->|Context + Query| API
    API -->|Deep Analysis| Gemini
    Gemini -->|Answer| API
    API -->|Response| UI

    %% Auth
    UI -->|Sign In| Auth
```

## コンポーネントの説明

1.  **Next.js (Client)**: ユーザーインターフェースを提供。Firebase SDK を使用して Auth や Firestore と直接通信し、軽量なデータ操作を行う。重いAI処理が必要な時だけ FastAPI を呼び出す。
2.  **FastAPI (AI Engine)**: AI処理のオーケストレーター。Whisper による文字起こしや、Gemini による構造化、Embedding の生成など、Python ライブラリや外部 AI API との連携を専門に行う。
3.  **Firebase**: アプリケーションの状態管理、認証、ファイル保存を担う。
4.  **Firestore Vector Search**: RAG のためのベクトル検索エンジン。エントリ保存時に自動または手動で同期されるベクトルデータに基づき、類似検索を実行する。
