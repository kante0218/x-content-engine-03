#!/usr/bin/env python3
"""えみり|オクパ 執行役員 用に、ペルソナ準拠の新規ドラフトを自動生成する。

- 6カテゴリ × 複数シードからランダム抽出
- Claude API に「えみりさんの素の独り言ドラフト」を書かせ、drafts/pending/ に保存
- pending に既にファイルが残っている場合はスキップ(投稿待ちが先)

Usage:
    python3 scripts/generate_draft.py
    python3 scripts/generate_draft.py --theme A   # カテゴリ強制
    python3 scripts/generate_draft.py --force     # pending に残っていても追加生成
"""
from __future__ import annotations

import datetime as dt
import json
import os
import random
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
sys.path.insert(0, str(ROOT / "scripts"))

from config import fetch_post_config, theme_map  # noqa: E402

PENDING = ROOT / "drafts" / "pending"
POSTED = ROOT / "drafts" / "posted"
LOGS = ROOT / "logs"

# 生成モデル。X_CLAUDE_MODEL 環境変数で切替可(未設定時 Sonnet 5)。
# 例: claude-opus-4-7 / claude-sonnet-5 / claude-haiku-4-5-20251001
MODEL = os.getenv("X_CLAUDE_MODEL", "claude-sonnet-5")

# テーマA-F: persona_axis.md と同期
THEMES = {
    "A": {
        "label": "エンジニアあるある",
        "ratio": 25,
        "seeds": [
            "面談で『前職の不満』を聞くと、評価への納得感のなさが必ず出てくる話",
            "もくもく作業を何時間も続けられるエンジニアへの素直な尊敬",
            "面談で『最近Claude Code触ってます』が増えた手応え",
            "案件選択制を初めて聞いたエンジニアの『え、本当ですか?』のリアクション",
            "リモート慣れすぎて、たまの出社が遠足モードになるエンジニア",
            "面談で『自分の市場価値が分からない』と言う人がここ最近すごく多い",
            "技術力はあるのに『コミュニケーション苦手で…』と謙遜する人ほど話してみると面白い",
            "成果は出してるのに評価で揉めて転職してきた人の共通点",
        ],
    },
    "B": {
        "label": "SES業界の透明化",
        "ratio": 20,
        "seeds": [
            "完全案件選択制100%を本当に維持できている理由",
            "営業都合のアサインゼロを実現する裏側(営業50人体制)",
            "還元率の高さがエンジニアのキャリアにどう効くか",
            "リファラル採用が3割を超える組織のカルチャー",
            "紹介特典20万円を続けている理由",
            "SES業界で『エンジニアをモノ扱いする会社』が未だに多い現実への違和感",
            "案件を選べるとキャリアの主導権が戻る、という当たり前の話",
            "未経験から1〜2年でコンサル領域に進める事実が業界で誤解されがちな件",
        ],
    },
    "C": {
        "label": "AIとエンジニア",
        "ratio": 15,
        "seeds": [
            "『AIに仕事を取られる』不安を持つベテランエンジニアにえみりが伝えたいこと",
            "Claude Codeを業務効率化ツールとして使い、思考は人間が持つというスタンス",
            "AIに勝てない部分(知識量)とAIに勝てる部分(顧客との関係構築・面談)",
            "ChatGPT有料版を全社員配布した理由",
            "日本のAI投資が世界より少ない現実への素朴な問題提起",
            "AIエージェント時代、エンジニアが磨くべきは要件定義力という確信",
            "AIに恋愛相談したらワクワクした話(軽め回)",
            "Claude Code/ChatGPT/Geminiを使い分ける日常",
        ],
    },
    "D": {
        "label": "採用担当の本音",
        "ratio": 15,
        "seeds": [
            "面談で必ず聞く『転職理由』と『なぜうちの会社か』、その意図",
            "面談で承諾後に飛ぶ/飛ばないが見抜けない悔しさ",
            "クロージング1時間で承諾を取れた瞬間の達成感",
            "暗い・覇気がない人を採用したくない、という本音",
            "コミュ力 × 要件定義まで自走できる、が今の市場価値の定義",
            "スキルアップ欲がない人はやっぱり長く活躍できない、というリアル",
            "下積みを下積みと捉えられる人が結局伸びる",
            "ベテランエンジニアがコンサル方向に舵を切るタイミング",
        ],
    },
    "E": {
        "label": "経営者・代表の素顔",
        "ratio": 15,
        "seeds": [
            "稲盛和夫『心』を何度も読み返す理由",
            "判断軸『自分が成長しそうかどうか』で迷いが減った話",
            "スピード重視と完璧主義の間で迷う日",
            "芸能事務所時代に学んだ『ビジュアルじゃなく実力で仕事をしたい』気持ち",
            "お天気キャスターのオーディションに受かった日のことを今でも覚えてる",
            "人前で話すのが実は苦手という告白(自虐は馬鹿にされない程度)",
            "経営者として一番怖いのは、エンジニア一人ひとりへのフォローが薄くなること",
            "『人はいつでも裏切る』と知った上で、それでも信じる選択をする(重め回・慎重に)",
        ],
    },
    "F": {
        "label": "日常・癒し",
        "ratio": 10,
        "seeds": [
            "週末の農作業のあとに飲むカフェラテが最高",
            "最近ハマってる自炊、野菜タンメンの話",
            "ランニング5kmが思考整理にちょうどいい",
            "廃墟系・空き家系YouTubeを見ながら田舎移住の妄想をする夜",
            "10年後は田舎で土地を買って週末農園を本気でやりたい",
            "家系ラーメンを食べたあとの罪悪感と幸福感",
            "ロシア旅行で見た景色がたまにフラッシュバックする",
            "朝に飲む一杯の水で1日が始まる、地味だけど大事",
        ],
    },
}


def _active_themes() -> dict:
    """ダッシュボード設定の有効テーマがあればそれを、無ければ組み込み THEMES を使う。"""
    cfg_themes = theme_map(fetch_post_config())
    if cfg_themes:
        sys.stderr.write(f"[config] テーマをダッシュボード設定から取得: {len(cfg_themes)}件\n")
        return cfg_themes
    return THEMES


def pick_theme(forced: str | None = None) -> tuple[str, str, str]:
    themes = _active_themes()
    if forced:
        if forced not in themes:
            raise ValueError(f"theme は {list(themes)} のいずれか")
        t = themes[forced]
        return forced, t["label"], random.choice(t["seeds"])
    keys = list(themes.keys())
    weights = [themes[k]["ratio"] for k in keys]
    k = random.choices(keys, weights=weights, k=1)[0]
    return k, themes[k]["label"], random.choice(themes[k]["seeds"])


def recent_seeds_to_avoid(n: int = 12) -> list[str]:
    """直近 n 件の posted を見て、似たトピック連発を避けるためのヒント"""
    if not POSTED.exists():
        return []
    files = sorted(
        (p for p in POSTED.iterdir() if p.suffix not in {".json"} and not p.name.startswith(".")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:n]
    out = []
    for f in files:
        try:
            txt = f.read_text(encoding="utf-8").strip()
            if txt:
                out.append(txt[:120])
        except Exception:
            pass
    return out


GENERATE_SYSTEM = """あなたは「えみり(@oxp_emiri)」=オックスフォードパートナーズ株式会社 執行役員 本人として、
これから自分のXに投稿する単体ツイートの**素のドラフト**を1つ書く。

仕上げの推敲は別工程で行うので、ここでは:
- 完成形でなくてよい。気持ちの温度感だけ正しく載せる
- **長さは毎回ほぼ最大長**(**260字前後を狙う、絶対280を超えない**)。エピソード+具体描写+気づき+本音 のように複数ブロックで密度を出す
- 一人称は必ず「私」。「えみり」と自称しない(三人称で自分を呼ばない)
- 絵文字は0〜2個程度、🌸に偏らせず色々な女性的な絵文字を散らす(最終的な絵文字は仕上げ工程で調整するので、ここでは温度感だけ)。派手系🔥💯💎🤑💸・白/赤ハート♡♥はNG
- **倒置法は禁止**: 述語のあとに副詞句を独立配置する語順(例: 「〜にしたい。本気で。」)はNG。自然な日本語の語順で書く
- 構成テンプレ(共感→気づき→締め)を毎回踏まない、毎回違う角度から入る
- 「みんなも頑張ろう」「素敵な一日を」みたいな定型締めは禁止
- AIが書いたと分かる流暢すぎる説明・大上段は禁止

# 本人プロフィール(重要なものだけ)
- 28歳、オックスフォードパートナーズ執行役員(SES企業、エンジニア採用責任者)
- 元お天気キャスター・芸能事務所所属を経て今の業界へ
- ポジティブ思考、せっかち、天然
- 趣味は農作業・自炊・読書(稲盛和夫『心』)・ランニング5km・廃墟系YouTube
- 食は家系ラーメン・カフェラテ。海鮮苦手
- 数百人のエンジニア面談経験
- 10年後は田舎で週末農園が夢

# 会社の事実
- 完全案件選択制100%、還元率最大100%(平均83%)
- フルリモート93%、営業50人体制、ChatGPT有料版全員配布
- 紹介特典20万円、リファラル比率3割
- ミッション「自分のキャリアは自分で。会社はあくまでフォロー」

# 絶対NG
- 代表交代・前任関係・株主・ミカタグループ・還元率原資・家族プライバシー(母がロシア人含む)・東日本大震災
- マジ/ガチ/だよな/だろ
- 他社・他者批判、強い断定、煽り

# 出力
- 本文のドラフトだけを返す。説明・前置き・引用符は一切なし
- 仕上げで整える前提なので完成度より素直さ優先"""


def generate(theme_key: str, theme_label: str, seed: str, avoid: list[str]) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY が未設定(https://aistudio.google.com/apikey で無料発行)")

    avoid_block = ""
    if avoid:
        avoid_block = (
            "\n# 直近の自分の投稿(似た角度・似た書き出しを避ける)\n"
            + "\n".join(f"- {t}" for t in avoid)
        )

    user_msg = (
        f"# 今回のテーマ\nカテゴリ: {theme_key} / {theme_label}\nネタの種: {seed}\n"
        + avoid_block
        + "\n\n上記の種を起点に、えみり本人が今ふと書きたくなって書く独り言ツイートのドラフトを1つだけ。"
        "完成形でなくてOK、気持ちの温度感を素直に載せて。"
    )

    client = Anthropic(api_key=api_key)
    res = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=GENERATE_SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(block.text for block in res.content if block.type == "text").strip()
    return text


def append_log(payload: dict) -> None:
    LOGS.mkdir(exist_ok=True)
    log = LOGS / "generate.log"
    payload = {"ts": dt.datetime.now(dt.timezone.utc).isoformat(), **payload}
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> int:
    args = sys.argv[1:]
    force = "--force" in args
    if force:
        args.remove("--force")
    theme_forced = None
    if "--theme" in args:
        i = args.index("--theme")
        theme_forced = args[i + 1]

    PENDING.mkdir(parents=True, exist_ok=True)
    existing = [p for p in PENDING.iterdir() if p.is_file() and not p.name.startswith(".")]
    if existing and not force:
        print(f"[skip] pending に {len(existing)} 件残っています。先に投稿してください(--force で追加生成)")
        append_log({"event": "skipped", "pending_count": len(existing)})
        return 0

    k, label, seed = pick_theme(theme_forced)
    print(f"[theme] {k} / {label}\n[seed] {seed}\n")
    avoid = recent_seeds_to_avoid()
    draft = generate(k, label, seed, avoid)
    print(f"[draft]\n{draft}\n")

    fname = f"{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{k}_auto.md"
    (PENDING / fname).write_text(draft, encoding="utf-8")
    append_log({"event": "generated", "file": fname, "theme": k, "label": label, "seed": seed, "chars": len(draft)})
    print(f"[saved] drafts/pending/{fname}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
