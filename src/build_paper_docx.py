import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=60, bottom=60, left=60, right=60):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="CCCCCC", sz="4"):
    tblPr = table._element.xpath('w:tblPr')
    if tblPr:
        borders = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>'
            f'  <w:top w:val="single" w:sz="8" w:space="0" w:color="333333"/>'
            f'  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="333333"/>'
            f'  <w:left w:val="none"/>'
            f'  <w:right w:val="none"/>'
            f'  <w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
            f'  <w:insideV w:val="none"/>'
            f'</w:tblBorders>'
        )
        tblPr[0].append(borders)

def set_col_widths(table, widths):
    for row in table.rows:
        for i, w in enumerate(widths):
            row.cells[i].width = Inches(w)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def create_perfect_submission_paper():
    template_path = os.path.join(BASE_DIR, 'archive', 'duplicate_docx', '創造理数科_理数探究論文テンプレート_2026年度版_確定.docx')
    if not os.path.exists(template_path):
        template_path = '創造理数科_理数探究論文テンプレート_2026年度版_確定.docx'
    doc = Document(template_path)

    # ========================================================
    # Section 0: ヘッダー（1段組）の差し替え
    # ========================================================
    # P0: 和文タイトル (ＭＳ ゴシック 12pt・太字・中央揃え)
    p0 = doc.paragraphs[0]
    p0.text = ""
    p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r0 = p0.add_run("抽出率スイープを用いたハイブリッド自動要約における\n抽出率の最適化と情報圧縮効果に関する研究")
    r0.bold = True
    r0.font.name = 'ＭＳ ゴシック'
    r0._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ ゴシック" w:hAnsi="ＭＳ ゴシック" w:eastAsia="ＭＳ ゴシック"/>'))
    r0.font.size = Pt(12)

    # P1: 英文タイトル (Times New Roman 12pt・中央揃え)
    p1 = doc.paragraphs[1]
    p1.text = ""
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r1 = p1.add_run("Optimization of Extraction Rate and Information Compression in Hybrid Text Summarization via Rate Sweeping")
    r1.bold = False
    r1.font.name = 'Times New Roman'
    r1._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/>'))
    r1.font.size = Pt(12)

    # P3: 和文著者名 (ＭＳ 明朝 10.5pt・中央揃え)
    p3 = doc.paragraphs[3]
    p3.text = ""
    p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = p3.add_run("浜田　賢一*1")
    r3.font.name = 'ＭＳ 明朝'
    r3._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ 明朝" w:hAnsi="ＭＳ 明朝" w:eastAsia="ＭＳ 明朝"/>'))
    r3.font.size = Pt(10.5)

    # P4: 英文著者名 (Times New Roman 10.5pt・中央揃え)
    p4 = doc.paragraphs[4]
    p4.text = ""
    p4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r4 = p4.add_run("Kenichi HAMADA*1")
    r4.font.name = 'Times New Roman'
    r4._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/>'))
    r4.font.size = Pt(10.5)

    # P5: 和文所属 (ＭＳ 明朝 10.0pt・中央揃え)
    p5 = doc.paragraphs[5]
    p5.text = ""
    p5.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r5 = p5.add_run("*1 東京都立科学技術高等学校 創造理数科 3年")
    r5.font.name = 'ＭＳ 明朝'
    r5._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ 明朝" w:hAnsi="ＭＳ 明朝" w:eastAsia="ＭＳ 明朝"/>'))
    r5.font.size = Pt(10.0)

    # P6: 英文所属 (Times New Roman 9.0pt・中央揃え)
    p6 = doc.paragraphs[6]
    p6.text = ""
    p6.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r6 = p6.add_run("*1 Dept. of Creative Science and Mathematics, Tokyo Metropolitan High School of Science and Technology")
    r6.font.name = 'Times New Roman'
    r6._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/>'))
    r6.font.size = Pt(9.0)

    # P8: 要旨見出し (ＭＳ ゴシック 10.5pt, bold=False テンプレート原本完全準拠)
    p8 = doc.paragraphs[8]
    p8.text = ""
    r8 = p8.add_run("要旨")
    r8.font.name = 'ＭＳ ゴシック'
    r8._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ ゴシック" w:hAnsi="ＭＳ ゴシック" w:eastAsia="ＭＳ ゴシック"/>'))
    r8.font.size = Pt(10.5)
    r8.bold = False

    # P9: 要旨本文 (ＭＳ 明朝 10.0pt, 1字下げ 127000 dxa, 400字程度, 全角「，」「．」統一)
    p9 = doc.paragraphs[9]
    p9.text = ""
    p9.paragraph_format.first_line_indent = Pt(10.0)
    p9.paragraph_format.line_spacing = 1.25
    r9 = p9.add_run(
        "自然言語処理における自動要約では，原文から重要文を選出する「抽出型要約」と，文を新たに生成する「生成型要約」を組み合わせたハイブリッド手法が有効とされる．しかし，最初の抽出段階で原文からどの程度の文量（抽出率）を残して生成モデルに入力すべきかという点は体系的に評価されていない．本研究では，日本語ニュース記事（XL-Sumデータセット）を対象に，抽出率を1%から100%まで変化させて要約品質への影響を実験的に検証した．予備実験による最適領域の探索を経て，独立したデータセット（30件）を用いた本実験を行った結果，抽出率50%条件で単語一致度（ROUGE-1）が0.3460を記録し，全文を直接入力したベースライン（0.2214）に比べて大幅に向上することを確認した（p < 0.001）．一方，意味の類似度（BERTScore）は条件間で有意差がなく横ばいであった．このことから，抽出前処理の主たる効果は冗長な情報の削ぎ落としによる語彙の凝縮にあることが分かった．また，Lead-3手法等との比較を通じ，本手法の情報圧縮効果と実用的な意義を考察した．"
    )
    r9.font.name = 'ＭＳ 明朝'
    r9._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ 明朝" w:hAnsi="ＭＳ 明朝" w:eastAsia="ＭＳ 明朝"/>'))
    r9.font.size = Pt(10.0)

    # P10: キーワード (ＭＳ 明朝 10.0pt, 6語・8語以内)
    p10 = doc.paragraphs[10]
    p10.text = ""
    p10.paragraph_format.first_line_indent = None
    r10 = p10.add_run("キーワード：自動要約，ハイブリッド要約，抽出率，言語モデル，情報圧縮，ROUGE")
    r10.font.name = 'ＭＳ 明朝'
    r10._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ 明朝" w:hAnsi="ＭＳ 明朝" w:eastAsia="ＭＳ 明朝"/>'))
    r10.font.size = Pt(10.0)

    # ========================================================
    # Section 1: 本文領域（2段組）の構築
    # ========================================================
    for t in list(doc.tables):
        t._element.getparent().remove(t._element)

    for p in list(doc.paragraphs)[12:]:
        p._element.getparent().remove(p._element)

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.first_line_indent = None
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.name = 'ＭＳ ゴシック'
        r._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ ゴシック" w:hAnsi="ＭＳ ゴシック" w:eastAsia="ＭＳ ゴシック"/>'))
        r.font.size = Pt(10.5)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.first_line_indent = None
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = True
        r.font.name = 'ＭＳ ゴシック'
        r._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ ゴシック" w:hAnsi="ＭＳ ゴシック" w:eastAsia="ＭＳ ゴシック"/>'))
        r.font.size = Pt(10.0)
        return p

    def add_body(text, indent=True):
        p = doc.add_paragraph()
        if indent:
            p.paragraph_format.first_line_indent = Pt(10.0)
        else:
            p.paragraph_format.first_line_indent = None
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.line_spacing = 1.2
        r = p.add_run(text)
        r.font.name = 'ＭＳ 明朝'
        r._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="ＭＳ 明朝"/>'))
        r.font.size = Pt(10.0)
        return p

    def add_caption(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.first_line_indent = None
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        r.bold = False
        r.font.name = 'ＭＳ ゴシック'
        r._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ ゴシック" w:hAnsi="ＭＳ ゴシック" w:eastAsia="ＭＳ ゴシック"/>'))
        r.font.size = Pt(9.0)
        return p

    # I. 背景・目的
    add_h1("I．背景・目的")
    add_body(
        "高校の探究活動の中で自然言語処理に興味を持ち，ニュース記事の自動要約を試した際，ある問題に直面した．長いニュース記事をそのまま既存の言語モデル（BART）に入力して要約させると，記事の前半ばかりに偏った要約が出力されたり，記事の後半にある重要な結論がすっぽりと抜け落ちてしまったりしたのである．"
    )
    add_body(
        "原因を調べたところ，使用したモデル（BART-base）には一度に入力できる文章の長さに「最大512トークン」という制限があり，長文記事を入力すると末尾が途中で切り捨てられてしまうことが分かった．また，切り捨てが発生しない程度の長さであっても，文章中に含まれる細かい背景説明や修飾語にモデルが引っ張られ，要約全体の焦点がぼやけてしまう傾向が見られた．"
    )
    add_body(
        "自動文章要約の手法には，元の文章から重要文をそのまま抜き出す「抽出型要約」と，ニューラルネットワークで自然な文章を書き直す「生成型要約」の二つがある（Rennard et al., 2023）．抽出型は事実を正確に残せるが文のつながりが不自然になりやすく，生成型は滑らかな文章を作れるが長文の処理に課題がある．そこで，まず抽出型の手法で重要な文を大まかに絞り込み，その文を生成モデルに入力して自然な文章にまとめる「ハイブリッド要約」というアプローチに着目した（Ishikawa et al., 2001）．"
    )
    add_body(
        "しかし，ここで一つの疑問が生じた．「最初の抽出段階で，元の文章から何パーセント程度の文量を残して生成モデルに渡すのが最も良い要約になるのか」という点である．抽出する文が少なすぎれば必要な情報が欠落して文脈が壊れてしまうし，逆に多すぎれば長文をそのまま入力するのと変わらず元の問題が再発するはずである．"
    )
    add_body(
        "そこで本研究では，抽出率（Extraction Rate）を1%から100%まで連続的に変化させながら要約品質を測定し，最も効果的な抽出率とそのメカニズムを実験的に明らかにすることを目的とした．"
    )

    # II. 方法
    add_h1("II．方法")
    add_h2("2.1 実験データと言語モデル")
    add_body(
        "実験データには，多言語要約ベンチマークとして標準的な「XL-Sum 日本語データセット」（Hasan et al., 2021）を使用した．本データセットの各記事には専門の編集者等によって人手で作成された高品質な「参照要約（正解要約）」が標準で付属しており，本研究における自動評価（ROUGEおよびBERTScore）の正解基準としてこの参照要約を用いた．本文の文字数が300〜1200字程度の記事から無作為に30件を抽出（再現性確保のため乱数シードを固定：予備実験 seed=42，本実験 seed=123）し，実験対象とした．要約を生成する言語モデルには，日本語ニュース記事で事前学習された「stockmark/bart-base-japanese-news」を採用し，Google Colab上のGPU（Tesla T4）環境でPythonを用いて実験プログラムを作成・実行した．"
    )

    add_h2("2.2 ハイブリッド要約の手順と計算式")
    add_body(
        "本研究で実装したハイブリッド要約プログラムは，以下の3つのステップで処理を行った．\n"
        "(1) 文の重要度計算：ニュース記事を文集合 {s_0, s_1, ..., s_{n-1}}（総文数 n）に分割し，各文の文字バイグラムTF-IDF値（Salton & Buckley, 1988）の総和を文長の平方根で正規化したスコア S_tfidf(s_k) を算出した．これにニュース特有の文頭重視傾向を反映する文位置ボーナス B_pos(k) = α · exp(-β · k / (n - 1)) + (γ if k = n-1 else 0)（本実験では文頭係数 α=0.15，減衰率 β=3.0，結論文を捉える末尾ボーナス γ=0.05）を加算し，各文の重要度スコア（Relevance）を R(s_k) = S_tfidf(s_k) + B_pos(k) として求めた．\n"
        "(2) 重要文の抽出：指定した抽出率（文数 round(n × ratio)）に達するまで，重要度が高く，かつ既選択文との内容重複が少ない文をMMR（Maximal Marginal Relevance, Carbonell & Goldstein, 1998）により逐次選出した．未選択文 s_i と既選択文集合 S に対するMMRスコアを MMR(s_i) = λ · R(s_i) - (1 - λ) · max_{s_j ∈ S} Sim_cos(s_i, s_j)（本実験では関連度と多様性のバランス係数 λ=0.70，類似度 Sim_cos は文字バイグラムTF-IDFベクトルのコサイン類似度）として計算した．\n"
        "(3) 要約文の生成：選ばれた文を元の文章の出現順（原文順）に並べ直してBARTに入力し，最大生成長を入力トークン数の約60%（GENERATIVE_RATIO = 0.60，min_new_tokens はその40%）に制御して，実測平均約190文字の要約文を生成させた．", indent=False
    )

    add_h2("2.3 予備実験から本実験への設計とベースラインの追加")
    add_body(
        "実験は段階的に進めた．まず予備実験として，抽出率を1%から100%まで1%刻み（全99条件）で変化させ，抽出率と要約スコアの関係の大まかな推移を観察した（探索用データセット，30件，seed=42）．"
    )
    add_body(
        "予備実験の結果，抽出率50%付近に明確なピークが観察されたが，「この30件だけで得られた結果が偶然ではないか」を確かめるため，新たに独立して抽出した別の30件の記事（検証用データセット，30件，seed=123）を用いて本実験を行った．本実験では，代表的な5つの条件（0% [前処理なしの全文直接入力]，25% [低抽出]，50% [中間]，75% [高抽出]，100% [抽出処理を通した全文]）を設定し，詳細な比較を行った．"
    )
    add_body(
        "さらに実験を進める中で，「抽出率50%が良いとして，それはTF-IDFによる文選択が効いているのか，それとも単に文章の長さを半分に減らしたこと自体が効いているだけなのか？」という疑問に突き当たった．また，「ニュース記事は冒頭に要点が集中しているため，単に最初の3文を抜き出すだけでも同じ結果になるのではないか？」という点も検証する必要があると考えた．そこで，以下の4つの比較対象（ベースライン）を設定した．\n"
        "・生成のみ（Base 1）：前処理を行わず，元の全文を直接BARTに入力して要約する（対照群）．\n"
        "・純粋抽出型（Base 2）：生成モデルを使わず，抽出した50%の文をそのまま要約とする．\n"
        "・Lead-3＋生成（Base 3）：ニュース記事の冒頭3文のみを抽出してBARTに入力する．\n"
        "・ランダム抽出＋生成（Base 4）：ランダムに選んだ50%の文（seed=123）をBARTに入力する．", indent=False
    )

    add_h2("2.4 評価指標")
    add_body(
        "生成された要約の評価には，XL-Sum付属の人手作成参照要約（ゴールドスタンダード）との比較により，以下の2つの指標を用いた．\n"
        "・ROUGE-1（F1値）：参照要約と生成要約の間で，単語（形態素）がどれくらい一致しているかを測る指標（Lin, 2004）．本研究では重要語句の網羅性を測る主指標とした．\n"
        "・BERTScore（F1値）：単語の完全一致だけでなく，事前学習モデルを用いて文全体の意味の近さを評価する指標（Zhang et al., 2020）．", indent=False
    )

    # III. 結果
    add_h1("III．結果")
    add_h2("3.1 予備実験：抽出率スイープによる推移")
    add_body(
        "予備実験において抽出率を1%から100%まで変化させたときのROUGE-1およびBERTScoreの平均値の推移を図1に示す（探索用データセット，n=30）．"
    )

    fig1_path = os.path.join(BASE_DIR, 'figures', 'fig1.png')
    if os.path.exists(fig1_path):
        p_img1 = doc.add_paragraph()
        p_img1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img1.paragraph_format.space_before = Pt(4)
        p_img1.paragraph_format.space_after = Pt(2)
        p_img1.paragraph_format.first_line_indent = None
        run_img1 = p_img1.add_run()
        run_img1.add_picture(fig1_path, width=Inches(3.3))
        add_caption("図1　予備実験における抽出率（1%〜100%）と評価スコアの推移（n=30）")

    add_body(
        "当初は「抽出率を上げるほど情報量が増えるため，意味の類似度（BERTScore）も右肩上がりに良くなるだろう」と予想していた．しかし実際に測定してみると，BERTScoreは抽出率を変えても約0.67〜0.68の間でほぼ横ばいに推移し，予想に反して大きな変化が見られなかった．"
    )
    add_body(
        "一方で，単語一致度（ROUGE-1）には極めて明瞭な変化が現れた．抽出率が10〜20%と極端に低い領域では情報不足によりスコアが低いものの，30%を超えると急上昇し，38〜50%付近で最高値（0.3608）に達した．その後，抽出率が70%を超えて100%に近づくにつれてスコアは再び低下した．これにより，抽出率30〜70%（特に40〜50%付近）が最も語彙一致度を高める有望な領域であることが分かった．"
    )

    add_h2("3.2 本実験：代表5条件の詳細比較")
    add_body(
        "予備実験で有望と判明した領域の再現性を確かめるため，独立して無作為抽出した別の30記事（検証用データセット，n=30）を用いて，代表的な5つの抽出率条件（0%, 25%, 50%, 75%, 100%）を測定した結果を図2および表1に示す．"
    )

    fig2_path = os.path.join(BASE_DIR, 'figures', 'fig2.png')
    if os.path.exists(fig2_path):
        p_img2 = doc.add_paragraph()
        p_img2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img2.paragraph_format.space_before = Pt(4)
        p_img2.paragraph_format.space_after = Pt(2)
        p_img2.paragraph_format.first_line_indent = None
        run_img2 = p_img2.add_run()
        run_img2.add_picture(fig2_path, width=Inches(3.3))
        add_caption("図2　本実験における代表5条件の要約スコア比較（n=30）")

    add_caption("表1　抽出率5条件における要約スコアの比較（平均値±標準偏差，n=30）")
    
    table1 = doc.add_table(rows=6, cols=4)
    table1.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table1, color="CCCCCC", sz="4")
    set_col_widths(table1, [0.85, 0.75, 0.75, 0.95])
    
    headers1 = ["抽出率条件", "ROUGE-1", "BERTScore", "対0%条件差 (t値, p値)"]
    t1_data = [
        ["0% (生成のみ)", "0.2214±0.0514", "0.6718±0.0258", "— (基準)"],
        ["25% (低抽出)", "0.3351±0.0827", "0.6707±0.0354", "+0.1137 (t=6.800, p<0.001)"],
        ["50% (中間)", "0.3460±0.0748", "0.6782±0.0243", "+0.1246 (t=11.882, p<0.001)"],
        ["75% (高抽出)", "0.2925±0.0645", "0.6765±0.0271", "+0.0711 (t=12.340, p<0.001)"],
        ["100% (全文)", "0.2273±0.0570", "0.6752±0.0216", "+0.0059 (t=1.879, p=0.070)"]
    ]

    for col_idx, text in enumerate(headers1):
        cell = table1.cell(0, col_idx)
        cell.text = text
        set_cell_background(cell, "EEEEEE")
        set_cell_margins(cell, top=40, bottom=40, left=40, right=40)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.bold = True
            r.font.name = 'ＭＳ ゴシック'
            r._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ ゴシック" w:hAnsi="ＭＳ ゴシック" w:eastAsia="ＭＳ ゴシック"/>'))
            r.font.size = Pt(8.0)

    for row_idx, row_vals in enumerate(t1_data):
        for col_idx, val in enumerate(row_vals):
            cell = table1.cell(row_idx + 1, col_idx)
            cell.text = val
            bg = "F9F9F9" if row_idx % 2 == 1 else "FFFFFF"
            if row_idx == 2:
                bg = "F0F4F8"
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=35, bottom=35, left=40, right=40)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.name = 'ＭＳ 明朝'
                r._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="ＭＳ 明朝"/>'))
                r.font.size = Pt(7.5)
                if row_idx == 2 and col_idx in [0, 1, 3]:
                    r.bold = True

    add_body(
        "表1の通り，独立した検証用データセットを用いた本実験においても，抽出率50%条件がROUGE-1で0.3460を記録し，全文直接入力（0%条件: 0.2214）に比べて+0.1246の大幅な改善を示した．対応のあるt検定を行ったところ，この差は統計的にも極めて有意であった（t(29) = 11.882, p < 0.001）．また，25%条件（0.3351, t(29)=6.800）や75%条件（0.2925, t(29)=12.340）でも0%条件を有意に上回っており（いずれも p < 0.001），事前に文を絞り込む前処理を行うこと自体が要約の語彙一致度を安定して底上げすることが確認できた．"
    )
    add_body(
        "なお，前処理を行わず全文を直接入力した0%条件（0.2214）と，抽出処理を経て全100%の文を原文順に再結合して入力した100%条件（0.2273）では，理論上はほぼ同一の入力テキストとなるものの，微小なスコア差（+0.0059, t(29)=1.879, p=0.070, 統計的有意差なし）が観測された．これは，文分割・再結合処理に伴う句読点や改行コードの整形，およびトークナイズ境界や512トークン制限による末尾切り捨て位置のわずかな変化に起因するものであり，両条件間に統計的な有意差は認められず，実装の一貫性が保たれていることを確認した．"
    )
    add_body(
        "また，表1において75%条件のROUGE改善差（+0.0711）は50%条件（+0.1246）よりも小さいが，t値（12.340）は50%条件（11.882）を上回っている．これは，75%条件では多くの記事でスコア改善のばらつき（差分の標準偏差）が極めて小さく，30記事全体を通じて非常に安定して底上げ効果が得られたためである（t値は平均差を差の標準誤差で割るため，ばらつきが小さいほど値が大きくなる）．"
    )
    add_body(
        "一方，意味の類似度（BERTScore F1）については，抽出率50%条件（0.6782）と0%条件（0.6718）の間で統計的有意差が認められず（対応のあるt検定: t(29) = 1.108, p = 0.28），全条件間を通じてスコアはほぼ横ばいであった．"
    )

    add_h2("3.3 ベースライン手法との比較結果")
    add_body(
        "提案手法（抽出率50%＋生成）と，4つのベースライン手法を比較した結果を図3および表2に示す．"
    )

    fig3_path = os.path.join(BASE_DIR, 'figures', 'fig3.png')
    if os.path.exists(fig3_path):
        p_img3 = doc.add_paragraph()
        p_img3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img3.paragraph_format.space_before = Pt(4)
        p_img3.paragraph_format.space_after = Pt(2)
        p_img3.paragraph_format.first_line_indent = None
        run_img3 = p_img3.add_run()
        run_img3.add_picture(fig3_path, width=Inches(3.3))
        add_caption("図3　ベースライン手法と提案ハイブリッド手法（50%）の性能比較（n=30）")

    add_caption("表2　ベースライン手法と提案ハイブリッド手法（50%）の比較（n=30）")

    table2 = doc.add_table(rows=6, cols=4)
    table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table2, color="CCCCCC", sz="4")
    set_col_widths(table2, [1.0, 0.75, 0.75, 0.8])

    headers2 = ["手法名", "ROUGE-1", "BERTScore", "対Base1差 (t値, p値)"]
    t2_data = [
        ["Base 1: 生成のみ", "0.2214±0.0514", "0.6718±0.0258", "— (対照群)"],
        ["Base 2: 純粋抽出型", "0.2974±0.0645", "0.6796±0.0234", "+0.0759 (t=10.291, p<0.001)"],
        ["Base 3: Lead-3+生成", "0.3283±0.0667", "0.6863±0.0233", "+0.1069 (t=14.945, p<0.001)"],
        ["Base 4: ランダム+生成", "0.3143±0.0654", "0.6847±0.0217", "+0.0929 (t=15.670, p<0.001)"],
        ["提案手法 (50%+生成)", "0.3460±0.0748", "0.6782±0.0243", "+0.1246 (t=11.882, p<0.001)"]
    ]

    for col_idx, text in enumerate(headers2):
        cell = table2.cell(0, col_idx)
        cell.text = text
        set_cell_background(cell, "EEEEEE")
        set_cell_margins(cell, top=40, bottom=40, left=40, right=40)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.bold = True
            r.font.name = 'ＭＳ ゴシック'
            r._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="ＭＳ ゴシック" w:hAnsi="ＭＳ ゴシック" w:eastAsia="ＭＳ ゴシック"/>'))
            r.font.size = Pt(8.0)

    for row_idx, row_vals in enumerate(t2_data):
        for col_idx, val in enumerate(row_vals):
            cell = table2.cell(row_idx + 1, col_idx)
            cell.text = val
            bg = "F9F9F9" if row_idx % 2 == 1 else "FFFFFF"
            if row_idx == 4:
                bg = "F0F4F8"
            set_cell_background(cell, bg)
            set_cell_margins(cell, top=35, bottom=35, left=40, right=40)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.font.name = 'ＭＳ 明朝'
                r._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="ＭＳ 明朝"/>'))
                r.font.size = Pt(7.5)
                if row_idx == 4 and col_idx in [0, 1]:
                    r.bold = True

    add_body(
        "表2および図3に示すように，提案ハイブリッド手法（50%）は，単語一致度（ROUGE-1）において，全文を直接入力する「生成のみ（0.2214）」はもちろん，生成モデルを使わない「純粋抽出型（0.2974）」や，適当に文を選ぶ「ランダム抽出＋生成（0.3143）」に対しても有意に高いスコア（0.3460）を達成した．"
    )
    add_body(
        "なお，4つのベースライン手法との並列比較にあたり，多重比較による偶然の有意差を抑制するためBonferroni補正（有意水準 α = 0.05 / 4 = 0.0125）を適用して検定を行った．その結果，生成のみ（t(29)=11.882, p < 0.001），純粋抽出型（t(29)=7.986, p < 0.001），およびランダム抽出＋生成（t(29)=3.106, 未調整 p = 0.0042 < 0.0125, 補正後 p = 0.0168 < 0.05）の3群に対し，統計的に有意な向上が維持されることを確認した．ニュース冒頭3文を使う「Lead-3＋生成（0.3283）」に対しても平均値として上回った（差 +0.0177, t(29)=1.652, 未調整 p = 0.109, Bonferroni補正後 p = 0.436）．"
    )
    add_body(
        "一方，意味の類似度（BERTScore）に関しては，Lead-3＋生成（0.6863）やランダム抽出＋生成（0.6847），純粋抽出型（0.6796）が提案手法（0.6782）をわずかに上回る値を示したものの，各条件間の差は極めて小さく，統計的な有意差は認められなかった（条件間で横ばい推移）．"
    )

    # IV. 考察
    add_h1("IV．考察")
    add_body(
        "得られた実験結果について，生成された要約文を実際に読み比べながら以下の5つの視点から考察した．"
    )
    add_body(
        "第一に，「なぜ抽出率50%で単語一致度（ROUGE-1）が大幅に向上したのか」という点である．実際に出力された文章を観察してみると，全文を直接入力した要約は平均文字数が多くなりがちで，事件の背景や関係者の細かいコメントといった副次的な情報（ノイズ）に引きずられ，記事の主語や結末といった最も重要な単語が欠落しやすい傾向があった．これに対し，抽出率50%の前処理を通した要約は，実測の平均文字数が約190文字程度にコンパクトに引き締まり，お手本の要約に含まれる重要キーワードがピンポイントで盛り込まれていた．つまり，抽出前処理が文章の無駄な部分を削ぎ落とし，言語モデルにとって最も処理しやすい「情報が凝縮された状態」を作ったことが，スコア向上の大きな要因であると考えられる（情報圧縮効果）．"
    )
    add_body(
        "第二に，「意味の類似度（BERTScore）において提案手法が抽出系ベースラインを上回らなかった理由」である．表2の通り，BERTScoreではLead-3＋生成（0.6863）等が提案手法（0.6782）をわずかに上回り，提案手法は抽出系4手法の中で最低水準にとどまった（ただし条件間の差は微小で統計的有意差はなし）．BARTは事前学習によって日本語の文章構造を深く理解しているため，冒頭3文のみを渡すLead-3等であっても文全体の大枠の意味や論旨は十分に捉えることができる．したがって，本研究で提案したハイブリッド手法の主たる優位性は，文全体の意味的類似度（BERTScore）の引き上げではなく，冗長な文を削ぎ落として記事固有の重要語句をピンポイントで捉える「重要キーワードの網羅性（ROUGE-1: 0.2214 → 0.3460）」の大幅な改善に特化していると評価するのが妥当である．"
    )
    add_body(
        "第三に，「ランダム抽出やLead-3との比較から何が分かったか」という点である．ランダム抽出＋生成（0.3143）は，全文入力（0.2214）よりはスコアが高かったものの，提案手法（0.3460）には及ばなかった．実際の生成文を確認すると，ランダム抽出ではたまたま重要文が選ばれた記事では良い要約になる一方，重要文が抜け落ちた記事では文脈が崩壊してスコアが大きく落ちており，安定性に欠けていた．このことから，「単に入力文字数を減らすこと」だけでなく，「TF-IDF等を用いて重要な文を確実に選ぶこと」が不可欠であると実感した．"
    )
    add_body(
        "また，ニュースの冒頭3文を使うLead-3＋生成（0.3283）が健闘したのは，一般的なニュース記事が「冒頭に結論や要点を書く（逆ピラミッド型）」という構造を持っているためである．しかし実際の記事の中には，冒頭に導入や情景描写が長く続き，中盤以降に事件の核心が書かれている記事も存在した．そうした記事ではLead-3は失敗していたが，本研究のTF-IDFに基づく抽出手法は文の位置に完全に縛られず重要文を拾い上げることができていた．この点から，本手法はニュース記事だけでなく，冒頭に結論があるとは限らない解説文や学校のレポートなど，多様な文章構造に対しても応用できる可能性があると考えられる．"
    )
    add_body(
        "第四に，実用環境における本研究の位置づけである．近年登場しているGPT-4などの超大規模クラウドLLMは極めて高い要約性能を持つ反面，インターネット通信への依存，継続的なAPI利用コスト，個人情報の外部送信リスク，推論遅延といった実用上の制約が存在する．これに対し，本研究で検証した「TF-IDF抽出前処理＋軽量ローカルモデル（BART）」の組み合わせは，通信が途絶した災害時や，プライバシー保護が求められる教育・医療・行政現場，さらにはスマート端末などのオンデバイス環境でも，モデル自体のサイズを増やすことなく安価に要約精度を引き上げられる実用的な技術的選択肢を提供するものである．"
    )
    add_body(
        "第五に，本研究の限界（Limitations）と今後の課題である．本研究には主に3つの限界が存在する．第1に，実験サンプル数が予備実験30件，本実験30件（計60件）と小規模なデータセットに基づいている点である．統計的検定により有意性は確認されたものの，より多様な記事群での大規模検証が望まれる．第2に，評価対象としたモデルがBART（stockmark/bart-base-japanese-news）1種類，データがXL-Sumのニュース記事1種類に限定されている点である．T5や他のモデルアーキテクチャ，ならびに論説文・会話文など他ジャンルの文書において最適な抽出率が50%付近で維持されるかは検証の余地がある．第3に，自動評価指標がROUGE-1（単語一致度）およびBERTScoreを中心としている点である．要約の連語・文構造の一致を測るROUGE-2やROUGE-L，ならびに人間による流暢性・事実性（ハルシネーションの有無）の定性評価を拡充することが今後の重要な課題である．"
    )

    # V. 結論
    add_h1("V．結論")
    add_body(
        "本研究では，抽出型要約と生成型要約を組み合わせたハイブリッド要約において，抽出率が要約品質に与える影響を二段階の実験（予備実験30件・本実験30件）により検証した．得られた主な知見は以下の3点である．\n"
        "1. 抽出率を1%から100%まで網羅的に変化させる予備実験により，抽出率30〜70%（特に50%付近）で要約の単語一致度（ROUGE-1）が最大化する傾向を発見した．\n"
        "2. 独立した検証用データセットを用いた本実験において，事前に適切な抽出率（50%）で重要文を絞り込んでから生成モデルに渡すことで，全文直接入力（0%条件: 0.2214）に比べて単語一致度（ROUGE-1）を0.3460へと大幅に向上させることができた（+0.1246, p < 0.001）．\n"
        "3. この品質向上は，前処理によって余分なノイズを削ぎ落とし，言語モデルが重要情報に集中できるようにする「情報圧縮効果」によるものであることが分かった．", indent=False
    )
    add_body(
        "今後は，ニュース記事以外の文章（教科書の説明文，小説，学校のレポートなど）にも本手法を適用して最適な抽出率を調べるとともに，元の文章の長さや難しさに応じてAIが自動で抽出率を切り替える仕組みの開発にも挑戦したい．"
    )

    # 文献
    add_h1("文献")
    references = [
        "1) Carbonell, J. G. and Goldstein, J. (1998): The Use of MMR, Diversity-Based Reranking for Reordering Documents and Producing Summaries, Proc. SIGIR '98, pp. 335–336.",
        "2) Hasan, T., Bhattacharjee, A., Islam, M. S., Mubasshir, K., Li, Y.-F., Kang, Y.-B., Rahman, M. S. and Shahriyar, R. (2021): XL-Sum: Large-Scale Multilingual Abstractive Summarization for 44 Languages, Findings of ACL-IJCNLP 2021, pp. 4693–4703.",
        "3) Ishikawa, K., Ando, S. and Okumura, A. (2001): Hybrid Text Summarization Method based on the TF Method and the Lead Method, Proc. NTCIR Workshop 2.",
        "4) Lin, C.-Y. (2004): ROUGE: A Package for Automatic Evaluation of Summaries, Proc. ACL Workshop, pp. 74–81.",
        "5) Rennard, V., Shang, G., Hunter, J. and Vazirgiannis, M. (2023): Abstractive Meeting Summarization: A Survey, Trans. ACL, Vol. 11, pp. 861–884.",
        "6) Salton, G. and Buckley, C. (1988): Term-weighting approaches in automatic text retrieval, Information Processing & Management, Vol. 24, No. 5, pp. 513–523.",
        "7) Stockmark Inc. (2023): stockmark/bart-base-japanese-news, Hugging Face Model Card.",
        "8) Zhang, T., Kishore, V., Wu, F., Weinberger, K. Q. and Artzi, Y. (2020): BERTScore: Evaluating Text Generation with BERT, Proc. ICLR 2020."
    ]
    for ref in references:
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.left_indent = Inches(0.2)
        p_ref.paragraph_format.first_line_indent = Inches(-0.2)
        p_ref.paragraph_format.space_after = Pt(2)
        p_ref.paragraph_format.line_spacing = 1.15
        r_ref = p_ref.add_run(ref)
        r_ref.font.name = 'Times New Roman'
        r_ref._r.get_or_add_rPr().append(parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="ＭＳ 明朝"/>'))
        r_ref.font.size = Pt(8.5)

    out_path = os.path.join(BASE_DIR, 'docs', 'paper_final.docx')
    try:
        doc.save(out_path)
        print(f"Successfully saved: {out_path}")
    except PermissionError:
        print(f"File locked by Word (skipping overwrite): {out_path}")

if __name__ == '__main__':
    create_perfect_submission_paper()
