#!/usr/bin/env python3
"""ダッシュボードの投稿設定(xops_config)を取得する（えみり用）。

GET {DASHBOARD_URL}/api/config?account=emiri  (ヘッダ x-sync-secret)
取得失敗時は None を返し、呼び出し側は組み込みデフォルトにフォールバックする。
"""
from __future__ import annotations

import json
import os
import urllib.request
import urllib.error

ACCOUNT = "emiri"
_TIMEOUT = 8


def fetch_post_config() -> dict | None:
    base = os.getenv("DASHBOARD_URL", "").rstrip("/")
    secret = os.getenv("SYNC_SECRET", "")
    if not base or not secret:
        return None
    url = f"{base}/api/config?account={ACCOUNT}"
    req = urllib.request.Request(url, headers={"x-sync-secret": secret})
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as res:
            payload = json.loads(res.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError) as e:
        print(f"[config] 取得失敗（デフォルトで継続）: {e}")
        return None
    cfg = payload.get("config")
    return cfg if isinstance(cfg, dict) else None


def theme_map(cfg: dict | None) -> dict | None:
    """設定の有効テーマを {key: {"label","ratio","seeds"}} 形式で返す。無効なら None。"""
    if not cfg:
        return None
    out: dict[str, dict] = {}
    for t in cfg.get("themes", []):
        if not isinstance(t, dict) or not t.get("enabled", True):
            continue
        key = str(t.get("key", "")).strip()
        label = str(t.get("label", "")).strip()
        weight = float(t.get("weight", 0))
        seeds = [str(s).strip() for s in t.get("seeds", []) if str(s).strip()]
        if not key or not label or weight <= 0 or not seeds:
            continue
        out[key] = {"label": label, "ratio": weight, "seeds": seeds}
    return out or None
