# youtube-auto-post

PythonでYouTube Data APIを使い、ローカル動画をYouTubeに自動投稿するプロジェクト。

## 初期ゴール

- ローカルのmp4動画を読み込む
- metadata JSONを読み込む
- YouTubeにprivate投稿する
- 投稿結果をCSVに保存する

## ディレクトリ

- scripts/: Pythonスクリプト
- config/: 認証情報
- data/metadata/: 投稿用メタデータJSON
- videos/: 動画ファイル
- logs/: 実行ログ