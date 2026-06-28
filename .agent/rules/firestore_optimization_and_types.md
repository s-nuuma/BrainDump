# Firestore コスト最適化 ＆ 型安全定義ルール (firestore_optimization_and_types.md)

このルールは、Firebase や Firestore の操作、またはデータアクセス層（リポジトリ・サービス）に関連する TypeScript ファイルの作成・編集時に発動します。

---

## 1. クエリ最適化とコスト管理

Firestore の課金体系（ドキュメントの読み取り・書き込み回数）を強く意識し、効率的なデータ操作を設計してください。

- **N+1クエリの禁止**:
  - ループ（`forEach`, `map`, `for...of` 等）の中で `getDoc` や `getDocs` などの非同期クエリを発行する実装を厳禁とします。
  - 複数のドキュメントを取得する際は、`documentId` を使用して `where(documentId(), 'in', [...])` などのバッチ取得や、データのローカルキャッシュキャッシュ構造を必ず適用してください。
- **データ取得範囲の最小化**:
  - 不要なドキュメントの全件取得を避け、必ず上限値（`limit(...)`）を設定してください。
  - 更新監視（`onSnapshot`）を使用する際は、コンポーネントのアンマウント時、または不要になったタイミングで**確実にリスナーを解除（unsubscribe）**してください。メモリリークとバックグラウンドでの不要な読み取り課金を防止します。

---

## 2. 厳格な型安全性の確保 (`withConverter`)

データの読み書き時に `any` を経由した「型が壊れた状態」でのやり取りを防ぐため、必ず FirestoreDataConverter を導入してください。

- **型安全なコンバーターの実装**:
  - Firestore からデータを取得する際、および保存する際は、Firestore 用のデータモデル（`FirestoreDataConverter`）を仲介させます。

```typescript
import { FirestoreDataConverter, DocumentData, QueryDocumentSnapshot } from 'firebase/app/firestore';

export interface UserProfile {
  id: string;
  name: string;
  email: string;
  createdAt: Date;
}

export const userProfileConverter: FirestoreDataConverter<UserProfile> = {
  toFirestore(user: UserProfile): DocumentData {
    return {
      name: user.name,
      email: user.email,
      createdAt: user.createdAt
    };
  },
  fromFirestore(snapshot: QueryDocumentSnapshot): UserProfile {
    const data = snapshot.data();
    return {
      id: snapshot.id,
      name: data.name || '',
      email: data.email || '',
      createdAt: data.createdAt?.toDate() || new Date()
    };
  }
};
```

- **適用方法**:
  - コレクションやドキュメントを参照する際は、必ず `.withConverter(userProfileConverter)` を接続して呼び出してください。これにより、エディタ上およびビルド時に型安全が完全に保証されます。

---

## 3. セキュリティルール (`firestore.rules`) との整合性

- `firestore.rules` を変更・追加する際は、最小権限の原則（Least Privilege）を厳守してください。
- `request.auth != null` による認証チェックを基本とし、ドキュメントの作成者本人のみが書き込み可能（`request.auth.uid == resource.data.userId`）とする条件式を確実に実装してください。
