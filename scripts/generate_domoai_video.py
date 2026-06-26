import json
import logging
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# ===========================
# Settings
# ===========================

load_dotenv()

API_KEY = os.getenv("DOMOAI_API_KEY")

CREATE_VIDEO_URL = "https://api.domoai.com/v1/video/text2video"
TASK_URL = "https://api.domoai.com/v1/tasks/{task_id}"

DEFAULT_PROMPT_FILE = "data/prompts/domoai_sample.json"
DEFAULT_OUTPUT_DIR = "videos/input"

MAX_WAIT_SECONDS = 600
POLL_INTERVAL_SECONDS = 60

LOG_FILE = "logs/generate_domoai.log"

# ===========================
# Logger
# ===========================

Path("logs").mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
)

file_handler = logging.FileHandler(
    LOG_FILE,
    encoding="utf-8"
)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


# ===========================
# Functions
# ===========================

def load_prompt_items(prompt_file):
    with open(prompt_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return [data]

    return data


def create_video_task(item):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}",
    }

    payload = {
        "prompt": item["prompt"],
        "model": item.get("model", "t2v-2.4-faster"),
        "duration": item.get("duration", 5),
        "aspect_ratio": item.get("aspect_ratio", "9:16"),
    }

    response = requests.post(
        CREATE_VIDEO_URL,
        headers=headers,
        json=payload,
    )
    response.raise_for_status()

    result = response.json()

    if result.get("code") != 0:
        raise Exception(result)

    return result["data"]["task_id"]


def get_task(task_id):
    response = requests.get(
        TASK_URL.format(task_id=task_id),
        headers={
            "Authorization": f"Bearer {API_KEY}"
        },
    )

    response.raise_for_status()

    return response.json()


def wait_for_success(task_id):
    waited = 0

    while waited <= MAX_WAIT_SECONDS:

        task = get_task(task_id)

        status = task["data"]["status"]

        logger.info(f"Task Status : {status}")

        if status in ["SUCCESS", "COMPLETED"]:
            return task["data"]

        if status in ["FAILED", "ERROR"]:
            raise Exception(task)

        time.sleep(POLL_INTERVAL_SECONDS)
        waited += POLL_INTERVAL_SECONDS

    raise TimeoutError("Video generation timed out.")


def download_video(video_url, output_path):

    Path(output_path).parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    response = requests.get(
        video_url,
        stream=True,
    )

    response.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in response.iter_content(
            chunk_size=1024 * 1024
        ):
            if chunk:
                f.write(chunk)


def generate_and_download(item):

    video_id = item["id"]

    output_path = (
        f"{DEFAULT_OUTPUT_DIR}/{video_id}.mp4"
    )

    logger.info(f"Start : {video_id}")

    task_id = create_video_task(item)

    logger.info(f"Task ID : {task_id}")

    task = wait_for_success(task_id)

    video_url = task["output_videos"][0]["url"]

    logger.info("Download Start")

    download_video(
        video_url,
        output_path,
    )

    logger.info(
        f"Downloaded : {output_path}"
    )


# ===========================
# Main
# ===========================

def main():

    if not API_KEY:
        raise Exception(
            "DOMOAI_API_KEY is not set."
        )

    prompt_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else DEFAULT_PROMPT_FILE
    )

    logger.info(
        f"Prompt File : {prompt_file}"
    )

    items = load_prompt_items(prompt_file)

    for item in items:
        generate_and_download(item)

    logger.info("Finished.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
        raise