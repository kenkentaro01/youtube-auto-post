import json
import subprocess
import sys
from pathlib import Path


DEFAULT_PROMPT_FILE = "data/prompts/domoai_sample.json"
DEFAULT_INPUT_DIR = "videos/input"
DEFAULT_OUTPUT_DIR = "videos/merged"


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return [data]

    return data


def create_ffmpeg_list(input_videos, list_file):
    with open(list_file, "w", encoding="utf-8") as f:
        for video in input_videos:
            f.write(f"file '{Path(video).resolve()}'\n")


def merge_videos(input_videos, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    list_file = output_path.parent / f"{output_path.stem}_merge_list.txt"
    create_ffmpeg_list(input_videos, list_file)

    command = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_path)
    ]

    subprocess.run(command, check=True)
    list_file.unlink()

    print(f"merged: {output_path}")


def build_input_videos(item):
    if "input_videos" in item:
        return item["input_videos"]

    video_id = item["id"]

    merge = item.get("merge", {})
    count = merge.get("count", 1)

    return [
        f"{DEFAULT_INPUT_DIR}/{video_id}_{str(i).zfill(2)}.mp4"
        for i in range(1, count + 1)
    ]


def build_output_path(item):
    merge = item.get("merge", {})

    if merge.get("output_path"):
        return merge["output_path"]

    return f"{DEFAULT_OUTPUT_DIR}/{item['id']}.mp4"


def should_merge(item):
    merge = item.get("merge", False)

    if isinstance(merge, bool):
        return merge

    return merge.get("enabled", False)


def main():
    prompt_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROMPT_FILE
    items = load_config(prompt_file)

    for item in items:
        if not should_merge(item):
            print(f"skip merge: {item['id']}")
            continue

        input_videos = build_input_videos(item)
        output_path = build_output_path(item)

        for video in input_videos:
            if not Path(video).exists():
                raise FileNotFoundError(f"動画がありません: {video}")

        merge_videos(input_videos, output_path)


if __name__ == "__main__":
    main()