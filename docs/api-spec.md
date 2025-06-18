# esa.io API仕様まとめ

## 認証

### アクセストークン
- ヘッダー: `Authorization: Bearer {access_token}`
- クエリパラメータ: `?access_token={access_token}` （非推奨）

## エンドポイント

### 記事一覧取得
```
GET /v1/teams/{team_name}/posts
```

#### パラメータ
- `q` (string): 検索クエリ
  - キーワード検索: `keyword`（日本語対応）
  - タグ検索: `tag:tagname`（日本語タグ対応）
  - カテゴリ検索: `category:path/to/category`（日本語パス対応）
  - 複合検索: `tag:release category:docs/api`
- `page` (integer): ページ番号（デフォルト: 1）
- `per_page` (integer): 1ページあたりの記事数（デフォルト: 20、最大: 100）
- `sort` (string): ソート順
  - `created`: 作成日順（デフォルト）
  - `updated`: 更新日順
  - `stars`: スター数順
- `order` (string): 並び順
  - `desc`: 降順（デフォルト）
  - `asc`: 昇順

#### レスポンス
```json
{
  "posts": [
    {
      "number": 1,
      "name": "記事タイトル",
      "full_name": "path/to/category/記事タイトル",
      "wip": false,
      "body_md": "記事本文（省略版）",
      "body_html": "HTMLバージョン（省略版）",
      "created_at": "2024-01-01T00:00:00+09:00",
      "updated_at": "2024-01-02T00:00:00+09:00",
      "tags": ["tag1", "tag2"],
      "category": "path/to/category",
      "revision_number": 1,
      "created_by": {
        "name": "user_name",
        "screen_name": "screen_name"
      },
      "updated_by": {
        "name": "user_name",
        "screen_name": "screen_name"
      }
    }
  ],
  "prev_page": null,
  "next_page": 2,
  "total_count": 150,
  "page": 1,
  "per_page": 20,
  "max_per_page": 100
}
```

### 記事詳細取得
```
GET /v1/teams/{team_name}/posts/{post_number}
```

#### レスポンス
一覧取得と同じ形式だが、`body_md`と`body_html`が完全版

## レート制限

### 制限値
- 15分間に300リクエストまで
- ユーザーごと、アプリケーションごとに適用

### レスポンスヘッダー
- `X-RateLimit-Limit`: 制限値
- `X-RateLimit-Remaining`: 残りリクエスト数
- `X-RateLimit-Reset`: リセット時刻（UNIX時間）

### 制限超過時
- HTTPステータス: 429 Too Many Requests
- Retry-Afterヘッダーで再試行可能時刻を通知

## エラーレスポンス

### 形式
```json
{
  "error": "error_type",
  "message": "エラーメッセージ"
}
```

### 主なエラー
- 401 Unauthorized: 認証エラー
- 403 Forbidden: アクセス権限なし
- 404 Not Found: リソース不存在
- 429 Too Many Requests: レート制限超過
- 500 Internal Server Error: サーバーエラー

## 検索クエリ詳細

### 基本構文
- AND検索: スペース区切り `keyword1 keyword2`
- OR検索: `OR`演算子 `keyword1 OR keyword2`
- NOT検索: `-`プレフィックス `-keyword`
- フレーズ検索: ダブルクォート `"exact phrase"`

### 日本語検索の例
- 日本語キーワード: `開発ドキュメント`
- 日本語タグ: `tag:リリース情報`
- 日本語カテゴリ: `category:仕様書/API`
- 複合: `API仕様 tag:公開 -tag:下書き`

### 特殊検索
- `wip:true` / `wip:false`: WIP状態
- `starred:true`: スター付き記事
- `watched:true`: ウォッチ中の記事
- `created:>2024-01-01`: 作成日フィルタ
- `updated:<2024-01-01`: 更新日フィルタ

## URLエンコーディング

日本語を含む検索クエリやカテゴリ名はURLエンコードが必要です。

### 例
- `開発` → `%E9%96%8B%E7%99%BA`
- `tag:重要` → `tag:%E9%87%8D%E8%A6%81`
- `category:仕様書/API` → `category:%E4%BB%95%E6%A7%98%E6%9B%B8%2FAPI`

クライアント実装時は`urllib.parse.quote()`を使用して適切にエンコードする必要があります。