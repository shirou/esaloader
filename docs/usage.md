# esaloader 使用方法

## インストール

Python 3.12以上が必要です。画像処理のためPillowが必要です。

```bash
git clone https://github.com/shirou/esaloader.git
cd esaloader

# 依存パッケージのインストール
pip install -e .

# uvを使用する場合（推奨）
uv sync

# または直接実行する場合
pip install Pillow>=10.0.0
```

## 初期設定

### アクセストークンの取得
1. esa.ioにログイン
2. チームの設定 → アプリケーション → Personal access tokens
3. 「Generate new token」をクリック
4. 必要な権限を選択（最低限「Read」権限が必要）
5. トークンをコピー

### 環境変数の設定
```bash
# Linux/Mac
export ESA_ACCESS_TOKEN="your_access_token_here"

# Windows (PowerShell)
$env:ESA_ACCESS_TOKEN="your_access_token_here"

# Windows (Command Prompt)
set ESA_ACCESS_TOKEN=your_access_token_here
```

## 基本的な使い方

### すべての記事をダウンロード
```bash
python esaloader.py -t your_team_name
```

### 特定のタグがついた記事をダウンロード
```bash
python esaloader.py -t your_team_name -q "tag:important"

# 日本語タグの例
python esaloader.py -t your_team_name -q "tag:重要"
```

### カテゴリを指定してダウンロード
```bash
python esaloader.py -t your_team_name -q "category:docs/api"

# 日本語カテゴリの例
python esaloader.py -t your_team_name -q "category:開発/仕様書"
```

### 出力ディレクトリを指定
```bash
python esaloader.py -t your_team_name -o ./my_esa_backup
```

## 高度な使い方

### 複合検索
```bash
# タグとカテゴリの組み合わせ
python esaloader.py -t your_team_name -q "tag:release category:changelog"

# キーワードとタグの組み合わせ
python esaloader.py -t your_team_name -q "API tag:documentation"

# NOT検索
python esaloader.py -t your_team_name -q "tag:public -tag:draft"
```

### 日本語検索
```bash
# 日本語キーワード検索
python esaloader.py -t your_team_name -q "開発ガイドライン"

# 日本語タグとカテゴリの組み合わせ
python esaloader.py -t your_team_name -q "tag:リリース category:更新履歴"

# 日本語と英語の混在検索
python esaloader.py -t your_team_name -q "APIドキュメント tag:公開"
```

### ドライラン（ダウンロードせずに対象を確認）
```bash
python esaloader.py -t your_team_name -q "tag:important" --dry-run
```

### 取得数の制限
```bash
# 最新の10件のみ取得
python esaloader.py -t your_team_name --limit 10
```

### 詳細ログの表示
```bash
python esaloader.py -t your_team_name -v
```

### 画像ダウンロードの制御
```bash
# 画像をimagesサブディレクトリに保存
python esaloader.py -t your_team_name --images-dir

# uvを使用する場合
ESA_ACCESS_TOKEN=your_token uv run python esaloader.py -t your_team_name -q "in:hoo" --images-dir
```

## オプション一覧

| オプション | 短縮形 | 説明 | デフォルト |
|---------|-------|------|----------|
| --team | -t | チーム名（必須） | - |
| --query | -q | 検索クエリ | - |
| --output | -o | 出力ディレクトリ | ./esa_posts |
| --dry-run | - | ダウンロードせずに対象を表示 | False |
| --limit | - | 取得する記事数の上限 | 無制限 |
| --images-dir | - | 画像を"images"サブディレクトリに保存 | False |
| --verbose | -v | 詳細なログ出力 | False |
| --help | -h | ヘルプを表示 | - |

## 出力形式

### ディレクトリ構造
```
output_directory/
├── category1/
│   ├── subcategory/
│   │   ├── 123_article_title.md
│   │   └── 124_another_article.md
│   └── 125_root_category_article.md
├── 開発/
│   ├── 仕様書/
│   │   ├── 127_API仕様.md
│   │   └── 128_データベース設計.md
│   └── 129_開発ガイドライン.md
└── 126_uncategorized_article.md
```

### ファイル形式
各記事は以下の形式で保存されます：

```markdown
---
number: 123
title: 記事タイトル
tags: ["tag1", "tag2", "日本語タグ"]
category: 開発/仕様書
created_at: 2024-01-01T00:00:00+09:00
updated_at: 2024-01-02T00:00:00+09:00
created_by: user_name
updated_by: user_name
wip: false
---

記事本文...
```

**注意**: すべてのファイルはUTF-8エンコーディングで保存されます。

### 画像処理

記事内の画像は自動的に処理されます：

- `<img src="https://img.esa.io/..." width="400">` 形式の画像を自動検出
- 画像をローカルにダウンロード  
- `width` 属性が指定されている場合、その幅にリサイズ（アスペクト比維持）
- Markdown内のリンクを相対パスに変更

```markdown
# 変換前
<img width="494" alt="image.png" src="https://img.esa.io/uploads/.../image.png">

# 変換後（デフォルト）
<img src="image.png" width="494">

# 変換後（--images-dir使用時）
<img src="images/image.png" width="494">
```

## トラブルシューティング

### 認証エラーが発生する場合
- アクセストークンが正しく設定されているか確認
- トークンの権限が適切か確認
- 環境変数名が`ESA_ACCESS_TOKEN`になっているか確認

### レート制限エラーが発生する場合
- 自動的にリトライされますが、大量の記事がある場合は時間がかかることがあります
- `--limit`オプションで取得数を制限することを検討してください

### ファイル保存エラーが発生する場合
- 出力ディレクトリへの書き込み権限があるか確認
- ディスク容量が十分にあるか確認
- ファイル名に使用できない文字が含まれている場合は自動的にサニタイズされます
- 日本語ファイル名は保持されますが、OSによっては制限がある場合があります

### 画像ダウンロードエラーが発生する場合
- 画像のダウンロードに失敗した場合、エラーメッセージが表示されますが処理は続行されます
- ネットワークエラーやURLが無効な場合に発生する可能性があります  
- リサイズに失敗した場合、元の画像がそのまま保存されます

### 依存パッケージのインストールエラー
```bash
# Pillowのインストールに失敗した場合
pip install --upgrade pip
pip install Pillow>=10.0.0

# システムによっては追加のライブラリが必要な場合があります
# Ubuntu/Debian
sudo apt-get install python3-dev libjpeg-dev libpng-dev

# CentOS/RHEL  
sudo yum install python3-devel libjpeg-turbo-devel libpng-devel
```

## 使用例

### 定期バックアップ（cron）
```bash
# 毎日午前3時にバックアップ
0 3 * * * ESA_ACCESS_TOKEN=your_token python /path/to/esaloader.py -t your_team -o /backup/esa/$(date +\%Y\%m\%d)
```

### 特定の期間の記事を取得
```bash
# 2024年以降に作成された記事
python esaloader.py -t your_team -q "created:>2024-01-01"

# 最近1週間に更新された記事
python esaloader.py -t your_team -q "updated:>$(date -d '7 days ago' +%Y-%m-%d)"
```

### 日本語環境での使用
```bash
# Windowsでの文字化けを避けるための設定
set PYTHONIOENCODING=utf-8
python esaloader.py -t your_team -q "日本語検索"

# ファイル名に日本語が含まれる場合の確認
python esaloader.py -t your_team -q "category:日本語カテゴリ" --dry-run
```