# YouTube Auto Post

AIを利用してショート動画を自動生成し、YouTubeへ自動投稿するシステムです。

## 機能

- DomoAI APIによる動画生成
- 動画の自動ダウンロード
- YouTube APIによる動画投稿
- 複数動画の一括投稿
- 投稿履歴の保存
- pending / completed / failed によるファイル管理

今後実装予定

- 動画結合(ffmpeg)
- Claudeによるmetadata自動生成
- LINE通知
- Instagram Reels投稿
- TikTok投稿
- 自動スケジューリング

---

# ディレクトリ構成

```
youtube-auto-post
├── config
│   ├── client_secret.json
│   └── token.json
│
├── data
│   ├── metadata
│   │   ├── pending
│   │   ├── completed
│   │   └── failed
│   │
│   ├── prompts
│   │   └── domoai_sample.json
│   │
│   └── posted_videos.csv
│
├── logs
│
├── scripts
│   ├── generate_domoai_video.py
│   ├── merge_videos.py
│   └── upload_youtube.py
│
├── videos
│   ├── input
│   ├── merged
│   ├── uploaded
│   └── failed
│
├── requirements.txt
└── .env
```

---

# 環境構築

## Python

```bash
python3 -m venv venv_youtube_auto_post

source venv_youtube_auto_post/bin/activate

pip install -r requirements.txt
```

## ffmpeg

Mac

```bash
brew install ffmpeg
```

動画結合で利用します。

## DomoAI

`.env`

```env
DOMOAI_API_KEY=xxxxxxxxxxxxxxxx
```

## YouTube API

Google Cloudで

- OAuth Client作成
- client_secret.json取得

```
config/client_secret.json
```

へ配置します。

---

# 動画生成

```bash
python scripts/generate_domoai_video.py
```

設定ファイル

```
data/prompts/domoai_sample.json
```

生成された動画

```
videos/input
```

---

# 動画結合

```bash
python scripts/merge_videos.py
```

結合後

```
videos/merged
```

---

# YouTube投稿

```bash
python scripts/upload_youtube.py
```

投稿対象

```
data/metadata/pending
```

投稿後

```
metadata/completed
videos/uploaded
```

失敗時

```
metadata/failed
videos/failed
```

投稿履歴

```
data/posted_videos.csv
```

---

# 現在の処理フロー

```
Prompt(JSON)

↓

DomoAI

↓

videos/input

↓

merge_videos.py（必要な場合）

↓

videos/merged

↓

metadata

↓

upload_youtube.py

↓

YouTube
```

---

# 今後の予定

- [x] DomoAI API連携
- [x] YouTube API連携
- [x] 複数動画投稿
- [ ] 動画結合
- [ ] Claude API連携
- [ ] metadata自動生成
- [ ] LINE通知
- [ ] main.py作成
- [ ] cronによる自動投稿
- [ ] Instagram Reels投稿
- [ ] TikTok投稿