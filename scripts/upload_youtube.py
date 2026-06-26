import csv
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "config/client_secret.json"
TOKEN_FILE = "config/token.json"

POSTED_CSV = "data/posted_videos.csv"

DEFAULT_PENDING_DIR = "data/metadata/pending"
COMPLETED_DIR = "data/metadata/completed"
FAILED_DIR = "data/metadata/failed"

UPLOADED_VIDEO_DIR = "videos/uploaded"
FAILED_VIDEO_DIR = "videos/failed"


def get_youtube_client():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE,
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def load_metadata(metadata_path):
    with open(metadata_path, "r", encoding="utf-8") as f:
        return json.load(f)


def upload_video(youtube, metadata):
    video_path = metadata["video_path"]

    body = {
        "snippet": {
            "title": metadata["title"],
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", []),
            "categoryId": metadata.get("categoryId", "22"),
        },
        "status": {
            "privacyStatus": metadata.get("privacyStatus", "private")
        },
    }

    media = MediaFileUpload(
        video_path,
        chunksize=-1,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = request.execute()
    return response["id"]


def save_posted_video(video_id, metadata, metadata_path):
    os.makedirs(os.path.dirname(POSTED_CSV), exist_ok=True)

    file_exists = os.path.exists(POSTED_CSV)

    with open(POSTED_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "video_id",
                "title",
                "video_path",
                "metadata_path",
                "uploaded_at"
            ])

        writer.writerow([
            video_id,
            metadata["title"],
            metadata["video_path"],
            str(metadata_path),
            datetime.now().isoformat()
        ])


def move_file(src_path, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)

    src_path = Path(src_path)
    dest_path = Path(dest_dir) / src_path.name

    if dest_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        dest_path = Path(dest_dir) / f"{src_path.stem}_{timestamp}{src_path.suffix}"

    shutil.move(str(src_path), str(dest_path))

    return dest_path


def update_metadata_video_path(metadata_path, metadata, new_video_path):
    metadata["video_path"] = str(new_video_path)

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(
            metadata,
            f,
            ensure_ascii=False,
            indent=2
        )


def upload_one_metadata(youtube, metadata_path):
    print(f"metadata: {metadata_path}")

    metadata = load_metadata(metadata_path)
    video_path = metadata["video_path"]

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"動画ファイルが存在しません: {video_path}")

    print(f"動画アップロード中: {video_path}")
    video_id = upload_video(youtube, metadata)

    save_posted_video(video_id, metadata, metadata_path)

    uploaded_video_path = move_file(video_path, UPLOADED_VIDEO_DIR)

    update_metadata_video_path(
        metadata_path,
        metadata,
        uploaded_video_path
    )

    completed_metadata_path = move_file(
        metadata_path,
        COMPLETED_DIR
    )

    print("アップロード成功")
    print(f"title: {metadata['title']}")
    print(f"video_id: {video_id}")
    print(f"url: https://www.youtube.com/watch?v={video_id}")
    print(f"metadata moved: {completed_metadata_path}")
    print(f"video moved: {uploaded_video_path}")


def handle_failed_file(metadata_path):
    try:
        metadata = load_metadata(metadata_path)
        video_path = metadata.get("video_path")

        if video_path and os.path.exists(video_path):
            move_file(video_path, FAILED_VIDEO_DIR)

    except Exception:
        pass

    move_file(metadata_path, FAILED_DIR)


def get_metadata_files(path):
    path = Path(path)

    if path.is_file():
        return [path]

    if path.is_dir():
        return sorted(path.glob("*.json"))

    raise FileNotFoundError(f"指定されたパスが存在しません: {path}")


def main():
    target_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_PENDING_DIR
    )

    metadata_files = get_metadata_files(target_path)

    if not metadata_files:
        print("投稿対象のmetadataがありません。")
        return

    print("YouTube認証中...")
    youtube = get_youtube_client()

    for metadata_path in metadata_files:
        try:
            upload_one_metadata(youtube, metadata_path)
        except Exception as e:
            print(f"アップロード失敗: {metadata_path}")
            print(e)
            handle_failed_file(metadata_path)


if __name__ == "__main__":
    main()