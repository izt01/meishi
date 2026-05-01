# 名刺アプリ セットアップガイド

## 構成
```
meishi-app/
├── backend/        → FastAPI（Railway にデプロイ）
│   ├── main.py
│   ├── requirements.txt
│   ├── Procfile
│   └── railway.toml
└── frontend/       → 静的HTML（GitHub Pages でホスト）
    └── index.html
```

---

## 1. GitHubリポジトリを作る

```bash
git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/YOUR_USER/meishi-app.git
git push -u origin main
```

---

## 2. バックエンドを Railway にデプロイ

1. https://railway.app にログイン
2. 「New Project」→「Deploy from GitHub repo」→ このリポジトリを選択
3. **Root Directory** を `backend` に設定
4. 「Add Service」→「Database」→「PostgreSQL」を追加

### 環境変数を設定（Railway の Variables タブ）

| 変数名 | 値 |
|---|---|
| `DATABASE_URL` | Railway が自動設定（PostgreSQL の接続URL） |
| `ADMIN_USER` | 管理者ユーザー名（例: `admin`） |
| `ADMIN_PASS` | 管理者パスワード（例: `your_strong_password`） |
| `FRONTEND_URL` | GitHub Pages のURL（例: `https://yourname.github.io`） |

5. デプロイ完了後、Railway の「Settings」→ 「Domain」でURLを確認
   - 例: `https://meishi-app-production.up.railway.app`

---

## 3. フロントエンドの API URL を更新

`frontend/index.html` の以下の行を編集：

```js
// 変更前
const API_BASE = 'https://your-app.railway.app';

// 変更後（RailwayのURLに変更）
const API_BASE = 'https://meishi-app-production.up.railway.app';
```

変更後、GitHubにプッシュ：
```bash
git add frontend/index.html
git commit -m "update API_BASE URL"
git push
```

---

## 4. GitHub Pages を有効化

1. GitHubリポジトリ → 「Settings」→「Pages」
2. Source: `Deploy from a branch`
3. Branch: `main` / Folder: `/frontend`
4. 「Save」をクリック
5. 公開URL: `https://YOUR_USER.github.io/meishi-app/`

---

## 5. 使い方

### 管理者（メンバー登録）
1. サイトを開く
2. 「管理者ページ」リンクをクリック
3. 管理者ユーザー名・パスワードを入力
4. 「＋ 新規登録」でメンバーを追加

### メンバー（プロフィール閲覧）
1. サイトを開く
2. 自分の名前を入力してログイン
3. プロフィールカードが表示される

---

## API エンドポイント一覧

| メソッド | パス | 説明 |
|---|---|---|
| GET | `/api/login?name=名前` | 名前でログイン・プロフィール取得 |
| GET | `/api/admin/profiles` | 全プロフィール一覧（要認証） |
| POST | `/api/admin/profiles` | 新規登録（要認証） |
| PUT | `/api/admin/profiles/{id}` | 編集（要認証） |
| DELETE | `/api/admin/profiles/{id}` | 削除（要認証） |
| GET | `/docs` | Swagger UI（API仕様書） |
