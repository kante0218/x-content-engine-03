#!/usr/bin/env python3
"""x.com/oxp_emiri のツイートを Playwright で取得する。

2モード:
  --open    : ブラウザを開いて待機(ユーザーがログインする時間を確保)
  (default) : 永続プロファイルの cookie を使って自動スクレイプ
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT / ".browser_profile"
OUT_DIR = ROOT / "analysis"
OUT_DIR.mkdir(exist_ok=True)
PROFILE_DIR.mkdir(exist_ok=True)

URL = "https://x.com/oxp_emiri"


def open_for_login() -> int:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="ja-JP",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        print("[open] ブラウザでログインしてください。完了したらこのウィンドウを閉じずに 1800秒 待機します。")
        # Wait long enough for user to log in and notify back
        time.sleep(1800)
        ctx.close()
    return 0


def scrape() -> int:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="ja-JP",
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded")
        try:
            page.wait_for_selector('article[data-testid="tweet"]', timeout=30000)
        except Exception:
            print("[error] tweet selector が見つからない。未ログインの可能性。--open で先にログインしてください。", file=sys.stderr)
            ctx.close()
            return 1

        seen: dict[str, dict] = {}
        last_count = 0
        stable = 0
        for i in range(50):
            arts = page.locator('article[data-testid="tweet"]').all()
            for a in arts:
                try:
                    txt_el = a.locator('div[data-testid="tweetText"]').first
                    text = txt_el.inner_text(timeout=2000) if txt_el.count() else ""
                except Exception:
                    text = ""
                try:
                    time_el = a.locator("time").first
                    if time_el.count():
                        ts = time_el.get_attribute("datetime", timeout=2000) or ""
                        link_el = time_el.locator("xpath=..").first
                        href = link_el.get_attribute("href", timeout=2000) or "" if link_el.count() else ""
                    else:
                        ts, href = "", ""
                except Exception:
                    ts, href = "", ""
                tweet_id = href.split("/status/")[-1] if href else f"_{ts}_{hash(text) & 0xffffffff}"
                if tweet_id in seen:
                    continue
                seen[tweet_id] = {"id": tweet_id, "ts": ts, "url": f"https://x.com{href}" if href else "", "text": text}

            print(f"  scroll {i+1}: {len(seen)} tweets")
            if len(seen) == last_count:
                stable += 1
                if stable >= 4:
                    break
            else:
                stable = 0
                last_count = len(seen)
            page.mouse.wheel(0, 4000)
            time.sleep(2)

        tweets = sorted(seen.values(), key=lambda x: x.get("ts", ""))
        (OUT_DIR / "tweets_raw.json").write_text(
            json.dumps(tweets, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        with (OUT_DIR / "tweets_text.txt").open("w", encoding="utf-8") as f:
            for i, t in enumerate(tweets, 1):
                f.write(f"--- [{i}] {t['ts']} {t['url']} ---\n{t['text']}\n\n")
        print(f"\n[saved] {OUT_DIR / 'tweets_raw.json'} ({len(tweets)} tweets)")
        ctx.close()
    return 0


if __name__ == "__main__":
    if "--open" in sys.argv:
        sys.exit(open_for_login())
    sys.exit(scrape())
