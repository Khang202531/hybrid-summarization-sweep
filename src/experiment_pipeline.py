"""
改良版ハイブリッド要約実験 ― 抽出率スイープ
==============================================
改善点（論文レビューに基づく）:
  [1] XL-Sum Japanese から 30 件のテキスト + 参照要約を取得
  [2] BERTScore / ROUGE / KW を「参照要約」と比較（元テキストではなく）
  [3] ROUGE-1/2/L を追加（日本語対応カスタムトークナイザで文字レベル N-gram）
  [4] BART 入力トークン数・上限超過フラグを CSV に記録
  [5] 抽出率ごとに平均 ± 標準偏差を集計 CSV に出力
  [6] 全ハイパーパラメータを設定セクション（§2）に集約

必要パッケージ（Colab でのインストール例）:
  !pip install datasets rouge-score bert-score fugashi unidic-lite transformers torch -q
"""

# ─────────────────────────────────────────────
# 1. 環境検出 & ライブラリ
# ─────────────────────────────────────────────
import re
import csv
import math
import os
import random
import warnings
import statistics
from collections import Counter
from datetime import datetime
from typing import Dict, List, Optional, Tuple

try:
    import google.colab          # type: ignore
    IS_COLAB = True
except ImportError:
    IS_COLAB = False

from datasets import load_dataset
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from bert_score import score as bert_score_fn
from rouge_score import rouge_scorer as rouge_lib

warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# 2. ハイパーパラメータ設定（全て一箇所で管理）
# ─────────────────────────────────────────────

# ── モデル ──────────────────────────────────
MODEL_NAME          = "stockmark/bart-base-japanese-news"
BART_MAX_INPUT      = 512    # BART の最大入力トークン数（この値を超えると切り捨て）
GENERATIVE_RATIO    = 0.60   # 生成要約の目標圧縮率（元テキストトークン比）
GEN_MIN_RATIO       = 0.40   # min_new_tokens = max_new_tokens × この割合
NUM_BEAMS           = 4      # ビームサーチのビーム数
LENGTH_PENALTY      = 2.0    # 長い要約を優遇する度合い（>1 で長め）
REPETITION_PENALTY  = 1.3    # 同一表現の繰り返しを抑制
NO_REPEAT_NGRAM     = 2      # この N-gram の繰り返しを禁止

# ── 生成長制御 [改善 B] ──────────────────────
# True : 抽出後テキスト基準で生成長を決定（改善版）
# False: 原文全体基準で生成長を決定（旧版、比較実験用に残す）
GEN_LENGTH_FROM_EXTRACTED = True

# ── 抽出アルゴリズム ─────────────────────────
# ── 抽出アルゴリズム ─────────────────────────
EXTRACTIVE_RATIOS   = [round(i / 100, 2) for i in range(1, 101)]  # 1%〜100%
MMR_LAMBDA          = 0.70   # MMR: 0=多様性重視 / 1=関連性重視
POSITION_BONUS      = 0.15   # 文頭ボーナス係数（先頭文を優先する強さ）
POSITION_DECAY      = 3.0    # 文頭ボーナスの減衰率（exp の指数）
TAIL_BONUS          = 0.05   # 末尾文へのボーナス（結論文を拾いやすくする）

# ── アブレーション [改善 F] ──────────────────
# 各要素をON/OFFして寄与を分解するためのフラグ
USE_TFIDF           = True   # TF-IDFベースの重要度スコア
USE_POSITION        = True   # 文位置ボーナス（文頭・末尾）
USE_MMR             = True   # MMRによる冗長性抑制

# ── データ ──────────────────────────────────
N_TEXTS             = 30     # 使用テキスト数（増やすほど結果の信頼性が上がる）
TEXT_MIN_CHARS      = 300    # テキストの最小文字数
TEXT_MAX_CHARS      = 1200   # テキストの最大文字数
DATASET_SPLIT       = "test" # XL-Sum のスプリット（"train"/"validation"/"test"）
RANDOM_SEED         = 42     # サンプリングの乱数シード（再現性のため固定）

# ── 複数シード [改善 I] ─────────────────────
# シード42 (第1段階予備実験), シード123 (第2段階本実験), シード2024 (再現性確認)
RANDOM_SEEDS        = [42, 123, 2024]

# ── ベースライン [改善 E] ────────────────────
# True にすると Pure Extraction, Lead-3+生成, ランダム抽出+生成 のベースラインも同時に評価
RUN_ADDITIONAL_BASELINES = True

# ── 評価 ────────────────────────────────────
BERTSCORE_LANG      = "ja"
KW_TOP_K            = 100    # キーワード一致率で使うバイグラム数

# ── ROUGE トークナイザ [改善 H] ──────────────
# True にすると fugashi ベースの単語単位 ROUGE も並行計算
ROUGE_MORPHEME      = True

OUTPUT_DIR = "/content" if IS_COLAB else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


# ─────────────────────────────────────────────
# 3. データ読み込み（XL-Sum Japanese）
#    [改善 1] 3 件のハードコード → 30 件の公開データセット
#    [改善 2] 参照要約（reference）を同時に取得
# ─────────────────────────────────────────────

def load_xlsum_japanese(
    n: int = N_TEXTS,
    min_chars: int = TEXT_MIN_CHARS,
    max_chars: int = TEXT_MAX_CHARS,
    split: str = DATASET_SPLIT,
    seed: int = RANDOM_SEED,
) -> List[Dict[str, str]]:
    """
    XL-Sum Japanese から { text, reference, title } のペアを n 件返す。

    Parameters
    ----------
    n         : 取得件数
    min_chars : テキスト本文の最小文字数
    max_chars : テキスト本文の最大文字数
    split     : "train" / "validation" / "test"
    seed      : サンプリング乱数シード

    Returns
    -------
    list of dict
        text      : BBC Japan 記事本文
        reference : データセット付属の人手参照要約 ← 評価の基準に使用
        title     : 記事タイトル
    """
    print(f"[DATA] XL-Sum Japanese ({split}) を読み込み中 ...")
    data_files = {
        split: f"hf://datasets/csebuetnlp/xlsum@refs/convert/parquet/japanese/{split}/*.parquet"
    }
    ds = load_dataset(
        "parquet",
        data_files=data_files,
        split=split,
    )

    filtered = [
        {
            "text"     : row["text"].strip(),
            "reference": row["summary"].strip(),
            "title"    : row["title"].strip(),
        }
        for row in ds
        if min_chars <= len(row["text"].strip()) <= max_chars
        and len(row["summary"].strip()) >= 20   # 参照要約が短すぎるものを除外
    ]

    if len(filtered) < n:
        raise ValueError(
            f"条件を満たすテキストが {len(filtered)} 件のみ（必要: {n} 件）。\n"
            f"TEXT_MIN_CHARS / TEXT_MAX_CHARS を調整してください。"
        )

    rng     = random.Random(seed)
    sampled = rng.sample(filtered, n)

    print(f"[DATA] {len(ds):,} 件中 {len(filtered):,} 件がフィルタ条件に一致 → {n} 件をサンプリング")
    print(f"[DATA] 本文字数   : {min(len(d['text']) for d in sampled)}〜"
          f"{max(len(d['text']) for d in sampled)} 字")
    print(f"[DATA] 参照要約   : {min(len(d['reference']) for d in sampled)}〜"
          f"{max(len(d['reference']) for d in sampled)} 字")
    print(f"[DATA] 例) {sampled[0]['title'][:40]}...\n")
    return sampled


# ─────────────────────────────────────────────
# 4. テキスト前処理
# ─────────────────────────────────────────────

def preprocess(text: str) -> str:
    text = re.sub(r"\n+", "。", text)
    text = re.sub(r"　+", " ", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def split_sentences(text: str) -> List[str]:
    sentences = re.split(r"(?<=[。！？])", text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]


# ─────────────────────────────────────────────
# 5. 抽出型要約（TF-IDF + 位置スコア + MMR）
# ─────────────────────────────────────────────

def _compute_tfidf(sentences: List[str]) -> List[Dict[str, float]]:
    """文字バイグラム TF-IDF を計算"""
    def bigram_tokens(s: str) -> List[str]:
        return [s[i:i + 2] for i in range(len(s) - 1)]

    tokenized = [bigram_tokens(s) for s in sentences]
    n         = len(tokenized)
    tf_list   = [Counter(t) for t in tokenized]

    df: Counter = Counter()
    for t in tokenized:
        for tok in set(t):
            df[tok] += 1

    idf = {tok: math.log((n + 1) / (freq + 1)) + 1
           for tok, freq in df.items()}

    result = []
    for tf in tf_list:
        total = sum(tf.values()) or 1
        result.append(
            {tok: (cnt / total) * idf.get(tok, 1.0)
             for tok, cnt in tf.items()}
        )
    return result


def _cosine_sim(a: Dict[str, float], b: Dict[str, float]) -> float:
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[k] * b[k] for k in common)
    na  = math.sqrt(sum(v * v for v in a.values()))
    nb  = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


def extractive_summary(
    text: str,
    ratio: float,
    use_tfidf: bool = None,
    use_position: bool = None,
    use_mmr: bool = None,
) -> str:
    """
    MMR_LAMBDA / POSITION_BONUS / POSITION_DECAY / TAIL_BONUS は §2 で制御。
    抽出比率 ratio (0.01〜0.99) で文を選択して返す。

    [改善 F] use_tfidf / use_position / use_mmr でアブレーション実験に対応。
    None の場合は §2 のグローバル設定を使用。
    """
    # アブレーションフラグ: 引数 > グローバル設定
    _use_tfidf    = USE_TFIDF    if use_tfidf    is None else use_tfidf
    _use_position = USE_POSITION if use_position is None else use_position
    _use_mmr      = USE_MMR      if use_mmr      is None else use_mmr

    sentences = split_sentences(text)
    if not sentences:
        return text

    top_n = max(1, round(len(sentences) * ratio))
    top_n = min(top_n, len(sentences))

    tfidf_list = _compute_tfidf(sentences)
    n          = len(sentences)

    # 関連度スコア（TF-IDF + 文位置ボーナス） [改善 F]
    relevance: Dict[int, float] = {}
    for idx, vec in enumerate(tfidf_list):
        # TF-IDF スコア
        lnorm  = math.sqrt(max(len(sentences[idx]), 1))
        tfidf_score = sum(vec.values()) / lnorm if _use_tfidf else 1.0 / n

        # 文位置ボーナス
        if _use_position:
            pos    = idx / max(n - 1, 1)
            bonus  = POSITION_BONUS * math.exp(-POSITION_DECAY * pos)
            bonus += TAIL_BONUS if idx == n - 1 else 0.0
        else:
            bonus = 0.0

        relevance[idx] = tfidf_score + bonus

    # MMR で冗長性を抑えながら選択 [改善 F]
    selected: List[int] = []
    remaining = list(range(n))

    while len(selected) < top_n and remaining:
        if not selected or not _use_mmr:
            best = max(remaining, key=lambda i: relevance[i])
        else:
            def mmr_score(
                i: int,
                _sel=selected,
                _tf=tfidf_list,
                _rel=relevance,
            ) -> float:
                sim = max(_cosine_sim(_tf[i], _tf[j]) for j in _sel)
                return MMR_LAMBDA * _rel[i] - (1 - MMR_LAMBDA) * sim
            best = max(remaining, key=mmr_score)
        selected.append(best)
        remaining.remove(best)

    selected.sort()
    return "".join(sentences[i] for i in selected)


def lead_n_summary(text: str, ratio: float) -> str:
    """
    [改善 E] Lead-N法ベースライン。
    先頭からN文をそのまま抽出する（TF-IDF/MMR不使用）。
    """
    sentences = split_sentences(text)
    if not sentences:
        return text
    top_n = max(1, round(len(sentences) * ratio))
    top_n = min(top_n, len(sentences))
    return "".join(sentences[:top_n])


def random_extractive_summary(text: str, ratio: float, seed: int = 42) -> str:
    """
    [改善 E] ランダム抽出ベースライン。
    同じ抽出率でランダムに文を選択する（下限比較用）。
    """
    sentences = split_sentences(text)
    if not sentences:
        return text
    top_n = max(1, round(len(sentences) * ratio))
    top_n = min(top_n, len(sentences))
    rng = random.Random(seed)
    selected = sorted(rng.sample(range(len(sentences)), top_n))
    return "".join(sentences[i] for i in selected)


# ─────────────────────────────────────────────
# 6. モデルのロード
# ─────────────────────────────────────────────

def load_model(model_name: str = MODEL_NAME):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype  = torch.float16 if device == "cuda" else torch.float32

    env = "Google Colab" if IS_COLAB else "ローカル PC"
    print(f"[MODEL] 実行環境     : {env}")
    print(f"[MODEL] 使用デバイス : {device.upper()}")
    if device == "cuda":
        print(f"[MODEL] GPU          : {torch.cuda.get_device_name(0)}")
        vram = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"[MODEL] VRAM         : {vram:.1f} GB")
    print(f"[MODEL] モデル       : {model_name}")

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = (
        AutoModelForSeq2SeqLM
        .from_pretrained(model_name, torch_dtype=dtype, trust_remote_code=True)
        .to(device)
    )
    model.eval()
    print("[MODEL] 読み込み完了\n")
    return tokenizer, model, device


# ─────────────────────────────────────────────
# 7. 生成型要約（BART）
#    [改善 4] 入力トークン数・上限超過フラグを返す
# ─────────────────────────────────────────────

def generative_summary(
    text: str,
    tokenizer,
    model,
    device: str,
    original_text: str,
) -> Tuple[str, int, bool]:
    """
    BART で要約し (生成テキスト, 入力トークン数, 切り捨てフラグ) を返す。

    input_token_count : BART に実際に渡されたトークン数
    was_truncated     : BART_MAX_INPUT を超えて切り捨てが発生した場合 True

    [改善 B] GEN_LENGTH_FROM_EXTRACTED の設定により、生成長の基準を
    「抽出後テキスト」または「原文全体」から選択可能。
    """
    # [改善 B] 生成長の基準テキストを選択
    if GEN_LENGTH_FROM_EXTRACTED:
        # 改善版: 抽出後テキスト基準
        length_basis = text
    else:
        # 旧版: 原文全体基準（比較実験用に残す）
        length_basis = original_text

    enc_basis = tokenizer(
        length_basis, return_tensors="pt",
        truncation=True, max_length=BART_MAX_INPUT,
    )
    max_new  = max(20, int(enc_basis["input_ids"].shape[1] * GENERATIVE_RATIO))
    min_new  = max(10, int(max_new * GEN_MIN_RATIO))

    # 上限超過チェック（切り捨て前のトークン数を確認）
    raw_tokens    = tokenizer(text, return_tensors="pt")["input_ids"].shape[1]
    was_truncated = raw_tokens > BART_MAX_INPUT

    # エンコード（truncation=True で BART_MAX_INPUT に収める）
    enc = tokenizer(
        text, return_tensors="pt",
        max_length=BART_MAX_INPUT,
        truncation=True,
        padding=True,
    ).to(device)
    input_token_count = enc["input_ids"].shape[1]

    with torch.no_grad():
        out = model.generate(
            **enc,
            max_new_tokens       = max_new,
            min_new_tokens       = min_new,
            num_beams            = NUM_BEAMS,
            length_penalty       = LENGTH_PENALTY,
            repetition_penalty   = REPETITION_PENALTY,
            no_repeat_ngram_size = NO_REPEAT_NGRAM,
            early_stopping       = True,
        )
    summary = tokenizer.decode(out[0], skip_special_tokens=True)
    return summary, input_token_count, was_truncated


# ─────────────────────────────────────────────
# 8. 評価指標
#    [改善 2] 参照要約（reference）を基準に評価
#    [改善 3] ROUGE-1/2/L を追加（日本語対応カスタムトークナイザ）
#
#  ※ rouge_score のデフォルトトークナイザは ASCII 以外を除去するため
#    日本語テキストで常に 0 になるバグがある。
#    _JaCharTokenizer を渡すことで文字単位の N-gram に切り替え、これを回避する。
# ─────────────────────────────────────────────

class _JaCharTokenizer:
    """
    日本語 ROUGE 用カスタムトークナイザ（文字単位版）。
    空白を除去したうえで 1 文字ずつリストに分割する。
    rouge_score ライブラリの tokenizer 引数に渡して使用。
    """
    def tokenize(self, text: str) -> List[str]:
        return list(re.sub(r"\s+", "", text))


class _JaMorphTokenizer:
    """
    [改善 H] 日本語 ROUGE 用カスタムトークナイザ（形態素解析版）。
    fugashi で分かち書きした単語単位でトークナイズする。
    文字 bigram 版との傾向の一致・不一致を比較するために使用。
    """
    def __init__(self):
        import fugashi
        self._tagger = fugashi.Tagger()

    def tokenize(self, text: str) -> List[str]:
        text = re.sub(r"\s+", "", text)
        return [word.surface for word in self._tagger(text) if word.surface.strip()]


# スコアラーをモジュールロード時に一度だけ初期化
_rouge_scorer = rouge_lib.RougeScorer(
    ["rouge1", "rouge2", "rougeL"],
    tokenizer=_JaCharTokenizer(),   # ← カスタムトークナイザで日本語に対応
)

# [改善 H] 形態素解析ベースのROUGEスコアラー
_rouge_scorer_morph = None
if ROUGE_MORPHEME:
    try:
        _rouge_scorer_morph = rouge_lib.RougeScorer(
            ["rouge1", "rouge2", "rougeL"],
            tokenizer=_JaMorphTokenizer(),
        )
    except ImportError:
        print("[WARN] fugashi が利用できないため形態素解析版 ROUGE は無効化されます")
        ROUGE_MORPHEME = False


_fugashi_tagger = None
if ROUGE_MORPHEME:
    try:
        import fugashi
        _fugashi_tagger = fugashi.Tagger()
    except Exception:
        pass


def keyword_match_rate(reference: str, summary: str, top_k: int = KW_TOP_K) -> float:
    """
    参照要約中の頻出バイグラム Top-K が要約に何割含まれるかを返す（文字バイグラム版）。
    """
    def bigrams(t: str) -> Counter:
        t = re.sub(r"\s", "", t)
        return Counter(t[i:i + 2] for i in range(len(t) - 1))

    ref_bg   = bigrams(reference)
    summ_set = set(bigrams(summary).keys())
    top_kw   = [kw for kw, _ in ref_bg.most_common(top_k)]
    if not top_kw:
        return 0.0
    return sum(1 for kw in top_kw if kw in summ_set) / len(top_kw)


def keyword_content_word_match(reference: str, summary: str) -> float:
    """
    参照要約中の内容語（名詞・動詞・形容詞）が要約に何割含まれるかを計算する（fugashi 形態素解析版）。
    """
    if _fugashi_tagger is None:
        return 0.0
    
    def get_content_words(t: str) -> set:
        t = re.sub(r"\s+", "", t)
        words = set()
        for word in _fugashi_tagger(t):
            if not word.surface.strip():
                continue
            try:
                pos = word.feature.pos1 if hasattr(word.feature, 'pos1') else (word.feature[0] if isinstance(word.feature, tuple) else "")
            except Exception:
                pos = ""
            if pos in ['名詞', '動詞', '形容詞']:
                words.add(word.surface)
        return words

    ref_words = get_content_words(reference)
    if not ref_words:
        return 0.0
    summ_words = get_content_words(summary)
    return sum(1 for w in ref_words if w in summ_words) / len(ref_words)


def evaluate(
    reference: str,
    summary: str,
    device: Optional[str] = None,
) -> Dict[str, float]:
    """
    BERTScore + ROUGE-1/2/L + キーワード一致率（バイグラム & 形態素内容語）を参照要約と比較して計算。
    """
    # BERTScore（文脈埋め込みによる意味的類似度）
    _, _, F1 = bert_score_fn(
        [summary], [reference],
        lang=BERTSCORE_LANG,
        device=device,
        verbose=False,
    )

    # ROUGE（_JaCharTokenizer により文字レベル N-gram で計算）
    r = _rouge_scorer.score(reference, summary)

    result = {
        "bert_f1"          : round(F1.item(), 4),
        "rouge1"           : round(r["rouge1"].fmeasure, 4),
        "rouge2"           : round(r["rouge2"].fmeasure, 4),
        "rougeL"           : round(r["rougeL"].fmeasure, 4),
        "kw_match"         : round(keyword_match_rate(reference, summary), 4),
        "kw_content_match" : round(keyword_content_word_match(reference, summary), 4),
    }

    # [改善 H] 形態素解析ベースの ROUGE を並行計算
    if ROUGE_MORPHEME and _rouge_scorer_morph is not None:
        r_morph = _rouge_scorer_morph.score(reference, summary)
        result["rouge1_morph"] = round(r_morph["rouge1"].fmeasure, 4)
        result["rouge2_morph"] = round(r_morph["rouge2"].fmeasure, 4)
        result["rougeL_morph"] = round(r_morph["rougeL"].fmeasure, 4)

    return result


# ─────────────────────────────────────────────
# 9. 実験ループ
# ─────────────────────────────────────────────

def run_experiment(
    data: List[Dict[str, str]],
    extractive_ratios: List[float] = EXTRACTIVE_RATIOS,
    seed: int = 42,
) -> None:
    """
    100 ステップ × N_TEXTS = (N_TEXTS × 100) 回のハイブリッド要約
    + N_TEXTS 回の生成型のみ要約（ベースライン）
    + 4つのベースライン比較
    + MMR lambda 感度分析
    → 詳細 CSV、集計 CSV、ベースライン CSV、感度分析 CSV を保存
    """
    tokenizer, model, device = load_model()

    n_texts = len(data)
    total   = n_texts * len(extractive_ratios)

    gen_basis = "抽出後テキスト" if GEN_LENGTH_FROM_EXTRACTED else "原文全体"
    print(f"[RUN] シード       : {seed}")
    print(f"[RUN] テキスト数   : {n_texts}")
    print(f"[RUN] 抽出比率     : {extractive_ratios[0]*100:.0f}%〜"
          f"{extractive_ratios[-1]*100:.0f}%  ({len(extractive_ratios)} ステップ)")
    print(f"[RUN] 生成目標圧縮 : {GENERATIVE_RATIO*100:.0f}%  (min {GEN_MIN_RATIO*100:.0f}%)")
    print(f"[RUN] 生成長基準   : {gen_basis}")
    print(f"[RUN] 合計         : ハイブリッド {total} 回 + ベースライン {n_texts} 回")
    print(f"[RUN] MMR λ        : {MMR_LAMBDA}")
    print(f"[RUN] アブレーション: TF-IDF={USE_TFIDF} 位置={USE_POSITION} MMR={USE_MMR}")
    print(f"[RUN] 形態素ROUGE  : {ROUGE_MORPHEME}")
    print(f"[RUN] BART 上限    : {BART_MAX_INPUT} トークン\n")

    rows: List[Dict] = []
    baseline_rows: List[Dict] = []
    sensitivity_rows: List[Dict] = []
    run = 0

    for text_idx, item in enumerate(data, start=1):
        text      = preprocess(item["text"])
        reference = item["reference"]       # ← 評価の基準（参照要約）
        orig_len  = len(text)
        ref_len   = len(reference)

        print(f"{'=' * 65}")
        print(f"  テキスト {text_idx}/{n_texts}  "
              f"本文: {orig_len} 字 / 参照要約: {ref_len} 字")
        print(f"  見出し: {item['title'][:50]}")
        print(f"{'=' * 65}")

        # ── 1. 生成型のみ (Base 1: BART Full Text) ────────────────
        gen_only, gen_tok, gen_trunc = generative_summary(
            text, tokenizer, model, device, original_text=text,
        )
        ev_gen  = evaluate(reference, gen_only, device=device)
        trunc_m = " [TRUNC]" if gen_trunc else ""
        print(
            f"  [BASE 1 (Gen Only)] tok={gen_tok}{trunc_m}"
            f"  F1={ev_gen['bert_f1']:.4f}"
            f"  R1={ev_gen['rouge1']:.4f}"
            f"  R2={ev_gen['rouge2']:.4f}"
            f"  KW_Cont={ev_gen['kw_content_match']:.4f}"
        )

        # ── 追加ベースライン (Base 2, Base 3, Base 4) ────────────
        if RUN_ADDITIONAL_BASELINES:
            # Base 2: 純粋抽出型 (TF-IDF + MMR 50%, 生成なし)
            pure_ext_text = extractive_summary(text, ratio=0.50)
            ev_pure_ext   = evaluate(reference, pure_ext_text, device=device)

            # Base 3: Lead-3 + BART 生成
            lead3_ext     = lead_n_summary(text, ratio=0.50)
            lead3_gen, lead3_tok, lead3_trunc = generative_summary(
                lead3_ext, tokenizer, model, device, original_text=text,
            )
            ev_lead3      = evaluate(reference, lead3_gen, device=device)

            # Base 4: ランダム抽出 50% + BART 生成
            rand_ext      = random_extractive_summary(text, ratio=0.50, seed=seed)
            rand_gen, rand_tok, rand_trunc = generative_summary(
                rand_ext, tokenizer, model, device, original_text=text,
            )
            ev_rand       = evaluate(reference, rand_gen, device=device)

            baseline_rows.append({
                "text_idx": text_idx, "seed": seed,
                "b1_bert_f1": ev_gen["bert_f1"], "b1_rouge1": ev_gen["rouge1"], "b1_rouge2": ev_gen["rouge2"], "b1_rougeL": ev_gen["rougeL"], "b1_kw_content": ev_gen["kw_content_match"],
                "b2_bert_f1": ev_pure_ext["bert_f1"], "b2_rouge1": ev_pure_ext["rouge1"], "b2_rouge2": ev_pure_ext["rouge2"], "b2_rougeL": ev_pure_ext["rougeL"], "b2_kw_content": ev_pure_ext["kw_content_match"],
                "b3_bert_f1": ev_lead3["bert_f1"], "b3_rouge1": ev_lead3["rouge1"], "b3_rouge2": ev_lead3["rouge2"], "b3_rougeL": ev_lead3["rougeL"], "b3_kw_content": ev_lead3["kw_content_match"],
                "b4_bert_f1": ev_rand["bert_f1"], "b4_rouge1": ev_rand["rouge1"], "b4_rouge2": ev_rand["rouge2"], "b4_rougeL": ev_rand["rougeL"], "b4_kw_content": ev_rand["kw_content_match"],
            })

        # ── MMR λ 感度分析 (λ = 0.5, 0.6, 0.7, 0.8, 0.9) ─────────
        for lam in [0.5, 0.6, 0.7, 0.8, 0.9]:
            # 一時的にグローバル λ をセット
            old_lam = MMR_LAMBDA
            globals()['MMR_LAMBDA'] = lam
            ext_lam = extractive_summary(text, ratio=0.50)
            globals()['MMR_LAMBDA'] = old_lam

            gen_lam, _, _ = generative_summary(
                ext_lam, tokenizer, model, device, original_text=text,
            )
            ev_lam = evaluate(reference, gen_lam, device=device)
            sensitivity_rows.append({
                "text_idx": text_idx, "seed": seed, "lambda": lam,
                "bert_f1": ev_lam["bert_f1"], "rouge1": ev_lam["rouge1"],
                "rouge2": ev_lam["rouge2"], "rougeL": ev_lam["rougeL"],
                "kw_content_match": ev_lam["kw_content_match"],
            })

        # ── ハイブリッド × 100 比率 ────────────────────
        for ext_r in extractive_ratios:
            run += 1
            pct = int(round(ext_r * 100))
            print(f"  [{run:>4}/{total}] ext {pct:>3}% ...", end=" ", flush=True)

            extracted = extractive_summary(text, ratio=ext_r)
            ext_len   = len(extracted)

            hybrid, hyb_tok, hyb_trunc = generative_summary(
                extracted, tokenizer, model, device, original_text=text,
            )
            hyb_len = len(hybrid)
            ev_hyb  = evaluate(reference, hybrid, device=device)

            trunc_m = " [T]" if hyb_trunc else ""
            print(
                f"tok={hyb_tok}{trunc_m}"
                f"  F1={ev_hyb['bert_f1']:.4f}"
                f"  R1={ev_hyb['rouge1']:.4f}"
                f"  R2={ev_hyb['rouge2']:.4f}"
                f"  KW_Cont={ev_hyb['kw_content_match']:.4f}"
            )

            row_data = {
                # ── 識別子 ──────────────────────────────
                "text_idx"           : text_idx,
                "seed"               : seed,
                "ext_ratio_pct"      : pct,
                # ── テキスト情報 ─────────────────────────
                "orig_chars"         : orig_len,
                "ref_chars"          : ref_len,
                "ext_chars"          : ext_len,
                "hyb_chars"          : hyb_len,
                "hyb_ratio"          : round(hyb_len / orig_len, 3),
                # ── BART トークン情報 [改善 4] ───────────
                "bart_input_tokens"  : hyb_tok,
                "bart_truncated"     : int(hyb_trunc),
                # ── ハイブリッド評価（vs 参照要約）[改善 2,3] ──
                "hyb_bert_f1"          : ev_hyb["bert_f1"],
                "hyb_rouge1"           : ev_hyb["rouge1"],
                "hyb_rouge2"           : ev_hyb["rouge2"],
                "hyb_rougeL"           : ev_hyb["rougeL"],
                "hyb_kw_match"         : ev_hyb["kw_match"],
                "hyb_kw_content_match" : ev_hyb["kw_content_match"],
                # ── ベースライン（vs 参照要約）[改善 2] ────
                "gen_bert_f1"          : ev_gen["bert_f1"],
                "gen_rouge1"           : ev_gen["rouge1"],
                "gen_rouge2"           : ev_gen["rouge2"],
                "gen_rougeL"           : ev_gen["rougeL"],
                "gen_kw_match"         : ev_gen["kw_match"],
                "gen_kw_content_match" : ev_gen["kw_content_match"],
                "gen_bart_tokens"      : gen_tok,
                "gen_bart_truncated"   : int(gen_trunc),
                # ── 生成長制御情報 [改善 B] ────────────
                "gen_length_basis"     : "extracted" if GEN_LENGTH_FROM_EXTRACTED else "original",
            }

            if ROUGE_MORPHEME and "rouge1_morph" in ev_hyb:
                row_data["hyb_rouge1_morph"] = ev_hyb["rouge1_morph"]
                row_data["hyb_rouge2_morph"] = ev_hyb["rouge2_morph"]
                row_data["hyb_rougeL_morph"] = ev_hyb["rougeL_morph"]
            if ROUGE_MORPHEME and "rouge1_morph" in ev_gen:
                row_data["gen_rouge1_morph"] = ev_gen["rouge1_morph"]
                row_data["gen_rouge2_morph"] = ev_gen["rouge2_morph"]
                row_data["gen_rougeL_morph"] = ev_gen["rougeL_morph"]

            rows.append(row_data)

    # ── CSV 保存 & サマリ表示 ────────────────────
    ts          = datetime.now().strftime("%Y%m%d_%H%M%S")
    path_detail = _save_csv_detail(rows, ts, seed)
    path_agg    = _save_csv_aggregate(rows, ts, seed)
    if baseline_rows:
        _save_csv_baselines(baseline_rows, ts, seed)
    if sensitivity_rows:
        _save_csv_sensitivity(sensitivity_rows, ts, seed)

    _print_best(rows, n_texts)

    print(f"\n[DONE] 詳細 CSV : {path_detail}")
    print(f"[DONE] 集計 CSV : {path_agg}")
    print(
        f"[DONE] BART 上限超過 : "
        f"{sum(r['bart_truncated'] for r in rows)} / {len(rows)} 件"
    )


# ─────────────────────────────────────────────
# 10. 詳細 CSV 保存（1 行 = 1 テキスト × 1 抽出率）
# ─────────────────────────────────────────────

def _save_csv_detail(rows: List[Dict], ts: str, seed: int = 42) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"hybrid_detail_{ts}_seed{seed}.csv")

    fields = [
        "text_idx", "seed", "ext_ratio_pct",
        "orig_chars", "ref_chars", "ext_chars", "hyb_chars", "hyb_ratio",
        "bart_input_tokens", "bart_truncated",
        "hyb_bert_f1", "hyb_rouge1", "hyb_rouge2", "hyb_rougeL", "hyb_kw_match", "hyb_kw_content_match",
        "gen_bert_f1", "gen_rouge1", "gen_rouge2", "gen_rougeL", "gen_kw_match", "gen_kw_content_match",
        "gen_bart_tokens", "gen_bart_truncated",
        "gen_length_basis",
    ]
    if rows and "hyb_rouge1_morph" in rows[0]:
        fields.extend([
            "hyb_rouge1_morph", "hyb_rouge2_morph", "hyb_rougeL_morph",
            "gen_rouge1_morph", "gen_rouge2_morph", "gen_rougeL_morph",
        ])
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)
    return path


def _save_csv_baselines(rows: List[Dict], ts: str, seed: int = 42) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"baselines_detail_{ts}_seed{seed}.csv")
    fields = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return path


def _save_csv_sensitivity(rows: List[Dict], ts: str, seed: int = 42) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"sensitivity_detail_{ts}_seed{seed}.csv")
    fields = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return path


_HYB_METRICS = ["hyb_bert_f1", "hyb_rouge1", "hyb_rouge2", "hyb_rougeL", "hyb_kw_match", "hyb_kw_content_match"]
_GEN_METRICS = ["gen_bert_f1", "gen_rouge1", "gen_rouge2", "gen_rougeL", "gen_kw_match", "gen_kw_content_match"]


def _save_csv_aggregate(rows: List[Dict], ts: str, seed: int = 42) -> str:
    """
    抽出率ごとに全テキストの平均・標準偏差を集計して保存。
    ベースライン（生成型のみ）の平均も各行に含める。
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"hybrid_aggregate_{ts}_seed{seed}.csv")

    # ベースライン: テキストごとに 1 値（抽出率に依存しない）
    gen_vals_by_text: Dict[int, Dict[str, float]] = {}
    for row in rows:
        tid = row["text_idx"]
        if tid not in gen_vals_by_text:
            gen_vals_by_text[tid] = {m: row[m] for m in _GEN_METRICS}

    gen_means = {
        m: round(statistics.mean(v[m] for v in gen_vals_by_text.values()), 4)
        for m in _GEN_METRICS
    }

    # 抽出率ごとに集計
    agg_rows = []
    for pct in range(1, 101):
        subset = [r for r in rows if r["ext_ratio_pct"] == pct]
        if not subset:
            continue

        agg: Dict = {"ext_ratio_pct": pct, "n_texts": len(subset)}

        for m in _HYB_METRICS:
            vals = [r[m] for r in subset]
            agg[f"{m}_mean"] = round(statistics.mean(vals), 4)
            agg[f"{m}_std"]  = (
                round(statistics.stdev(vals), 4) if len(vals) > 1 else 0.0
            )

        # ベースライン平均（参照用・抽出率によらず同一）
        for m in _GEN_METRICS:
            agg[f"{m}_mean"] = gen_means[m]

        # BART 上限超過率・平均トークン数
        agg["truncation_rate"] = round(
            sum(r["bart_truncated"] for r in subset) / len(subset), 3
        )
        agg["avg_bart_tokens"] = round(
            statistics.mean(r["bart_input_tokens"] for r in subset), 1
        )

        agg_rows.append(agg)

    fields = (
        ["ext_ratio_pct", "n_texts"]
        + [f"{m}_{s}" for m in _HYB_METRICS for s in ["mean", "std"]]
        + [f"{m}_mean" for m in _GEN_METRICS]
        + ["truncation_rate", "avg_bart_tokens"]
    )

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(agg_rows)
    return path


# ─────────────────────────────────────────────
# 12. ベスト比率サマリ表示
# ─────────────────────────────────────────────

def _print_best(rows: List[Dict], n_texts: int) -> None:
    bar = "=" * 65
    print(f"\n{bar}")
    print("★ テキスト別ベスト抽出比率（BERTScore F1 最大）")
    print(bar)
    for t in range(1, n_texts + 1):
        sub  = [r for r in rows if r["text_idx"] == t]
        best = max(sub, key=lambda r: r["hyb_bert_f1"])
        gen  = sub[0]["gen_bert_f1"]
        diff = best["hyb_bert_f1"] - gen
        sign = "+" if diff >= 0 else ""
        print(
            f"  Txt{t:>2}: 最適抽出 {best['ext_ratio_pct']:>2}%"
            f"  Hyb F1={best['hyb_bert_f1']:.4f}"
            f"  R1={best['hyb_rouge1']:.4f}"
            f"  R2={best['hyb_rouge2']:.4f}"
            f"  KW={best['hyb_kw_match']:.4f}"
            f"  (vs Base {sign}{diff:.4f})"
        )

    print(f"\n{'─' * 65}")
    print("★ 全テキスト平均（抽出率別）上位 5")
    print(f"{'─' * 65}")

    avg_by_pct = {}
    for pct in range(1, 101):
        subset = [r for r in rows if r["ext_ratio_pct"] == pct]
        if subset:
            avg_by_pct[pct] = statistics.mean(r["hyb_bert_f1"] for r in subset)

    top5 = sorted(avg_by_pct.items(), key=lambda x: x[1], reverse=True)[:5]
    for rank, (pct, score) in enumerate(top5, 1):
        vals = [r["hyb_bert_f1"] for r in rows if r["ext_ratio_pct"] == pct]
        std  = statistics.stdev(vals) if len(vals) > 1 else 0.0
        print(f"  #{rank}  抽出 {pct:>2}%  平均 F1={score:.4f}  ± {std:.4f}")

    print(bar)


# ─────────────────────────────────────────────
# 13. エントリポイント
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # [改善 I] 複数シードでの再現性確認に対応
    for seed_idx, seed in enumerate(RANDOM_SEEDS):
        if len(RANDOM_SEEDS) > 1:
            print(f"\n{'#' * 60}")
            print(f"# シード {seed_idx + 1}/{len(RANDOM_SEEDS)}: seed={seed}")
            print(f"{'#' * 60}")

        # [Step 1] XL-Sum から参照要約付きテキストを取得
        data = load_xlsum_japanese(seed=seed)

        # [Step 2] 実験実行
        run_experiment(data, EXTRACTIVE_RATIOS, seed=seed)