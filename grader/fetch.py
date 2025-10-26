from __future__ import annotations
import os
import re
import requests

GIST_RE = re.compile(r"https?://gist\.github\.com/[^/]+/([0-9a-f]+)")
RAW_RE = re.compile(r"https?://gist\.githubusercontent\.com/.+/raw/.+/assessment-(2|3)\.py")


def _pick_gist_file(files: dict) -> dict | None:
    """Gist files(dict) から assessment-3.py or assessment-2.py を選択。"""
    # files は {filename: {raw_url:..., ...}} の想定
    if "assessment-3.py" in files:
        return files["assessment-3.py"]
    if "assessment-2.py" in files:
        return files["assessment-2.py"]
    # 他にも submission.py などに対応するならここで条件を追加
    return None

class FetchError(Exception):
    pass

def detect_and_fetch(url: str, dest_path: str, target_filename: str = 'assessment-3.py') -> None:
    """URLがGistページ or raw URL のどちらでも target_filename を取得して保存。"""
    url = url.strip()
    if RAW_RE.match(url):
        _fetch_raw(url, dest_path)
        return

    m = GIST_RE.match(url)
    if not m:
        raise FetchError("サポートしていないURL形式です：" + url)

    gist_id = m.group(1)
    api = f"https://api.github.com/gists/{gist_id}"
    r = requests.get(api, timeout=15)
    if r.status_code != 200:
        raise FetchError(f"Gist APIエラー: {r.status_code}")
    data = r.json()

    files = data.get("files", {})
    target = files.get(target_filename)
    if not target:
        raise FetchError(f"Gistに '{target_filename}' が見つかりません。含まれるファイル: " + ", ".join(files.keys()))

    raw_url = target.get("raw_url")
    if not raw_url:
        raise FetchError("raw_url を取得できませんでした")

    _fetch_raw(raw_url, dest_path)

def _fetch_raw(raw_url: str, dest_path: str) -> None:
    rr = requests.get(raw_url, timeout=15)
    if rr.status_code != 200:
        raise FetchError(f"raw取得エラー: {rr.status_code}")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        f.write(rr.content)
