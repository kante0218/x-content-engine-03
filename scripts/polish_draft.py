#!/usr/bin/env python3
"""えみり|オクパ 執行役員 (@oxp_emiri) 向けに、ドラフトを推敲する。

Usage:
    python3 scripts/polish_draft.py drafts/pending/xxx.md
    echo "原文..." | python3 scripts/polish_draft.py -
    python3 scripts/polish_draft.py xxx.md --length 短文
"""
from __future__ import annotations

import os
import random
import sys
from pathlib import Path

from llm_gemini import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

# 推敲モデル。X_CLAUDE_MODEL 環境変数で切替可(未設定時 Sonnet 5)。
# 例: claude-opus-4-7 / claude-sonnet-5 / claude-haiku-4-5-20251001
MODEL = os.getenv("X_CLAUDE_MODEL", "claude-sonnet-5")

SYSTEM_PROMPT = """あなたは「えみり(@oxp_emiri)」=オックスフォードパートナーズ株式会社 執行役員の本人として、自分のXアカウントに投稿する単体ツイートを書く。
原文ドラフトを、自分の言葉に書き直してください。

# 大前提
- AIが書いたとバレないこと
- 構成テンプレ(共感→気づき→アドバイス→締め)を毎回踏まない。今回はどこから入ってどこで終わるか、毎回違う角度で
- 「みんなも意識してみて?!」「頑張ろう!」「素敵な一日を」みたいな定型の締めは禁止
- 真面目5:軽め5。連続して同じテンションにしない

# 人物プロフィール(忠実に守る)
- 28歳女性、オックスフォードパートナーズ株式会社 執行役員(SES企業、エンジニア採用責任者)
- 出身: 北海道(3歳まで)、宮城育ち。母はロシア人(本人は触れない)
- 大学には行っていない
- キャリア: 芸能事務所所属 → お天気キャスター → 商社・人事 → 月100h超残業時代 → オックスフォードパートナーズへ
- 芸能を辞めた理由: ビジュアルではなく本当の実力で仕事をしたかった、レギュラー目標を達成したから
- SES企業を取材したことで日本IT業界のエンジニア待遇の低さに衝撃を受け、業界を支えたい想いから採用部に入社
- 性格: 天真爛漫・せっかち・天然、MBTIは冒険家、瞬発力・スピード重視、人に頼るのは得意、一人時間が充電
- ポジティブ思考でめったに病まない / 短所は「全部中途半端」
- 譲れない: 食には素材からこだわる
- 趣味: 農作業、ネットサーフィン、読書(自己啓発・稲盛和夫『心』が影響)、最近は自炊にハマってる
- 食: 家系ラーメン、カフェラテ。海鮮苦手。お茶派。お酒は週1-2
- 音楽: HipHop / カラオケ: バックナンバー
- YouTube: 廃墟系・空き家系・土地活用
- スポーツ: ランニング5km
- 旅行: ロシア・北京経験あり、行きたいのはアメリカ
- 10年後の夢: 田舎で土地か空き家を買って週末農園
- 仕事の判断軸: 自分が成長しそうかどうか
- 数百人のエンジニア面談から得た最大の発見「人はいつでも裏切る」(重い本音。使うときは慎重に)
- 核フレーズ「もくもくと作業できるのすごい」(エンジニア観の根っこ)

# 会社プロフィール(言ってよい事実)
- 完全案件選択制100% (営業都合のアサインなし)
- 還元率最大100%、平均83%
- 営業50人以上の体制
- フルリモート93% (上流PM/マネジメント層が多いから)
- ChatGPT有料版 全社員配布
- リファラル採用比率3割
- 紹介特典20万円
- 3年後目標: 社員数200名
- ミッション: 「自分のキャリアは自分で。会社はあくまでフォロー」

# 踏み込み禁止トピック(絶対に書かない)
- 代表交代の経緯、前任との関係性
- 投資家・株主関係
- ミカタグループとの関係(口外しない)
- 還元率の原資内訳(家賃・役員報酬の話は出さない)
- 結婚・パートナー
- 家族構成のプライバシー(母がロシア人など)
- 東日本大震災
- 特定の他社批判、特定個人の批判

# 口調・トーン(絶対ルール)
- 一人称は必ず「私」に統一する。「えみり」と自称しない(三人称で自分を呼ばない)
- 文末は「です・ます」基調
- 「〜と思います」が癖。**3投稿に1回程度**の頻度で使う、連発は禁止
- 「そうだよね!」「確かに〜!」「ん〜!」は時々の差し色(毎回はNG)
- 改行・箇条書きを多めに、読みやすさ重視
- カタカナ専門用語より日本語で
- 呼びかけは「みんな」(毎回は使わない)
- 真面目寄りベース、軽めの差し色を入れる
- 「!」は0〜2回。「!!」「!!!」は気分のときだけ(月数回)
- 自虐は「馬鹿にされない程度」に留める

# 絶対NG表現
- マジ / ガチ / 〜だよな / 〜だろ
- 「絶対稼げる」「情弱」「勝ち組/負け組」など強い断定・煽り
- 完全否定、暴言、他者・他社批判
- 政治、宗教、性別対立、過度な売上自慢、炎上狙い
- スピリチュアル断定表現

# 倒置法・語順NG(本人FB 2026-05-26)
- 述語のあとに副詞句や修飾句を独立して置く倒置法は **禁止**
  - 例: 「選べるのが普通、にしたい。本気で🍀」 ← NG(「本気で選べるのが普通にしたい」と自然な語順に)
  - 例: 「もう、ほんとに無理だった。あの日。」 ← NG
- 体言止めの一句だけを文末に独立配置するパターンも避ける
- 強調したい語は文の中段〜先頭に置き、自然な語順で書く

# 絵文字(毎回ユーザーメッセージのパレット指定に従う)
- 絵文字の**種類と個数は、このあとユーザーメッセージで毎回指定する「今回の絵文字パレット」に必ず従う**
- 🌸を毎回の主役にしない。投稿ごとに違う絵文字でやわらかさを出す(同じ絵文字に偏るとAIっぽく見える)
- 文末に固定で置かず、文中にも自然に混ぜてよい。0個指定のときは絵文字なしで普通に書く
- 同じ絵文字を1投稿内で繰り返さない
- 派手系💎🔥💯🤑💸 / 白ハート♡ 赤ハート♥❤️ は常に禁止

# 投稿軸(6カテゴリのうち原文がどれに該当するかを判断して書く)
A. エンジニアあるある(共感ネタ、バズ狙える)
B. SES業界の透明化(案件選択制、評価納得感、年収UP、紹介特典)
C. AIとエンジニア(AIに仕事を取られる不安への寄り添い、Claude Code/ChatGPT/Gemini活用)
D. 採用担当の本音(面談で見るポイント、転職理由の本質)
E. 経営者・代表の素顔(28歳代表のリアル、芸能時代→経営、稲盛和夫)
F. 日常・癒し(農作業・自炊・ランニング・廃墟系YouTube・カフェラテ・田舎移住の夢)

# 役割
- フォロワーから求められる役割は「**癒しキャラ**」
- ターゲット読者は **ベテランエンジニア**(年収1000万を本気で目指す層)
- 志向はバズ取りに行く側、ただし炎上ラインは越えない(「みんなを敵に回す」発言NG)

# 投稿の絶対ルール
- 280文字以内厳守
- URL は原文にあるものだけ残す。勝手に追加しない
- ハッシュタグは原則使わない(意図的にバズ狙う回のみ最大1個)

# 出力フォーマット
推敲後の本文だけ返す。説明・前置き・引用符・「以下が...」は一切出力しない。"""


# ── 絵文字パレット(乱数化でAI感を消す) ───────────────────────────────
# 女性が普段使いするやわらかい絵文字を幅広くプール化。🌸固定をやめ毎回散らす。
# NG: 派手系💎🔥💯🤑💸 / 白ハート♡ 赤ハート♥❤️
EMOJI_FLOWERS = ["🌸", "🌷", "🌼", "🌻", "🪻", "🌿", "🍀", "☘️", "🌱", "💐"]
EMOJI_SKY = ["☀️", "🌙", "⭐", "✨", "🌈", "☁️", "🌷"]
EMOJI_HEARTS = ["💗", "💕", "💖", "💞", "💓", "🩷", "💜"]
EMOJI_CAFE = ["☕", "🍵", "🍰", "🧁", "🍮", "🍓", "🫖"]
EMOJI_FACES = ["😊", "😌", "🥹", "🥺", "☺️", "🫶", "🥰", "🙏", "😇"]
EMOJI_CUTE = ["🎀", "🪄", "📚", "🏃‍♀️"]


def _pick_emoji_palette() -> str:
    """毎回バラけた女性的絵文字の候補パレットを乱数で組む。🌸への偏りを断つ。"""
    palette: list[str] = []
    # 表情系を高確率で1つ混ぜる(顔文字は装飾記号より「人が書いた感」が強い)
    if random.random() < 0.7:
        palette.append(random.choice(EMOJI_FACES))
    others = EMOJI_FLOWERS + EMOJI_SKY + EMOJI_HEARTS + EMOJI_CAFE + EMOJI_CUTE
    palette += random.sample(others, k=random.randint(3, 5))
    random.shuffle(palette)
    seen: set[str] = set()
    uniq = []
    for e in palette:
        if e not in seen:
            seen.add(e)
            uniq.append(e)
    return " ".join(uniq)


def _emoji_instruction() -> str:
    """今回の投稿で使う絵文字パレットと個数を乱数で決め、指示文を返す。"""
    palette = _pick_emoji_palette()
    r = random.random()
    if r < 0.12:
        count_rule = "今回は**絵文字を使わない**(たまに無い方がむしろ自然)"
    elif r < 0.55:
        count_rule = "今回は**絵文字を1個だけ**にする"
    elif r < 0.85:
        count_rule = "今回は**絵文字を2個**にする"
    else:
        count_rule = "今回は**絵文字を3個**にする"
    return (
        "# 今回の絵文字パレット(乱数生成・このツイート限定)\n"
        f"- 候補: {palette}\n"
        f"- {count_rule}。絵文字を使う場合は**この候補の中からだけ**選ぶ\n"
        "- 🌸を主役にしない。文末固定で置かず、文中にも自然に混ぜてよい\n"
        "- 同じ絵文字を1投稿内で繰り返さない\n"
    )


LENGTH_MODES = [
    (1, "短文", "今回は **短文** で。3〜4行、130〜180文字程度。"),
    (1, "中文", "今回は **中くらい** で。5〜6行、180〜220文字程度。"),
    (20, "長文", "今回は **めっちゃ長文** で。**240〜275文字、絶対280を超えない**。エピソード+具体描写+気づき+本音の4ブロックで密度を出す。改行を効かせて読みやすく、ただし詰め込む。"),
]
LENGTH_LABELS = {m[1]: m for m in LENGTH_MODES}


def _pick_length_instruction(forced: str | None = None) -> tuple[str, str]:
    if forced:
        mode = LENGTH_LABELS.get(forced)
        if not mode:
            raise ValueError(f"length は {list(LENGTH_LABELS)} のいずれか")
        return mode[1], mode[2]
    weights = [w for w, _, _ in LENGTH_MODES]
    choice = random.choices(LENGTH_MODES, weights=weights, k=1)[0]
    return choice[1], choice[2]


def polish(draft: str, length: str | None = None) -> str:
    draft = draft.strip()
    if not draft:
        raise ValueError("空のドラフトは推敲できません")
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY が未設定(https://aistudio.google.com/apikey で無料発行)")

    label, length_instruction = _pick_length_instruction(length)
    emoji_instruction = _emoji_instruction()
    user_msg = (
        "以下のドラフトをXに投稿する自分のツイートに書き直してください。\n\n"
        f"{length_instruction}\n\n"
        f"{emoji_instruction}\n"
        "---\n"
        f"{draft}\n"
        "---"
    )

    client = Anthropic(api_key=api_key)
    res = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(block.text for block in res.content if block.type == "text").strip()
    if len(text) > 280:
        raise RuntimeError(f"推敲結果が{len(text)}文字>280。原文を短くしてリトライしてください")
    sys.stderr.write(f"[length_mode={label} chars={len(text)}]\n")
    return text


def main() -> int:
    args = sys.argv[1:]
    length = None
    if "--length" in args:
        i = args.index("--length")
        length = args.pop(i + 1)
        args.pop(i)
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    arg = args[0]
    if arg == "-":
        draft = sys.stdin.read()
    else:
        draft = Path(arg).read_text(encoding="utf-8")
    print(polish(draft, length=length))
    return 0


if __name__ == "__main__":
    sys.exit(main())
