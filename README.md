# x-automation-oxp-emiri

@oxp_emiri(えみり|オクパ 執行役員 / オックスフォードパートナーズ株式会社)向け X投稿自動化

- 認証: OAuth 1.0a User Context(投稿) / OAuth 2.0 Bearer(検索・読み取り、要Basic以上)
- 推敲・生成モデル: Claude Opus 4.7
- スケジューラ: launchd `com.user.x-automation-oxp-emiri`(毎日 09:30 / 13:30 / 21:00 JST)

## 仕組み

```
launchd
  └─ scripts/auto_tweet.sh
       ├─ scripts/generate_draft.py   # pending が空ならテーマプールから新規ドラフト生成
       └─ scripts/pipeline.py         # 最古ドラフトを推敲 → 投稿 → posted/ に移動
            ├─ scripts/polish_draft.py  # ペルソナ準拠で推敲
            └─ scripts/post_tweet.py    # X API v2 POST /2/tweets
```

## ディレクトリ

```
x-automation-oxp-emiri/
├── .env                          # 秘密鍵(コミット禁止)
├── .env.example                  # 雛形
├── analysis/
│   ├── persona_source_215q.md    # 本人記入215問の一次資料
│   └── persona_axis.md           # 投稿軸(SYSTEM_PROMPT のソース)
├── drafts/
│   ├── pending/   # 投稿待ち
│   ├── posted/    # 投稿済(_YYYYMMDD_HHMMSS_<原ファイル名> + .result.json)
│   └── failed/    # 失敗
├── logs/
│   ├── auto_tweet.log
│   ├── generate.log
│   ├── pipeline.log
│   └── launchd.out.log / launchd.err.log
└── scripts/
    ├── auto_tweet.sh        # launchd エントリポイント
    ├── generate_draft.py    # ペルソナ準拠の自動ドラフト生成
    ├── polish_draft.py      # 既存ドラフトを推敲
    ├── post_tweet.py        # 投稿のみ
    └── pipeline.py          # pending → 推敲 → 投稿 → posted
```

## 投稿軸(6カテゴリ)

| ID | テーマ | 比率 |
| --- | --- | --- |
| A | エンジニアあるある | 25% |
| B | SES業界の透明化 | 20% |
| C | AIとエンジニア | 15% |
| D | 採用担当の本音 | 15% |
| E | 経営者・代表の素顔 | 15% |
| F | 日常・癒し | 10% |

詳細は `analysis/persona_axis.md` を参照。

## 運用コマンド

### 手動で1本生成 → 推敲 → 投稿(本番)

```bash
.env で X_LIVE_POST=true にしてから:
./scripts/auto_tweet.sh
```

### 手動でドラフトだけ作る

```bash
/Users/user/Desktop/x-automation-wakana/venv/bin/python3 scripts/generate_draft.py
# テーマ指定: --theme A
# pending に残っていても追加生成: --force
```

### 手動で推敲だけ試す(本番投稿しない)

```bash
/Users/user/Desktop/x-automation-wakana/venv/bin/python3 scripts/pipeline.py --dry-run
```

### launchd 再読み込み

```bash
launchctl unload ~/Library/LaunchAgents/com.user.x-automation-oxp-emiri.plist
launchctl load   ~/Library/LaunchAgents/com.user.x-automation-oxp-emiri.plist
launchctl list | grep oxp-emiri   # 登録確認
```

### launchd を一時停止したいとき

```bash
launchctl unload ~/Library/LaunchAgents/com.user.x-automation-oxp-emiri.plist
```

## 安全装置

- `.env` の `X_LIVE_POST=false` の間は **dry-run のみ**(推敲結果をログに書くだけ、X には投稿されない)
- pending に未投稿が残っていれば `generate_draft.py` はスキップ(投稿待ち列が伸びない)
- 推敲結果が 280 文字を超えた場合は failed/ に移して停止
- 失敗時は failed/ にドラフトを退避し pipeline.log にエラーを残す

## 踏み込み禁止トピック(SYSTEM_PROMPT で禁止済み)

- 代表交代の経緯・前任との関係性
- 投資家・株主関係
- ミカタグループとの関係(口外しない)
- 還元率原資の内訳
- 結婚・パートナー
- 家族プライバシー(母がロシア人含む)
- 東日本大震災
- 他社・他個人批判
