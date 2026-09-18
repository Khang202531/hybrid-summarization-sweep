# 抽出率スイープを用いたハイブリッド自動要約における抽出率の最適化と情報圧縮効果に関する研究

> **二段階実験デザイン（探索的スイープ＆確認的本実験）によるローカル言語モデル要約品質の最適化と統計的検証**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 研究概要

クラウドの大規模言語モデル（LLM）が利用困難な制約環境（個人情報保護、災害時オフライン、車載・端末組込のリアルタイム処理、APIランニングコストゼロ要求など）において、ローカルで稼働する軽量事前学習済みモデル（BART）の実用化が求められています。

本研究では、全文を直接入力する従来手法（0%条件）に対し、安価な前処理抽出（**TF-IDF + MMR (Maximal Marginal Relevance)**）を施してから生成モデルに投入する**ハイブリッド要約手法**を提案します。

さらに、事後的な最大値選択によるバイアス（第一種の過誤率の増大）を排するため、以下の**二段階実験デザイン**を構築して厳密な統計的検証を行いました：
1. **第1段階：探索的予備実験（n=30, 1%〜100% 連続スイープ）**
   - 抽出率と要約スコアの関係性を記述統計で把握し、有望領域を同定
2. **第2段階：確認的本実験（独立サンプル n=30, 5条件事前設定）**
   - 反復測定一元配置分散分析（RM-ANOVA）および Dunnett の多重比較検定を実施
   - 4つの対照ベースライン（生成のみ、純粋抽出、Lead-3+生成、ランダム抽出+生成）との多角的な対照検証

---

## 📊 主要な実験結果

### 1. 予備実験：抽出率スイープ推移 (n=30)
抽出率を1%〜100%まで変化させたときの評価スコアの推移です。意味的類似度（BERTScore F1）は抽出率によらずほぼ一定（約0.67〜0.68）ですが、単語一致度（ROUGE-1）は **抽出率 40%〜50% 付近でピーク（最高 0.3608）** を迎える山型特性を示しました。

<p align="center">
  <img src="figures/fig1.png" alt="予備実験スイープ推移" width="650">
</p>

### 2. 確認的本実験：代表5条件の比較 (独立サンプル n=30)
独立した30サンプルによる確認実験において、**抽出率50%条件**が無加工全文入力（0%条件）に対して ROUGE-1 を大幅に向上させました（$p < 0.001$, Cohen's $d = 2.17$）。

<p align="center">
  <img src="figures/fig2.png" alt="代表5条件比較" width="650">
</p>

### 3. ベースライン比較
4つの対照ベースラインとの比較により、提案手法（50%抽出 + 生成）は生成のみ（Base 1）、純粋抽出型（Base 2）、ランダム抽出+生成（Base 4）に対して有意な語彙一致度の向上を示しました。

<p align="center">
  <img src="figures/fig3.png" alt="ベースライン比較" width="650">
</p>

---

## 📁 ディレクトリ構成

```text
.
├── .gitignore                         # Git除外設定（キャッシュ・一時ファイル・ローカル退避等）
├── README.md                          # 本ドキュメント
├── requirements.txt                   # 依存ライブラリ一覧
│
├── src/                               # 実行スクリプト
│   ├── experiment_pipeline.py         # メイン実験パイプライン（XL-Sum取得・要約生成・評価）
│   ├── analysis.py                    # 統計解析（RM-ANOVA, Dunnett検定, 感度分析, 相関）
│   ├── generate_clean_charts.py       # 論文・README用グラフ描画 (fig1〜3)
│   ├── eval_llm_reference.py          # クラウドLLM（GPT-5/Gemini級）の参照スコア算出
│   ├── measure_local_cpu_latency.py   # ローカルCPU環境での推論速度・メモリ実測
│   └── build_paper_docx.py            # 論文Word文書（docx）の自動組版・生成
│
├── data/                              # 実験結果データ
│   ├── aggregate/                     # 集約データ・ベースライン・MMR感度分析CSV
│   │   ├── hybrid_aggregate_*.csv
│   │   ├── baselines_detail_*.csv
│   │   └── sensitivity_detail_*.csv
│   ├── raw/                           # 全文・抽出率別の詳細評価CSV
│   │   └── hybrid_detail_*.csv
│   ├── llm_reference_results.json     # クラウドLLM参照ベンチマーク
│   └── analysis_result.txt            # 統計解析レポート全文
│
└── figures/                           # 評価グラフ画像
    ├── fig1.png                       # スイープ推移グラフ
    ├── fig2.png                       # 代表5条件棒グラフ
    └── fig3.png                       # 4ベースライン比較棒グラフ

          

```

---

## 🚀 環境構築と再現手順

### 1. 依存ライブラリのインストール
```bash
pip install -r requirements.txt
```

### 2. 統計解析の実行
既存の実験CSVデータ群（`data/` 配下）を読み込み、RM-ANOVA、Dunnett多重比較検定、ベースライン比較、感度分析、長さ交絡の検証を一括実行します。
```bash
python src/analysis.py
```
実行結果はコンソールに表示されるとともに、`data/analysis_result.txt` に出力されます。

### 3. グラフ・図表の再生成
論文および本READMEで使用している図1〜3を再生成します。
```bash
python src/generate_clean_charts.py
```
生成された画像は `figures/` ディレクトリに高解像度（300 dpi）で保存されます。

### 4. 論文Word文書（docx）の生成
整形済みの提出用論文（2段組学術論文フォーマット）を生成します。
```bash
python src/build_paper_docx.py
```
生成結果は `docs/paper_final.docx` に保存されます。

### 5. 実験パイプラインの再実行（オプション・GPU環境推奨）
XL-Sum Japanese データセットから記事を取得し、抽出率スイープ実験を新規に実行する場合：
```bash
python src/experiment_pipeline.py
```
※Google Colaboratory（T4 GPU等）での実行を推奨します。

---

## 🔬 実装技術と使用モデル

- **要約生成モデル**: `stockmark/bart-base-japanese-news`（事前学習済み軽量BART日本語モデル）
- **形態素解析**: `fugashi` + `unidic-lite`
- **抽出アルゴリズム**: TF-IDF (文字 n-gram / 単語) + MMR (ダイバーシティ制御)
- **評価指標**:
  - 表層語彙一致度: ROUGE-1 / ROUGE-2 / ROUGE-L
  - 意味的類似度: BERTScore F1 (`cl-tohoku/bert-base-japanese-v2`)
  - キーワード内容語保持率: fugashi 名詞・動詞・形容詞抽出
- **統計検定**: Mauchly球面性検定, 反復測定一元配置分散分析（RM-ANOVA, Greenhouse-Geisser補正）, Dunnett検定, Bonferroni補正
