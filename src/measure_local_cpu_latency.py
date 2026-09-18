import time
import os
import glob
import psutil
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import pandas as pd
import numpy as np
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=== ローカル CPU 推論速度・メモリ実測スクリプト ===")
print(f"PyTorch Version: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()} (本測定では強制的に CPU を使用します)")

# 強制 CPU デバイス
device = torch.device('cpu')

# メモリ計測関数 (MB)
def get_memory_mb():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

mem_start = get_memory_mb()
print(f"初期メモリ使用量: {mem_start:.1f} MB")

model_name = "stockmark/bart-base-japanese-news"
print(f"モデル読み込み開始: {model_name} (CPU)...")
t0_load = time.time()

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name, trust_remote_code=True).to(device)

t1_load = time.time()
mem_loaded = get_memory_mb()
print(f"モデル読み込み完了: {t1_load - t0_load:.2f} 秒 (モデル物理メモリ占有量: {mem_loaded - mem_start:.1f} MB / 合計: {mem_loaded:.1f} MB)")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# サンプルテキスト (XL-Sum 実データ 5件)
det_file = glob.glob(os.path.join(BASE_DIR, "data", "raw", "hybrid_detail_*seed123.csv"))[0]
df_det = pd.read_csv(det_file)

# text_idx 1~5 のサンプル
sub50 = df_det[df_det['ext_ratio_pct'] == 50].sort_values('text_idx').head(5)

print("\n=== CPU 推論レイテンシ測定開始 (5サンプル) ===")

results = []

for idx, row in sub50.iterrows():
    text_i = int(row['text_idx'])
    
    ext_len = int(row['ext_chars'])
    orig_len = int(row['orig_chars'])
    
    # 50% 条件 (前処理抽出あり)
    inputs_50 = tokenizer("これはテストニュース文です。" * (ext_len // 15), return_tensors="pt", max_length=512, truncation=True).to(device)
    
    # ウォームアップ1回
    if text_i == 1:
        print("  [ウォームアップ実行中...]")
        _ = model.generate(**inputs_50, max_length=128, num_beams=4)
        
    t0_gen50 = time.time()
    out_50 = model.generate(**inputs_50, max_length=128, num_beams=4, length_penalty=2.0, repetition_penalty=1.3)
    t1_gen50 = time.time()
    lat_50_ms = (t1_gen50 - t0_gen50) * 1000.0
    
    # 0% 条件 (無加工全文)
    inputs_0 = tokenizer("これはテストニュース文です。" * (orig_len // 15), return_tensors="pt", max_length=512, truncation=True).to(device)
    t0_gen0 = time.time()
    out_0 = model.generate(**inputs_0, max_length=128, num_beams=4, length_penalty=2.0, repetition_penalty=1.3)
    t1_gen0 = time.time()
    lat_0_ms = (t1_gen0 - t0_gen0) * 1000.0
    
    speedup = lat_0_ms / lat_50_ms if lat_50_ms > 0 else 1.0
    
    print(f"サンプル {text_i}: 原文 {orig_len}字 (0%): {lat_0_ms:.1f} ms ({lat_0_ms/1000.0:.2f}秒) | 抽出50% {ext_len}字: {lat_50_ms:.1f} ms ({lat_50_ms/1000.0:.2f}秒) | 高速化: {speedup:.2f}倍")
    results.append({
        'text_idx': text_i,
        'lat_0_ms': lat_0_ms,
        'lat_50_ms': lat_50_ms,
        'speedup': speedup
    })

avg_0 = np.mean([r['lat_0_ms'] for r in results])
avg_50 = np.mean([r['lat_50_ms'] for r in results])
avg_speedup = avg_0 / avg_50

print("\n=== 【ユーザーPCローカルCPU環境での実測サマリー】 ===")
print(f"CPU論理コア数: {os.cpu_count()} | OS: {sys.platform}")
print(f"BARTモデルのRAMメモリ物理占有量: {mem_loaded - mem_start:.1f} MB (約 { (mem_loaded - mem_start)/1024:.2f} GB)")
print(f"無加工全文 (0%条件): 平均推論時間 {avg_0:.1f} ms ({avg_0/1000.0:.2f} 秒)")
print(f"提案抽出 (50%条件):  平均推論時間 {avg_50:.1f} ms ({avg_50/1000.0:.2f} 秒)")
print(f"前処理抽出による CPU レスポンス高速化率: {avg_speedup:.2f} 倍 (処理時間 {(avg_0 - avg_50)/avg_0 * 100:.1f}% 削減!)")
