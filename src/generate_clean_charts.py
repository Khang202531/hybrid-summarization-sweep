import os
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import csv

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'Meiryo', 'MS Gothic', 'TakaoPGothic', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 300

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data", "aggregate")
FIG_DIR = os.path.join(BASE_DIR, "figures")

def plot_fig1():
    path = os.path.join(DATA_DIR, "hybrid_aggregate_20260805_192028_seed42.csv")
    ratios = []
    r1_means = []
    bert_means = []
    
    with open(path, encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            ratios.append(int(r['ext_ratio_pct']))
            r1_means.append(float(r['hyb_rouge1_mean']))
            bert_means.append(float(r['hyb_bert_f1_mean']))
            
    fig, ax1 = plt.subplots(figsize=(6.5, 3.8))
    
    color_r1 = '#1f77b4'
    ax1.set_xlabel('抽出率 (%)', fontsize=10, fontweight='bold')
    ax1.set_ylabel('ROUGE-1 (単語一致度)', color=color_r1, fontsize=10, fontweight='bold')
    line1 = ax1.plot(ratios, r1_means, color=color_r1, lw=2, label='ROUGE-1')
    ax1.tick_params(axis='y', labelcolor=color_r1)
    ax1.set_ylim(0.15, 0.40)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    peak_idx = np.argmax(r1_means)
    ax1.scatter([ratios[peak_idx]], [r1_means[peak_idx]], color='#d62728', s=45, zorder=5)
    ax1.annotate(f'最高値 ({ratios[peak_idx]}%, {r1_means[peak_idx]:.4f})',
                 xy=(ratios[peak_idx], r1_means[peak_idx]),
                 xytext=(ratios[peak_idx]+5, r1_means[peak_idx]+0.015),
                 arrowprops=dict(facecolor='#d62728', shrink=0.08, width=1, headwidth=4),
                 fontsize=8.5, color='#d62728', fontweight='bold')
    
    ax2 = ax1.twinx()
    color_bert = '#2ca02c'
    ax2.set_ylabel('BERTScore F1 (意味類似度)', color=color_bert, fontsize=10, fontweight='bold')
    line2 = ax2.plot(ratios, bert_means, color=color_bert, lw=2, linestyle='--', label='BERTScore F1')
    ax2.tick_params(axis='y', labelcolor=color_bert)
    ax2.set_ylim(0.60, 0.75)
    
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='lower right', fontsize=8.5)
    
    plt.title('予備実験：抽出率スイープと要約スコアの推移 (n=30)', fontsize=10.5, fontweight='bold', pad=10)
    plt.tight_layout()
    fig1_path = os.path.join(FIG_DIR, 'fig1.png')
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print("Saved fig1.png")

def plot_fig2():
    conditions = ['0%\n(生成のみ)', '25%\n(低抽出)', '50%\n(中間)', '75%\n(高抽出)', '100%\n(全文)']
    r1_means = [0.2214, 0.3351, 0.3460, 0.2925, 0.2273]
    r1_sds = [0.0514, 0.0827, 0.0748, 0.0645, 0.0570]
    bert_means = [0.6718, 0.6707, 0.6782, 0.6765, 0.6752]
    bert_sds = [0.0258, 0.0354, 0.0243, 0.0271, 0.0216]
    
    x = np.arange(len(conditions))
    width = 0.35
    
    fig, ax1 = plt.subplots(figsize=(6.5, 3.8))
    
    rects1 = ax1.bar(x - width/2, r1_means, width, yerr=r1_sds, capsize=4,
                     label='ROUGE-1 (単語一致度)', color='#336699', edgecolor='black', linewidth=0.5)
    
    rects1[2].set_color('#1b365d')
    rects1[2].set_edgecolor('black')
    
    ax1.set_ylabel('ROUGE-1', color='#1b365d', fontsize=9.5, fontweight='bold')
    ax1.set_ylim(0, 0.45)
    ax1.set_xticks(x)
    ax1.set_xticklabels(conditions, fontsize=8.5)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    
    for rect in rects1:
        height = rect.get_height()
        ax1.annotate(f'{height:.3f}',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 10),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=7.5, fontweight='bold')
        
    ax2 = ax1.twinx()
    rects2 = ax2.bar(x + width/2, bert_means, width, yerr=bert_sds, capsize=4,
                     label='BERTScore F1 (意味類似度)', color='#88b04b', edgecolor='black', linewidth=0.5)
    ax2.set_ylabel('BERTScore F1', color='#4f6d2f', fontsize=9.5, fontweight='bold')
    ax2.set_ylim(0.50, 0.75)
    
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=8)
    
    plt.title('本実験：代表5条件における要約スコア比較 (n=30)', fontsize=10.5, fontweight='bold', pad=10)
    plt.tight_layout()
    fig2_path = os.path.join(FIG_DIR, 'fig2.png')
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print("Saved fig2.png")

def plot_fig3():
    methods = [
        'Base 1\n生成のみ',
        'Base 2\n純粋抽出型',
        'Base 3\nLead-3+生成',
        'Base 4\nランダム+生成',
        '提案手法\n(50%+生成)'
    ]
    r1_scores = [0.2214, 0.2974, 0.3283, 0.3143, 0.3460]
    r1_errors = [0.0514, 0.0645, 0.0667, 0.0654, 0.0748]
    colors = ['#8faadc', '#8faadc', '#8faadc', '#8faadc', '#1b365d']
    
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    
    bars = ax.bar(methods, r1_scores, yerr=r1_errors, capsize=4.5, color=colors, edgecolor='black', linewidth=0.6, width=0.55)
    
    ax.set_ylabel('ROUGE-1 (単語一致度)', fontsize=10, fontweight='bold')
    ax.set_ylim(0, 0.48)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.tick_params(axis='x', labelsize=8.5)
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f'{height:.4f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 8),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8, fontweight='bold')
        
    # 有意差ブラケット 1: 提案手法 vs Base 1 (*** p < 0.001)
    ax.plot([0, 0, 4, 4], [0.38, 0.44, 0.44, 0.425], lw=1.1, c='#333333')
    ax.text(2.0, 0.445, '*** (vs Base 1, p < 0.001)', ha='center', va='bottom', fontsize=8, fontweight='bold', color='#111111')

    # 有意差ブラケット 2: 提案手法 vs Base 2 (*** p < 0.001)
    ax.plot([1, 1, 3.85, 3.85], [0.365, 0.405, 0.405, 0.42], lw=0.9, c='#555555', linestyle='--')
    ax.text(2.4, 0.41, '*** (vs Base 2)', ha='center', va='bottom', fontsize=7.5, color='#333333')

    # 有意差ブラケット 3: 提案手法 vs Base 4 (* p = 0.0168 < 0.05, Bonferroni補正後)
    ax.plot([3, 3, 4.15, 4.15], [0.385, 0.39, 0.39, 0.42], lw=0.9, c='#555555', linestyle=':')
    ax.text(3.6, 0.392, '* (vs Base 4)', ha='center', va='bottom', fontsize=7.5, color='#333333')
    
    plt.title('ベースライン手法と提案ハイブリッド手法(50%)の性能比較 (n=30)', fontsize=10.5, fontweight='bold', pad=10)
    plt.tight_layout()
    fig3_path = os.path.join(FIG_DIR, 'fig3.png')
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print("Saved fig3.png with multiple significance annotations.")

if __name__ == '__main__':
    plot_fig1()
    plot_fig2()
    plot_fig3()
