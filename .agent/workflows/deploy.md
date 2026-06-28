# 自律開発 ＆ 自己修復リリースワークフロー (deploy.md)

このワークフローは、機能開発（新機能追加、仕様変更）またはバグ修正の依頼を受けた際、AIエージェント（Antigravity）が自律的かつ自動で「実装 ➔ テスト ➔ PR作成 ➔ 自己修復ループ ➔ デプロイ監視 ➔ 完了検証」を回すためのレシピです。

---

## 🛠 ワークフロー手順

エージェントは以下のステップを順に、自律的にコマンドを呼び出して進めてください。

### Step 1: 実装 ＆ 単体テストの追加
1. 要件（`spec.md`）に沿ってコードを実装する。
2. 今回追加した新規ロジックやコンポーネントに対する単体テスト（Vitest: `*.test.ts`, `*.test.tsx`）を必ず記述する。
3. `npm run test` を実行し、すべてのユニットテストが Green（パス）になるまで修復を繰り返す。

### Step 2: 既存機能のデグレード検証 (E2Eテスト)
1. 新規実装によって既存の機能が壊れていないかを確認するため、Playwright のテストを実行する。
   - コマンド: `npm run test:e2e` または `npx playwright test`
2. E2Eテストで失敗が発生した場合は、実装コードを修正し、Step 1 と Step 2 がすべて成功するまでループする。

### Step 3: ローカルビルドの事前検証
1. VercelやFirebaseなどのリモート環境でビルドエラーが起きないよう、ローカル環境（WSL）でプロダクションビルドを実行する。
   - コマンド: `npm run build`
2. TypeScriptのコンパイルエラーやTurbopackのバンドルエラーが発生した場合は、エラーログを分析して修復する。

### Step 4: ブランチ作成 ➔ コミット ➔ プッシュ
1. 開発用の新ブランチを作成する。
   - コマンド: `git checkout -b feature/your-feature-name` (バグ修正の場合は `bugfix/...`)
2. 変更ファイルをすべてステージングし、明確なコミットメッセージでコミットを作成する。
   - コマンド: `git add . && git commit -m "feat: add user-facing feature with tests"`
   - ※ ローカルのリントやフックでブロックされないよう、必要に応じて `--no-verify` を使用する。
3. リモートリポジトリにブランチをプッシュする。
   - コマンド: `git push origin HEAD`

### Step 5: Pull Request (PR) の自動作成
1. GitHub CLI を使用して、`main`（または `master`）に対する Pull Request を自動作成する。
   - コマンド例:
     ```bash
     gh pr create --title "feat: [機能名] の実装とテスト検証" --body "## 概要\n- [実装内容の説明]\n\n## 検証結果\n- 単体テストおよびE2Eテスト通過済\n- ローカルビルド確認済" --head HEAD
     ```
2. 出力された PR の番号または URL を記録する。

### Step 6: 🔄 自己修復レビュー・ループ (Review-Fix-Push Loop)
外部レビュアー（Jules または GitHub Actions 上の Gemini レビュアーボット）による「コンテキストなし」の客観的コードレビューと、エージェント自身による「コンテキストあり」の修復を繰り返します。

1. **レビュー完了の監視**:
   PR作成によってトリガーされた GitHub Actions ワークフロー（`jules-review.yml`）の実行状況を監視し、完了するまで待機する。
   - コマンド: `gh run list --workflow jules-review.yml --limit 1` で状況を確認し、必要なら `gh run watch <RunID>` を実行。
2. **レビュー指摘コメントの自動取得**:
   Actions完了後、PRに投稿されたレビュアーAIのレビューコメント（ディスカッション）を取得する。
   - コマンド: `gh pr view <PR番号> --comments` または GitHub API を使用。
3. **自律修復の実行**:
   - **指摘があった場合**:
     1. 指摘された内容（型定義の不整合、パフォーマンスの無駄、Tailwindの競合など）を読み取り、プロジェクトの全体コンテキストと照らし合わせてコードを修正する。
     2. `npm run test` および `npm run build` を再実行して問題がないことを確認。
     3. 修正をコミットし、リモートにプッシュする。
        - コマンド: `git add . && git commit -m "fix: resolve jules code review feedback" && git push origin HEAD`
     4. **再度、手順 1 (レビュー完了の監視) に戻り、再レビュー結果を待つ。**
   - **指摘がゼロになった場合（または解決済の場合）**:
     * ループを抜けて **Step 7** に進む。

### Step 7: マージ ➔ 本番デプロイ検証
1. PRをマージ（またはユーザーによるマージ承認を検知）する。
2. `main` ブランチに統合されたことによる Vercel / Firebase Hosting の本番デプロイステータスを監視する。
   - コマンド: `gh api repos/:owner/:repo/commits/:commit_sha/statuses`
   - ステータスが `success` になるまでポーリング待機。
3. デプロイ完了後、ターゲットURL（VercelのデプロイプレビューURLまたは本番URL）に対して、curl等で簡易疎通確認を行い、正しくHTTP 200が返ってくることを確認してタスク完了とする。
