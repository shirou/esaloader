# esaloader

esa.ioの記事を指定した条件でまとめてダウンロードするCLIツールです。

## 概要

esaloaderは、esa.ioのAPIを使用して記事を一括ダウンロードするPython製のコマンドラインツールです。タグやカテゴリ、キーワードで記事を絞り込んでダウンロードでき、ローカルにMarkdown形式で保存します。

## 特徴

- 柔軟な検索条件（タグ、カテゴリ、キーワード）での絞り込み
- 日本語検索・日本語ファイル名の完全サポート
- esa.ioのカテゴリ構造をディレクトリとして再現
- 画像の自動ダウンロードとリサイズ機能
- API レート制限の自動ハンドリング
- 記事のメタデータをフロントマター形式で保存
- 環境変数によるセキュアなトークン管理

## 必要要件

- Python 3.12以上
- esa.io の Personal Access Token（読み取り権限）

## インストール

```bash
git clone https://github.com/shirou/esaloader.git
cd esaloader

# 依存パッケージのインストール
pip install -e .

# uvを使用する場合（推奨）
uv sync

# または直接実行する場合
pip install Pillow>=10.0.0
chmod +x esaloader.py  # Linux/Macの場合
```

## 使い方

### 1. アクセストークンの取得と設定

まず、esa.ioでPersonal Access Tokenを取得します：

1. esa.ioにログイン
2. チームの設定 → アプリケーション → Personal access tokens
3. 「Generate new token」をクリック
4. 必要な権限（最低限「Read」権限）を選択
5. トークンをコピー

環境変数に設定：

```bash
# Linux/Mac
export ESA_ACCESS_TOKEN="your_access_token_here"

# Windows (PowerShell)
$env:ESA_ACCESS_TOKEN="your_access_token_here"

# Windows (Command Prompt)
set ESA_ACCESS_TOKEN=your_access_token_here
```

### 2. 基本的な使用例

```bash
# すべての記事をダウンロード
python esaloader.py -t your_team_name

# 特定のタグがついた記事をダウンロード
python esaloader.py -t your_team_name -q "tag:important"

# 日本語タグで検索
python esaloader.py -t your_team_name -q "tag:重要"

# カテゴリを指定してダウンロード
python esaloader.py -t your_team_name -q "category:開発/仕様書"

# 出力先ディレクトリを指定
python esaloader.py -t your_team_name -o ./my_backup

# ドライラン（ダウンロードせずに対象記事を確認）
python esaloader.py -t your_team_name -q "tag:公開" --dry-run
```

#### uvを使用する場合

```bash
# uvでの実行例
ESA_ACCESS_TOKEN=your_token uv run python esaloader.py -t your_team_name -q "in:hoo"

# 画像もダウンロード
ESA_ACCESS_TOKEN=your_token uv run python esaloader.py -t your_team_name --images-dir -v
```

### 3. 高度な使用例

```bash
# 複合検索（タグとカテゴリの組み合わせ）
python esaloader.py -t your_team_name -q "tag:release category:changelog"

# NOT検索
python esaloader.py -t your_team_name -q "tag:public -tag:draft"

# 日本語キーワード検索
python esaloader.py -t your_team_name -q "開発ガイドライン"

# 取得数を制限
python esaloader.py -t your_team_name --limit 10

# 詳細ログを表示
python esaloader.py -t your_team_name -v

# 画像をimagesサブディレクトリに保存
python esaloader.py -t your_team_name --images-dir
```

## コマンドラインオプション

| オプション | 短縮形 | 説明 | デフォルト |
|---------|-------|------|----------|
| `--team` | `-t` | esa.ioのチーム名（必須） | - |
| `--query` | `-q` | 検索クエリ（タグ、カテゴリ、キーワード） | - |
| `--output` | `-o` | 出力先ディレクトリ | ./esa_posts |
| `--dry-run` | - | ダウンロードせずに対象記事を表示 | - |
| `--limit` | - | 取得する記事数の上限 | 無制限 |
| `--images-dir` | - | 画像を"images"サブディレクトリに保存 | - |
| `--verbose` | `-v` | 詳細なログを出力 | - |
| `--help` | `-h` | ヘルプを表示 | - |

## 出力形式

### ディレクトリ構造

esa.ioのカテゴリ構造がそのままディレクトリとして再現されます：

```
出力ディレクトリ/
├── カテゴリ1/
│   ├── サブカテゴリ/
│   │   ├── 123_記事タイトル.md
│   │   └── image1.png          # デフォルト: 記事と同じディレクトリ
│   └── 124_別の記事.md
├── 開発/
│   ├── 仕様書/
│   │   ├── images/             # --images-dir使用時
│   │   │   ├── diagram.png
│   │   │   └── screenshot.jpg
│   │   └── 127_API仕様.md
│   └── 129_開発ガイドライン.md
└── 125_カテゴリなし記事.md
```

### ファイル形式

各記事は以下の形式で保存されます：

```markdown
---
number: 123
title: 記事タイトル
tags: ["tag1", "日本語タグ"]
category: 開発/仕様書
created_at: 2024-01-01T00:00:00+09:00
updated_at: 2024-01-02T00:00:00+09:00
created_by: username
updated_by: username
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

## 実装の詳細

### 技術仕様

- **言語**: Python 3.12
- **依存関係**: Pillow（画像処理）、標準ライブラリ（urllib, json, argparse等）
- **文字エンコーディング**: UTF-8（日本語完全対応）
- **API通信**: HTTPS only
- **認証**: Bearer トークン（環境変数から取得）

### 主な機能

1. **検索機能**
   - キーワード、タグ、カテゴリによる絞り込み
   - AND/OR/NOT検索のサポート
   - 日本語検索の完全サポート

2. **画像処理機能**
   - 記事内画像の自動検出とダウンロード
   - width属性に基づく自動リサイズ
   - 相対パスでのリンク書き換え
   - 画像保存場所の選択（記事と同じディレクトリ or imagesサブディレクトリ）

3. **エラーハンドリング**
   - API レート制限時の自動リトライ（指数バックオフ）
   - ネットワークエラー時のリトライ
   - 認証エラーの明確な通知
   - 画像ダウンロード失敗時の適切な処理

4. **ファイル保存**
   - カテゴリ構造の保持
   - ファイル名の自動サニタイズ（日本語は保持）
   - メタデータの保存

## トラブルシューティング

### 認証エラーが発生する場合

- 環境変数 `ESA_ACCESS_TOKEN` が正しく設定されているか確認
- トークンに必要な権限（Read）があるか確認

### 日本語が文字化けする場合（Windows）

```bash
set PYTHONIOENCODING=utf-8
python esaloader.py -t your_team
```

### レート制限エラー

- 自動的にリトライされますが、大量の記事がある場合は時間がかかることがあります
- `--limit` オプションで取得数を制限することを検討してください

### 画像ダウンロードエラー

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

## ライセンス

MIT License

## 作者

shirou

## 貢献

Issue や Pull Request は歓迎します。

## 関連ドキュメント

より詳細な情報については、`docs/` ディレクトリ内のドキュメントを参照してください：

- [設計書](docs/design.md) - アーキテクチャと実装の詳細
- [使用方法](docs/usage.md) - より詳しい使用例とTips
- [API仕様](docs/api-spec.md) - esa.io APIの仕様まとめ