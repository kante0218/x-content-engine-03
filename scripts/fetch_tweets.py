#!/usr/bin/env python3
"""@oxp_emiri の過去ツイートを X API v2 で取得して JSON 保存する。

- X_USER_ID が未設定なら GET /2/users/by/username/:handle で解決して .env を更新提案
- GET /2/users/:id/tweets?max_results=100 で最新100件まで取得
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

BEARER = os.getenv("X_BEARER_TOKEN")
HANDLE = os.getenv("X_HANDLE", "oxp_emiri").lstrip("@")
USER_ID = os.getenv("X_USER_ID")

if not BEARER:
    sys.exit("X_BEARER_TOKEN が .env に未設定")

H = {"Authorization": f"Bearer {BEARER}"}


def resolve_user_id() -> str:
    r = requests.get(
        f"https://api.x.com/2/users/by/username/{HANDLE}",
        headers=H,
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["data"]["id"]


def fetch_tweets(user_id: str) -> list[dict]:
    params = {
        "max_results": 100,
        "tweet.fields": "created_at,public_metrics,lang,referenced_tweets,entities",
        "exclude": "retweets,replies",
    }
    r = requests.get(
        f"https://api.x.com/2/users/{user_id}/tweets",
        headers=H,
        params=params,
        timeout=30,
    )
    if r.status_code != 200:
        sys.exit(f"X API error: {r.status_code} {r.text}")
    return r.json().get("data", [])


def main() -> int:
    uid = USER_ID or resolve_user_id()
    print(f"[user_id] {uid}")
    if not USER_ID:
        print(f"  → .env の X_USER_ID={uid} を埋めてください")
    tweets = fetch_tweets(uid)
    print(f"[tweets] {len(tweets)} 件取得")

    out = ROOT / "analysis" / "tweets_raw.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(tweets, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[saved] {out}")

    txt = ROOT / "analysis" / "tweets_text.txt"
    with txt.open("w", encoding="utf-8") as f:
        for i, t in enumerate(tweets, 1):
            f.write(f"--- [{i}] {t.get('created_at','')} ---\n{t.get('text','')}\n\n")
    print(f"[saved] {txt}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
