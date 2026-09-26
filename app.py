import streamlit as st
import json
import random
import re

st.set_page_config(page_title="數學智慧組卷系統", layout="wide")
st.title("📚 數學智慧組卷系統")

# 1. 讀取題庫
with open('questions.json', 'r', encoding='utf-8') as file:
    questions = json.load(file)

# 輔助函式：美化網頁預覽
def clean_for_web(text):
    text = re.sub(r'\$\s+([^$]+?)\$', r'$\1$', text)
    text = re.sub(r'\$([^$]+?)\s+\$', r'$\1$', text)
    text = re.sub(r'\\CJKunderline\{(.*?)\}', r'<u>\1</u>', text)
    text = re.sub(
        r'\\rule\[.*?\]\{.*?\}\{.*?\}\\raisebox\{.*?\}\{\\makebox\[.*?\]\[.*?\]\{\\makebox\[.*?\]\[.*?\]\{\\textbf\{(\(\d+\))\}\}\}\}',
        r' <u>&nbsp;&nbsp;&nbsp;&nbsp;<b>\1</b>&nbsp;&nbsp;&nbsp;&nbsp;</u> ',
        text
    )
    return text

# 輔助函式：將來源標籤插入在題幹文字最後面（若有圖表則放在圖表上方文字的最右側）
def append_source_right(content, source_str, show_source):
    if not show_source or not source_str:
        return content
    tag_tex = f"\\penalty50\\hspace*{{1em}}\\hfill\\mbox{{{{\\small\\color{{darkgray}}【{source_str}】}}}}"
    
    # 若題目下方有置中圖表 (\begin{center} 或 {\centering)，將出處放在題幹文字結尾、圖表之前
    for marker in ["\n{\\centering", "\n\\begin{center}"]:
        if marker in content:
            parts = content.split(marker, 1)
            return parts[0] + tag_tex + marker + parts[1]
    return content + tag_tex

# 輔助函式：自動產生 tabularx 答案卷表格
def build_answer_grid(q_list, start_num, cols_per_row=5, is_teacher=True):
    if not q_list:
        return ""
    total = len(q_list)
    cols = min(total, cols_per_row)
    col_spec = "|" + "Y|" * cols
    
    latex = f"\\noindent\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}\n\\hline\n"
    for i in range(0, total, cols):
        chunk = q_list[i:i+cols]
        num_cells = [f"\\textbf{{({start_num + i + j})}}" for j in range(len(chunk))]
        while len(num_cells) < cols:
            num_cells.append("")
        latex += " & ".join(num_cells) + " \\\\ \\hline\n"
        
        if is_teacher:
            ans_cells = [f"{{\\color{{red}}{q.get('answer', '')}}}" for q in chunk]
        else:
            ans_cells = ["" for _ in chunk]
        while len(ans_cells) < cols:
            ans_cells.append("")
        latex += " & ".join(ans_cells) + " \\\\[0.55cm] \\hline\n"
        
    latex += "\\end{tabularx}\n"
    return latex

# 輔助函式：組裝完整 LaTeX 考卷程式碼（內建自動防跨頁與智慧排版）
def generate_latex(exam_questions, title, range_text, doc_class, calc_space=2.5, non_choice_height=4.0, show_source=True, is_teacher=True):
    version_tag = "（教用詳解版）" if is_teacher else "（學生試題卷）"
    ans_sheet_tag = "答案卷（教用版）" if is_teacher else "答案卷"
    
    if doc_class == "跨電腦通用獨立模版 (推薦)":
        preamble = """\\documentclass[12pt, a4paper]{article}
\\usepackage{xeCJK}
\\setCJKmainfont{BiauKaiTC} % Mac 標楷體，Windows 可改為 DFKai-SB
"""
    else:
        preamble = "\\documentclass{../../共用素材/mathtest}\n"

    preamble += f"""\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{array}}
\\usepackage{{tabularx}}
\\usepackage[table]{{xcolor}}
\\usepackage{{tikz}}
\\usepackage[margin=1.8cm]{{geometry}}
\\usepackage{{xeCJKfntef}}
\\usepackage{{enumitem}}

% 定義深灰色出處標籤顏色
\\definecolor{{darkgray}}{{RGB}}{{90, 90, 90}}

\\linespread{{1.5}}
\\everymath{{\\displaystyle}}
\\setlist[enumerate]{{itemsep=1.2em, parsep=0.4em}}

\\begin{{document}}

\\section*{{{title}{version_tag}}}

\\noindent 範圍：{range_text} \\hfill 班級：\\rule[-2ex]{{1.8cm}}{{0.4pt}} \\quad 座號：\\rule[-2ex]{{1.5cm}}{{0.4pt}} \\quad 姓名：\\rule[-2ex]{{2.2cm}}{{0.4pt}}
\\vspace{{0.2cm}}
"""

    fill_qs = [q for q in exam_questions if q.get("type", "填充題") == "填充題"]
    non_choice_qs = [q for q in exam_questions if q.get("type") == "非選題"]

    body = ""
    blank_counter = 1

    # 第一部分：填充題（加入 minipage 防跨頁切斷保護 + 學生卷計算留白）
    if fill_qs:
        body += "\n\\subsection*{一、填充題：}\n\n\\begin{enumerate}\n"
        for q in fill_qs:
            q_content = re.sub(
                r'\\textbf\{\(\d+\)\}',
                f'\\\\textbf{{({blank_counter})}}',
                q['content']
            )
            blank_counter += 1
            # 將深灰色【114花崗】加在題幹最後並靠右對齊
            q_content_with_tag = append_source_right(q_content, q.get('source', ''), show_source)
            
            # 使用 minipage[t]{\linewidth} 確保同一題（含圖表與計算空間）絕對不會被跨頁切開
            body += "\\item \\begin{minipage}[t]{\\linewidth}\n"
            body += f"{q_content_with_tag}\n"
            
            if is_teacher:
                sol_tex = q.get('solution', '').replace('\n', '\\\\\n    ')
                ans_tex = q.get('answer', '')
                body += f"""\\par\\vspace{{0.4em}}
    【觀念】{q.get('unit', '')} > {q['concept']} （難度：{q['difficulty']}）\\\\
    【解析】\\\\
    {{\\color{{blue}}
    {sol_tex}
    }}\\\\
    【答案】{{\\color{{red}}{ans_tex}}}
\\end{{minipage}}\n\n"""
            else:
                # 學生卷：自動加上計算留白空間
                body += f"\\par\\vspace{{{calc_space}cm}}\n\\end{{minipage}}\n\n"
                
        body += "\\end{enumerate}\n"

    # 若試題卷也有非選題，在試題卷印出題目（或直接整合於答案卷）
    # 後半部：答案卷與非選題（自動緊湊排版，防止大塊空白）
    ans_sheet = f"""
\\newpage
\\newgeometry{{top=1.2cm, bottom=1.2cm, left=1.5cm, right=1.5cm}}

\\section*{{{title} {ans_sheet_tag}}}

\\noindent 班級：\\rule[-2ex]{{2cm}}{{0.4pt}} \\quad 座號：\\rule[-2ex]{{2cm}}{{0.4pt}} \\quad 姓名：\\rule[-2ex]{{2.5cm}}{{0.4pt}}

\\newcolumntype{{Y}}{{>{{\\centering\\arraybackslash}}X}}
"""
    grid_counter = 1
    if fill_qs:
        # 若填充題較多，自動改為每列 8 格以節省答案卷垂直空間，讓下方非選題不會被擠到下一頁
        cols_count = 8 if len(fill_qs) > 10 else 5
        ans_sheet += "\n\\vspace{0.3em}\n\\noindent \\textbf{一、填充題：}\n\\vspace{0.2em}\n\n"
        ans_sheet += build_answer_grid(fill_qs, grid_counter, cols_per_row=cols_count, is_teacher=is_teacher)
        grid_counter += len(fill_qs)

    if non_choice_qs:
        sec_num = "二" if fill_qs else "一"
        ans_sheet += f"\n\\vspace{{0.5em}}\n\\noindent \\textbf{{{sec_num}、非選應用題：（須寫出計算過程）}}\n\\vspace{{0.2em}}\n\n"
        
        # 將每道非選題做成獨立的防斷頁方框，避免整個表格因第2題太長而整塊跳頁留白
        for q in non_choice_qs:
            q_nc_with_tag = append_source_right(q['content'], q.get('source', ''), show_source)
            ans_sheet += "\\noindent\\begin{minipage}{\\textwidth}\n"
            ans_sheet += "{\\renewcommand\\arraystretch{1.25}\n\\begin{tabularx}{\\textwidth}{|X|}\n\\hline\n"
            ans_sheet += f"\\textbf{{{grid_counter}.}} {q_nc_with_tag} \\\\ \\hline\n"
            if is_teacher:
                sol_nc = q.get('solution', '').replace('\n', '\\newline\n')
                ans_nc = q.get('answer', '')
                ans_sheet += f"""\\textbf{{【觀念】}} {q.get('unit', '')} > {q['concept']} （難度：{q['difficulty']}） \\\\
\\textbf{{【解析】}} \\newline
{{\\color{{blue}}
{sol_nc}
}} \\newline
\\textbf{{【答案】}} {{\\color{{red}}{ans_nc}}} \\\\ \\hline\n"""
            else:
                ans_sheet += f"\\rule{{0pt}}{{{non_choice_height}cm}} \\\\ \\hline\n"
            ans_sheet += "\\end{tabularx}}\n\\vspace{0.3cm}\n\\end{minipage}\n\n"
            grid_counter += 1

    ans_sheet += "\n\\restoregeometry\n\\end{document}\n"
    return preamble + body + ans_sheet


# ==========================================
# 網頁介面
# ==========================================
tab1, tab2 = st.tabs(["📝 挑選與組卷", "➕ 新增題目入庫"])

with tab1:
    st.sidebar.header("📝 考卷版面與自動排版設定")
    exam_title = st.sidebar.text_input("考卷主標題", value="花崗國中 114 學年七上第三次段考精選卷")
    exam_range = st.sidebar.text_input("考試範圍", value="一元一次方程式")
    show_source_tag = st.sidebar.checkbox("在每題尾端靠右印出處 (深灰色【114花崗】)", value=True)
    
    # 新增：學生卷計算空間與非選框高度微調滑桿
    calc_space_slider = st.sidebar.slider("📐 學生卷每題下方計算留白 (cm)", min_value=0.5, max_value=6.0, value=2.5, step=0.5)
    nc_height_slider = st.sidebar.slider("📐 答案卷非選題作答框高度 (cm)", min_value=2.5, max_value=8.0, value=3.8, step=0.2, help="若非選題被擠到下一頁，稍微調小此高度即可一頁完美塞滿！")
    
    doc_class = st.sidebar.selectbox(
        "LaTeX 模版設定",
        ["跨電腦通用獨立模版 (推薦)", "本機 ../../共用素材/mathtest"]
    )

    st.sidebar.divider()
    st.sidebar.header("🎯 步驟 1：篩選題庫範圍")

    all_schools = sorted(list({q.get('school', '未分類') for q in questions}))
    selected_schools = st.sidebar.multiselect("🏫 學校來源", all_schools, default=all_schools)

    diff_order = ["基礎", "中等", "進階", "資優"]
    selected_diffs = st.sidebar.multiselect("📊 學生體感難度", diff_order, default=diff_order)

    all_types = ["填充題", "非選題"]
    selected_types = st.sidebar.multiselect("✏️ 題型", all_types, default=all_types)

    all_units = sorted(list({q.get('unit', '未分類') for q in questions}))
    selected_unit = st.sidebar.selectbox("📂 核心大單元", ["全部單元"] + all_units)

    all_concepts = sorted(list({
        q['concept'] for q in questions
        if selected_unit == "全部單元" or q.get('unit') == selected_unit
    }))
    st.sidebar.subheader("🔍 細部考點（可複選）")
    selected_concepts = [c for c in all_concepts if st.sidebar.checkbox(c, value=True)]

    filtered_q = [
        q for q in questions
        if q.get('school', '未分類') in selected_schools
        and q.get('difficulty', '基礎') in selected_diffs
        and q.get('type', '填充題') in selected_types
        and (selected_unit == "全部單元" or q.get('unit') == selected_unit)
        and q['concept'] in selected_concepts
    ]

    st.info(f"🔍 題庫總數：**{len(questions)}** 題 ｜ 符合左側篩選條件：**{len(filtered_q)}** 題")

    mode = st.radio("🎯 步驟 2：選擇挑題方式", ["🖐️ 手動勾選題目（推薦）", "🎲 電腦隨機抽題"], horizontal=True)

    selected_exam = []

    if mode == "🖐️ 手動勾選題目（推薦）":
        btn_col1, btn_col2, _ = st.columns([1, 1, 4])
        if btn_col1.button("✅ 全選目前篩選題目", use_container_width=True):
            for q in filtered_q:
                st.session_state[f"chk_{q['id']}"] = True
        if btn_col2.button("⬜ 全部取消勾選", use_container_width=True):
            for q in filtered_q:
                st.session_state[f"chk_{q['id']}"] = False

        diff_badge = {"基礎": "🟢 基礎", "中等": "🟡 中等", "進階": "🔴 進階", "資優": "🟣 資優"}

        for q in filtered_q:
            chk_key = f"chk_{q['id']}"
            if chk_key not in st.session_state:
                st.session_state[chk_key] = False

            with st.container(border=True):
                c1, c2 = st.columns([1, 18])
                is_checked = c1.checkbox("", key=chk_key)
                with c2:
                    d_label = diff_badge.get(q.get('difficulty', '基礎'), q.get('difficulty', ''))
                    st.markdown(f"**`{q['id']}`** ｜ `{d_label}` ｜ `{q.get('type', '填充題')}` ｜ `{q['concept']}`")
                    
                    preview_text = clean_for_web(q['content'])
                    # 網頁預覽也呈現靠右的深灰色出處標籤
                    source_html = f"<span style='float:right; color:#5a5a5a; font-size:0.9em;'>【{q.get('source', '')}】</span>" if (show_source_tag and q.get('source')) else ""
                    
                    if "\\begin{tikzpicture}" in preview_text or "\\begin{tabular}" in preview_text:
                        clean_t = re.sub(r'\\begin\{center\}.*?\\end\{center\}|\{\\centering.*?\\par\}', '', preview_text, flags=re.DOTALL)
                        st.markdown(clean_t + source_html, unsafe_allow_html=True)
                        st.caption("🎨 *(本題包含表格或 TikZ 圖形，匯出 LaTeX 時將完整呈現)*")
                    else:
                        st.markdown(preview_text + source_html, unsafe_allow_html=True)
                        
                    with st.expander(f"查看答案與解析（答案：{q.get('answer', '')}）"):
                        st.markdown(clean_for_web(q['solution']), unsafe_allow_html=True)
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
        st.success(f"🎉 目前已選定 **{len(selected_exam)}** 道題目！已啟用「防跨頁切斷保護」與「自動計算留白」。")
        
        teacher_tex = generate_latex(
            selected_exam, exam_title, exam_range, doc_class,
            calc_space=calc_space_slider, non_choice_height=nc_height_slider,
            show_source=show_source_tag, is_teacher=True
        )
        student_tex = generate_latex(
            selected_exam, exam_title, exam_range, doc_class,
            calc_space=calc_space_slider, non_choice_height=nc_height_slider,
            show_source=show_source_tag, is_teacher=False
        )
        
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
        col1, col2, col3 = st.columns(3)
        with col1:
            new_id = st.text_input("題目編號 (如 114HG_7A_3_34)")
            new_school = st.text_input("學校全稱 (如 花崗國中)", value="花崗國中")
        with col2:
            new_source = st.text_input("簡短出處 (如 114花崗)", value="114花崗")
            new_unit = st.text_input("核心大單元 (如 M03 一元一次方程式)", value="M03 一元一次方程式")
        with col3:
            new_concept = st.text_input("細部考點 (如 解一元一次方程式)")
            new_diff = st.selectbox("學生體感難度", ["基礎", "中等", "進階", "資優"])
            
        new_type = st.selectbox("題型", ["填充題", "非選題"])
        new_content = st.text_area("題目內容 (直接貼上 LaTeX 語法)", height=120)
        new_answer = st.text_input("簡答 (用於填入 tabularx 答案卷表格，如 $18x-27$)")
        new_solution = st.text_area("詳細解析 (直接貼上 LaTeX 語法)", height=120)
        
        if st.form_submit_button("💾 儲存至題庫"):
            if not new_id or not new_concept or not new_content:
                st.error("⚠️ 請填寫完整欄位！")
            else:
                questions.append({
                    "id": new_id.strip(),
                    "school": new_school.strip(),
                    "source": new_source.strip(),
                    "unit": new_unit.strip(),
                    "concept": new_concept.strip(),
                    "difficulty": new_diff,
                    "type": new_type,
                    "content": new_content.strip(),
                    "answer": new_answer.strip(),
                    "solution": new_solution.strip()
                })
                with open('questions.json', 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                st.success(f"🎉 成功新增題目：{new_id}！")
