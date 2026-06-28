# Next.js App Router ＆ コンポーネント設計ルール (nextjs_app_router_component_policy.md)

このルールは、`**/app/**/*.tsx` (ページ・ルーティング) または `**/components/**/*.tsx` (UIコンポーネント) に分類されるファイルの作成・編集時に発動します。

---

## 1. Server Component (RSC) と Client Component の境界設計

Next.js App Router のパフォーマンスを最大限引き出し、クライアント側のJSバンドルサイズを最小限に抑えるためのルールです。

- **Server Component (デフォルト) の推奨**:
  - コンポーネントは原則として Server Component として実装し、不要な `"use client"` の付与は避けてください。
  - データ取得（`fetch` や DB直接クエリ）や、バックエンド特有のロジック処理は Server Component 側で完結させます。
- **Client Component の適用境界**:
  - `"use client"` は、インタラクション（`useState`, `useReducer`, `useEffect` などの状態やライフサイクル）を使用する場合、またはブラウザ専用のAPI（`window`, `localStorage` 等）を扱う末端のUI要素にのみ付与してください。
  - 親コンポーネント全体を Client Component にするのではなく、状態を持つフォームやボタンなどのインタラクティブなパーツのみを Client Component に切り出す設計を徹底してください。

---

## 2. セキュリティと `server-only` の使用

- **サーバーコードの流出防止**:
  - データベースクエリや認証鍵の操作、外部APIの秘密鍵を扱うモジュール（`lib/db.ts` や `services/private/` 等）には、必ずファイルの先頭に `import 'server-only'` を記述してください。
  - これにより、サーバー専用のコードが誤ってクライアントサイド（Client Component）にインポートされた場合、ビルドエラーとして事前に検知できます。

---

## 3. Tailwind CSS と UI一貫性 (shadcn/ui 結合ルール)

- **`cn` ユーティリティの徹底使用**:
  - コンポーネントの `className` でスタイルをマージまたは条件分岐する際は、直接の文字列結合ではなく、必ずプロジェクト共通の `cn(...)` ユーティリティ（`clsx` + `tailwind-merge`）を通してください。
  - これにより、Tailwind の同一属性のクラス（例: `p-4` と `p-2`）が衝突した際に、後から渡されたクラスが優先される型安全なマージが保証され、予期せぬ表示バグを防ぐことができます。

```typescript
import { cn } from '@/lib/utils'; // プロジェクト共通のユーティリティ

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
}

export function Button({ className, variant = 'primary', ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        'px-4 py-2 rounded-md font-semibold transition-colors',
        variant === 'primary' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-800',
        className // 外部から注入されるスタイルが正しくマージされる
      )}
      {...props}
    />
  );
}
```
