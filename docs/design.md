# esa.io記事ダウンロードCLIツール設計書

## 概要
esa.ioのAPIを使用して、指定した条件に合致する記事を一括ダウンロードするCLIツール。

## 設計方針
- Python 3.12で実装（画像処理にPillowを使用）
- シンプルで使いやすいインターフェース
- エラーハンドリングとリトライ機構の実装
- カテゴリ構造を保持したファイル保存
- 日本語を含むUTF-8文字の完全サポート
- 記事内画像の自動ダウンロードとリサイズ機能

## アーキテクチャ

### モジュール構成
```
esaloader.py
├── EsaClient          # APIクライアントクラス
│   ├── __init__()     # 認証トークンの初期化
│   ├── search_posts() # 記事検索（日本語クエリ対応）
│   ├── get_post()     # 個別記事取得
│   └── _request()     # HTTPリクエスト共通処理（URLエンコード含む）
├── ImageDownloader    # 画像処理クラス
│   ├── extract_images() # HTMLからimg要素抽出
│   ├── download_image() # 画像ダウンロード
│   ├── resize_image()   # 画像リサイズ
│   └── process_images() # 画像一括処理とリンク書き換え
├── PostDownloader     # ダウンロード管理クラス
│   ├── download_all() # 一括ダウンロード
│   ├── save_post()    # 記事保存（UTF-8エンコーディング、画像処理含む）
│   └── sanitize_path() # ファイル名・パスのサニタイズ
└── main()             # CLIエントリーポイント
```

### データフロー
1. コマンドライン引数の解析
2. 環境変数から認証トークン取得
3. 検索条件に基づいて記事リストを取得（ページネーション対応）
4. 各記事の詳細を取得
5. 記事内の画像URLを抽出・ダウンロード・リサイズ
6. Markdownテキストの画像リンクを相対パスに書き換え
7. ローカルファイルシステムに保存

## 主要機能

### 1. 認証
- 環境変数`ESA_ACCESS_TOKEN`からトークンを読み込み
- Authorizationヘッダーに`Bearer`トークンとして設定

### 2. 記事検索
- 検索クエリ（`-q`オプション）で条件指定
- 日本語キーワード、タグ、カテゴリ名に対応
- チーム名（`-t`オプション）必須
- ページネーション自動処理

### 3. 画像処理
- HTMLの`<img>`タグから画像URLを自動抽出
- 画像ファイルをローカルにダウンロード
- `width`属性に基づく自動リサイズ（アスペクト比維持）
- 画像保存場所の選択（記事と同じディレクトリ or imagesサブディレクトリ）
- Markdownテキスト内の画像リンクを相対パスに書き換え

### 4. ファイル保存
- カテゴリをディレクトリ構造として再現（日本語カテゴリ対応）
- ファイル名: `{post_number}_{name}.md`
- 日本語を含むファイル名・ディレクトリ名の適切な処理
- メタデータ（タグ、作成日等）をフロントマターとして保存
- すべてのファイルをUTF-8で保存

### 5. エラーハンドリング
- ネットワークエラー: 3回までリトライ
- レート制限（429）: 指数バックオフでリトライ
- 認証エラー: 明確なエラーメッセージ
- 画像ダウンロード失敗: 処理続行（エラーログ出力）

## コマンドラインインターフェース

```bash
# 基本的な使い方
python esaloader.py -t TEAM_NAME -q "tag:important" -o ./output

# オプション一覧
-t, --team       チーム名（必須）
-q, --query      検索クエリ
-o, --output     出力ディレクトリ（デフォルト: ./esa_posts）
--dry-run        ダウンロードせずに対象記事を表示
--limit          取得する記事数の上限
--images-dir     画像を"images"サブディレクトリに保存
-v, --verbose    詳細なログ出力
```

## エラー処理

### HTTPステータスコード別の処理
- 401: 認証エラー → プログラム終了
- 404: リソース不存在 → スキップして続行
- 429: レート制限 → バックオフリトライ
- 5xx: サーバーエラー → リトライ

### ファイルシステムエラー
- 書き込み権限なし → エラーメッセージ表示
- ディスク容量不足 → エラーメッセージ表示
- 無効なファイル名 → サニタイズ処理
- ファイルシステムで使用できない文字の置換

## 文字エンコーディング処理

### URL処理
- 検索クエリのURLエンコード（urllib.parse.quote）
- 日本語を含むパスの適切なエンコード
- スペースや特殊文字の処理

### ファイルシステム処理
- ファイル名に使用できない文字の置換規則
  - `/` → `_`
  - `\` → `_`
  - `:` → `-`
  - `*` → `_`
  - `?` → `_`
  - `"` → `'`
  - `<` → `(`
  - `>` → `)`
  - `|` → `_`
- 長すぎるファイル名の切り詰め（255バイト制限）
- 日本語文字を保持したまま処理

### コマンドライン引数
- sys.argvの適切な処理
- UTF-8環境での動作を前提
- Windows環境でのコンソール出力対応

### ファイル入出力
- すべてのファイル読み書きでencoding='utf-8'を明示
- BOMなしUTF-8で保存
- エラーハンドリング時の文字化け防止

## セキュリティ考慮事項
- トークンをコマンドライン引数で受け取らない（環境変数のみ）
- トークンをログに出力しない
- HTTPSのみ使用