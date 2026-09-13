# XトレンドからLINEへ投稿案を届ける

`scripts/trend_suggestions.py` は日本のXトレンドを1回取得し、えみり・若菜の短文案（3〜35文字）と長文案（60〜130文字）を1件ずつ作ります。候補はLINEで人が確認する用途です。Xへの投稿処理や投稿待ちフォルダとの連携はありません。

## 実行

既存の `.env` または実行環境に、次の設定が必要です。この実装は設定ファイルを書き換えません。

- `X_BEARER_TOKEN`: XトレンドAPIを使えるトークンとAPI残高。
- `GEMINI_API_KEY`: 既存のGemini生成処理用キー。`GOOGLE_API_KEY` / `GEMINI_API_KEY_2` も既存処理で利用できます。クラウドのSecretはローカル実行には自動で渡りません。
- `LINE_CHANNEL_ACCESS_TOKEN`: 送信するLINE公式アカウントのMessaging APIチャネルアクセストークン。
- `LINE_TO`: ユーザーが指定・確認した送信先のユーザーID、グループID、ルームID。表示名・電話番号・友だち追加URLではありません。対象ユーザーによる友だち追加、または対象グループへのBot参加など、LINEの送信条件を満たす必要があります。

```sh
cd /Users/user/x-automation-oxp-emiri
# プレビューが既定。X/Gemini APIは利用するためAPI費用が発生し得ます。LINE送信はしません。
./venv/bin/python scripts/trend_suggestions.py
# 確認済みのLINE宛先へ、2アカウント分の提案をまとめて送る
./venv/bin/python scripts/trend_suggestions.py --send
# 1アカウントだけプレビュー
./venv/bin/python scripts/trend_suggestions.py --account wakana
# 外部通信なしの回帰チェック
./venv/bin/python scripts/test_trend_suggestions.py
```

定期実行する場合は同じローカル環境で上記 `--send` を1日1回実行します。認証・宛先・X残高の確認が済むまで有効化しません。このスクリプト自体は定期実行を登録しません。

## 保存と再実行

`drafts/trend_suggestions/` にプレビューとLINE受付状態を保存します。通常の `drafts/pending/` に入りません。日本時間で同じ日の同じアカウント構成は受付済みならスキップします。定期実行は既定の2名構成に統一してください。`--account emiri` と既定の2名構成は別の配信なので、混ぜるとえみりの案を二重に届けます。

ネットワーク切断時も本文・宛先・LINEリトライキーを保存したままにし、次の実行で同じリクエストを再送します。LINE側の重複受付応答も受付済みとして扱います。23時間を超えた未確定送信は自動再送を停止します。宛先のLINEと保存状態を人が照合してから整理してください。未確定の状態ファイルを安易に削除しないでください。APIによる受付は相手の受信・閲覧の証明ではありません。

トレンドが取得できない、生成内容が形式や長さに合わない場合は送信しません。ニュースの事実をトレンド名だけから補いません。投稿前にリンク先で文脈と事実、本人の意向を確認してください。

2026-09-13の接続確認ではX APIがHTTP 402（クレジット不足）を返しました。ローカルの生成用キー、LINE認証・送信先の設定も確認が必要です。これらが解決するまで実配信は未検証です。

公式仕様: [XトレンドAPI](https://docs.x.com/x-api/trends/get-trends-by-woeid)、[LINEリトライキー](https://developers.line.biz/en/docs/messaging-api/retrying-api-request/)。
