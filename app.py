import streamlit as st
import json
import random
import re

st.set_page_config(page_title="數學智慧組卷系統", layout="wide")
st.title("📚 數學智慧組卷系統（花崗模版專業版）")

# 1. 讀取題庫
with open('questions.json', 'r', encoding='utf-8') as file:
    questions = json.load(file)

# 輔助函式：美化網頁預覽（把 LaTeX 專屬排版指令轉成網頁好讀格式）
def clean_for_web(text):
    # 將 \CJKunderline{名字} 轉為底線文字
    text = re.sub(r'\\CJKunderline\{(.*?)\}', r'<u>\1</u>', text)
    # 將複雜的 \rule...\textbf{(n)} 填充底線轉為乾淨的 ____(n)____
    text = re.sub(
        r'\\rule\[.*?\]\{.*?\}\{.*?\}\\raisebox\{.*?\}\{\\makebox\[.*?\]\[.*?\]\{\\makebox\[.*?\]\[.*?\]\{\\textbf\{(\(\d+\))\}\}\}\}',
        r' `______\1______` ',
        text
    )
    return text

# 輔助函式：自動產生 tabularx 答案卷表格
def build_answer_grid(q_list, start_num, cols_per_row=5, is_teacher=True):
    if not q_list:
        return ""
    total = len(q_list)
    cols = min(total, cols_per_row)
    col_spec = "|" + "Y|" * cols
    
    latex = f"\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}\n\\hline\n"
    
    # 將題目依每列格數分組
    for i in range(0, total, cols):
        chunk = q_list[i:i+cols]
        # 1. 題號列
        num_cells = [f"\\textbf{{({start_num + i + j})}}" for j in range(len(chunk))]
        while len(num_cells) < cols:
            num_cells.append("") # 補齊空白格避免 LaTeX 報錯
        latex += " & ".join(num_cells) + " \\\\ \\hline\n"
        
        # 2. 答案列 (教用版填紅字答案，學用版留空)
        if is_teacher:
            ans_cells = [f"{{\\color{{red}}{q.get('answer', '')}}}" for q in chunk]
        else:
            ans_cells = ["" for _ in chunk]
        while len(ans_cells) < cols:
            ans_cells.append("")
        latex += " & ".join(ans_cells) + " \\\\[0.6cm] \\hline\n"
        
    latex += "\\end{tabularx}\n"
    return latex

# 輔助函式：組裝完整 LaTeX 考卷程式碼 (is_teacher=True 為教用版，False 為學用版)
def generate_latex(exam_questions, title, range_text, doc_class, is_teacher=True):
    version_tag = "（教用詳解版）" if is_teacher else "（學生試題卷）"
    ans_sheet_tag = "答案卷（教用版）" if is_teacher else "答案卷"
    
    # 檔頭設定（完全復刻你的考卷格式）
    preamble = f"""\\documentclass{{{doc_class}}}

\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{array}}
\\usepackage{{tabularx}}
\\usepackage[table]{{xcolor}}
\\usepackage{{tikz}}
\\usepackage[margin=2cm]{{geometry}}
\\usepackage{{xeCJKfntef}}
\\usepackage{{enumitem}}
"""
    # 若選擇標準 article，補上中文與字體設定確保任何資料夾都能編譯
    if doc_class == "article":
        preamble += "\\usepackage{xeCJK}\n\\setCJKmainfont{BiauKaiTC}\n"

    preamble += f"""
\\linespread{{1.6}}
\\everymath{{\\displaystyle}}
\\setlist[enumerate]{{itemsep=1.5em, parsep=0.5em}}

\\begin{{document}}

\\section*{{{title}{version_tag}}}

\\noindent 範圍：{range_text} \\quad 班級：\\rule[-2ex]{{2cm}}{{0.4pt}} \\quad 座號：\\rule[-2ex]{{2cm}}{{0.4pt}} \\quad 姓名：\\rule[-2ex]{{2cm}}{{0.4pt}}
"""

    # 依大題分類整理題目
    sections_order = ["基測會考題", "進階能力題", "素養活用題", "非選應用題"]
    cn_nums = ["一", "二", "三", "四"]
    
    grouped = {sec: [] for sec in sections_order}
    for q in exam_questions:
        sec = q.get("section", "基測會考題")
        if sec not in grouped:
            grouped["基測會考題"].append(q)
        else:
            grouped[sec].append(q)

    body = ""
    blank_counter = 1
    section_idx = 0

    # 產生試題卷前半部（填充題三大題）
    for sec in ["基測會考題", "進階能力題", "素養活用題"]:
        sec_qs = grouped[sec]
        if not sec_qs:
            continue
        cn = cn_nums[section_idx]
        section_idx += 1
        body += f"\n\\subsection*{{{cn}、{sec}：}}\n\n\\begin{{enumerate}}\n"
        
        for q in sec_qs:
            # 自動將題目內的 (n) 替換為連續的新題號
            q_content = re.sub(
                r'\\textbf\{\(\d+\)\}',
                f'\\\\textbf{{({blank_counter})}}',
                q['content']
            )
            blank_counter += 1
            body += f"\\item {q_content}\n\n"
            
            # 如果是教用版，附上出處、藍字解析與紅字答案
            if is_teacher:
                sol_tex = q.get('solution', '').replace('\n', '\\\\\n    ')
                ans_tex = q.get('answer', '')
                body += f"""    【出處】{q['concept']}\\\\
    【解析】\\\\
    {{\\color{{blue}}
    {sol_tex}
    }}\\\\
    【答案】{{\\color{{red}}{ans_tex}}}\n\n"""
        body += "\\end{enumerate}\n"

    # 產生後半部：答案卷與非選應用題
    ans_sheet = f"""
\\newpage
\\newgeometry{{margin=1.2cm}}

\\section*{{{title} {ans_sheet_tag}}}

\\noindent 班級：\\rule[-2ex]{{2cm}}{{0.4pt}} \\quad 座號：\\rule[-2ex]{{2cm}}{{0.4pt}} \\quad 姓名：\\rule[-2ex]{{2cm}}{{0.4pt}}

\\newcolumntype{{Y}}{{>{{\\centering\\arraybackslash}}X}}
"""
    grid_counter = 1
    sec_idx_ans = 0
    for sec in ["基測會考題", "進階能力題", "素養活用題"]:
        sec_qs = grouped[sec]
        if not sec_qs:
            continue
        cn = cn_nums[sec_idx_ans]
        sec_idx_ans += 1
        cols_count = 8 if sec == "基測會考題" else 5
        ans_sheet += f"\n\\vspace{{0.4em}}\n\\noindent \\textbf{{{cn}、{sec}：}}\n\\vspace{{0.2em}}\n\n"
        ans_sheet += build_answer_grid(sec_qs, grid_counter, cols_per_row=cols_count, is_teacher=is_teacher)
        grid_counter += len(sec_qs)

    # 第四部分：非選應用題
    non_choice_qs = grouped["非選應用題"]
    if non_choice_qs:
        cn = cn_nums[sec_idx_ans]
        ans_sheet += f"\n\\vspace{{0.6em}}\n\\noindent \\textbf{{{cn}、非選應用題：（須寫出計算過程）}}\n\\vspace{{0.2em}}\n\n"
        ans_sheet += "{\\renewcommand\\arraystretch{1.2}\n\\begin{tabularx}{\\textwidth}{|X|}\n\\hline\n"
        for q in non_choice_qs:
            ans_sheet += f"\\textbf{{{grid_counter}.}} {q['content']} \\\\ \\hline\n"
            if is_teacher:
                sol_nc = q.get('solution', '').replace('\n', '\\newline\n')
                ans_nc = q.get('answer', '')
                ans_sheet += f"""\\textbf{{【出處】}} {q['concept']} \\\\
\\textbf{{【解析】}} \\newline
{{\\color{{blue}}
{sol_nc}
}} \\newline
\\textbf{{【答案】}} {{\\color{{red}}{ans_nc}}} \\\\ \\hline\n"""
            else:
                ans_sheet += "\\rule{0pt}{4.5cm} \\\\ \\hline\n"
            grid_counter += 1
        ans_sheet += "\\end{tabularx}}\n"

    ans_sheet += "\n\\restoregeometry\n\\end{document}\n"
    return preamble + body + ans_sheet


# ==========================================
# 網頁介面：三個分頁籤
# ==========================================
tab1, tab2 = st.tabs(["📝 挑選與組卷", "➕ 新增題目入庫"])

with tab1:
    st.sidebar.header("📝 考卷版面設定")
    exam_title = st.sidebar.text_input("考卷主標題", value="花崗國中 114 學年第一學期七年級第三次定期評量數學科")
    exam_range = st.sidebar.text_input("考試範圍", value="南一數學(一) 3-1 $\\sim$ 3-3")
    doc_class = st.sidebar.selectbox(
        "LaTeX 模版路徑",
        ["../../共用素材/mathtest", "article"],
        help="若放在你原本的資料夾結構請選 mathtest；若單獨編譯請選 article"
    )

    st.sidebar.divider()
    st.sidebar.header("🎯 步驟 1：篩選題庫範圍")

    all_sections = ["基測會考題", "進階能力題", "素養活用題", "非選應用題"]
    selected_sections = st.sidebar.multiselect("大題分類", all_sections, default=all_sections)

    all_concepts = sorted(list({q['concept'] for q in questions}))
    st.sidebar.subheader("核心觀念細項")
    selected_concepts = [c for c in all_concepts if st.sidebar.checkbox(c, value=True)]

    # 過濾題目
    filtered_q = [
        q for q in questions
        if q['concept'] in selected_concepts and q.get('section', '基測會考題') in selected_sections
    ]

    st.info(f"🔍 題庫總數：**{len(questions)}** 題 ｜ 符合左側篩選條件：**{len(filtered_q)}** 題")

    # 選擇組卷模式：手動勾選 vs 隨機抽題
    mode = st.radio("🎯 步驟 2：選擇挑題方式", ["🖐️ 手動勾選題目（推薦）", "🎲 電腦隨機抽題"], horizontal=True)

    selected_exam = []

    if mode == "🖐️ 手動勾選題目（推薦）":
        st.write("請在下方勾選你要放入考卷的題目：")
        col_btn1, col_btn2 = st.columns([1, 5])
        select_all = col_btn1.checkbox("✅ 全選目前篩選出的題目", value=False)
        
        for q in filtered_q:
            with st.container(border=True):
                c1, c2 = st.columns([1, 15])
                is_checked = c1.checkbox("", value=select_all, key=f"chk_{q['id']}")
                with c2:
                    st.markdown(f"**`{q['id']}`** ｜ `{q.get('section', '填充題')}` ｜ `{q['concept']}`")
                    # 使用美化函式顯示題目
                    preview_text = clean_for_web(q['content'])
                    if "\\begin{tikzpicture}" in preview_text or "\\begin{tabular}" in preview_text:
                        clean_t = re.sub(r'\\begin\{center\}.*?\\end\{center\}|\{\\centering.*?\\par\}', '', preview_text, flags=re.DOTALL)
                        st.markdown(clean_t, unsafe_allow_html=True)
                        st.caption("🎨 *(本題包含表格或 TikZ 圖形，匯出 LaTeX 時將完整呈現)*")
                    else:
                        st.markdown(preview_text, unsafe_allow_html=True)
                        
                    with st.expander(f"查看答案與解析（答案：{q.get('answer', '')}）"):
                        st.markdown(q['solution'])
                if is_checked:
                    selected_exam.append(q)
    else:
        max_q = max(1, len(filtered_q))
        num_to_draw = st.number_input("要隨機抽取幾題？", min_value=1, max_value=max_q, value=min(10, max_q))
        if st.button("🎲 立即隨機抽題"):
            st.session_state['random_exam'] = random.sample(filtered_q, num_to_draw)
        selected_exam = st.session_state.get('random_exam', [])

    # 匯出區塊
    if selected_exam:
        st.divider()
        st.success(f"🎉 目前已選定 **{len(selected_exam)}** 道題目！系統已自動重新編號並生成答案卷表格。")
        
        teacher_tex = generate_latex(selected_exam, exam_title, exam_range, doc_class, is_teacher=True)
        student_tex = generate_latex(selected_exam, exam_title, exam_range, doc_class, is_teacher=False)
        
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="📥 下載【學生空白卷 + 空白答案卷】(.tex)",
                data=student_tex,
                file_name="exam_student.tex",
                mime="text/plain",
                use_container_width=True
            )
        with dl_col2:
            st.download_button(
                label="📥 下載【教師詳解卷 + 紅字答案卷】(.tex)",
                data=teacher_tex,
                file_name="exam_teacher.tex",
                mime="text/plain",
                use_container_width=True
            )
            
        with st.expander("👀 預覽生成的 LaTeX 原始碼（教用版與學用版）"):
            sub_t1, sub_t2 = st.tabs(["教用詳解版原始碼", "學生試題卷原始碼"])
            with sub_t1:
                st.code(teacher_tex, language="latex")
            with sub_t2:
                st.code(student_tex, language="latex")

# ==========================================
# 分頁二：新增題目入庫
# ==========================================
with tab2:
    st.subheader("➕ 新增題目至 JSON 題庫")
    with st.form("add_question_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            new_id = st.text_input("題目編號 (如 HG114_34)")
        with col2:
            new_section = st.selectbox("大題分類", ["基測會考題", "進階能力題", "素養活用題", "非選應用題"])
        with col3:
            new_concept = st.text_input("核心觀念 (如 一元一次方程式>應用問題)")
        with col4:
            new_diff = st.selectbox("難易度", ["基礎", "進階"])
            
        new_content = st.text_area("題目內容 (直接貼上 LaTeX 語法)", height=120)
        new_answer = st.text_input("簡答 (用於填入 tabularx 答案卷表格，如 $18x-27$)")
        new_solution = st.text_area("詳細解析 (直接貼上 LaTeX 語法)", height=120)
        
        if st.form_submit_button("💾 儲存至題庫"):
            if not new_id or not new_concept or not new_content:
                st.error("⚠️ 請填寫完整欄位！")
            else:
                questions.append({
                    "id": new_id.strip(),
                    "concept": new_concept.strip(),
                    "difficulty": new_diff,
                    "section": new_section,
                    "type": "非選題" if new_section == "非選應用題" else "填充題",
                    "content": new_content.strip(),
                    "answer": new_answer.strip(),
                    "solution": new_solution.strip()
                })
                with open('questions.json', 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                st.success(f"🎉 成功新增題目：{new_id}！")
