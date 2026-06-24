import csv
import json
import os
import sys
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "config/client_secret.json"
TOKEN_FILE = "config/token.json"
POSTED_CSV = "data/posted_videos.csv"


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


def save_posted_video(video_id, metadata):
    os.makedirs(os.path.dirname(POSTED_CSV), exist_ok=True)

    file_exists = os.path.exists(POSTED_CSV)

    with open(POSTED_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["video_id", "title", "video_path", "uploaded_at"])

        writer.writerow([
            video_id,
            metadata["title"],
            metadata["video_path"],
            datetime.now().isoformat()
        ])


def main():
    if len(sys.argv) < 2:
        print("使い方: python scripts/upload_youtube.py data/metadata/sample.json")
        sys.exit(1)

    metadata_path = sys.argv[1]
    metadata = load_metadata(metadata_path)

    print("YouTube認証中...")
    youtube = get_youtube_client()

    print("動画アップロード中...")
    video_id = upload_video(youtube, metadata)

    save_posted_video(video_id, metadata)

    print("アップロード成功")
    print(f"video_id: {video_id}")
    print(f"url: https://www.youtube.com/watch?v={video_id}")


if __name__ == "__main__":
    main()