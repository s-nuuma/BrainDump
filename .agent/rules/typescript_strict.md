# TypeScript 厳格型定義ルール (typescript_strict.md)

このルールは、`*.ts` および `*.tsx` ファイルの作成または編集時にのみ発動します（Globモード）。

---

## 1. 発動条件 (Glob)
- **対象ファイル**: `**/*.ts`, `**/*.tsx`
- **目的**: プロジェクト全体の型安全性を極限まで高め、コンパイルエラーや実行時エラーを事前に防止する。

---

## 2. 厳守ルール

### ① `any` 型の原則使用禁止
- コード内での明示的な `any` 型（`eslint-disable-next-line @typescript-eslint/no-explicit-any` を含む）の使用を厳禁とします。
- 外部APIや動的なデータを扱う場合は `unknown` 型を使用し、必ず**型ガード（Type Guard）**または**型アサーション関数**を用いて安全な型にキャストしたうえで処理を行ってください。

```typescript
// ❌ 悪い例 (Bad)
function processUser(data: any) {
  console.log(data.name);
}

// ⭕ 良い例 (Good)
interface User {
  name: string;
}
function isUser(data: unknown): data is User {
  return typeof data === 'object' && data !== null && 'name' in data;
}
function processUser(data: unknown) {
  if (isUser(data)) {
    console.log(data.name);
  } else {
    throw new Error('Invalid user data structure');
  }
}
```

### ② すべての関数への型定義
- 関数の引数および戻り値（返り値）の型定義を省略しないでください。
- 暗黙の `any` 型（implicit any）が発生しないようにしてください。

### ③ インターフェースと型エイリアスの明確な使い分け
- データ構造やオブジェクトの形状を定義する際は、拡張が容易な `interface` を優先して使用してください。
- ユニオン型（Union Type）や交差型（Intersection Type）、ユーティリティ型などを定義する際は `type` エイリアスを使用してください。

### ④ Firebase データモデルの型安全性の確保
- Firestoreとのデータのやり取りを行う際は、必ず Firestore `withConverter` を使用して、取得データおよび書き込みデータが適切な TypeScript インターフェースに適合するように制御してください。
