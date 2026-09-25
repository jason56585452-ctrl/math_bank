import streamlit as st
import json
import random
import re

st.set_page_config(page_title="數學智慧組卷系統", layout="wide")
st.title("📚 數學智慧組卷系統")

# 1. 讀取題庫
with open('questions.json', 'r', encoding='utf-8') as file:
    questions = json.load(file)

# 建立兩個分頁籤：一個用來出考卷，一個用來加題目
tab1, tab2 = st.tabs(["📝 挑選與組卷", "➕ 新增題目入庫"])

# ==========================================
# 分頁一：挑選與組卷
# ==========================================
with tab1:
    st.sidebar.header("📝 考卷基本設定")
    exam_title = st.sidebar.text_input("考卷標題", value="數學科隨堂測驗卷")
    question_space = st.sidebar.slider("每題作答留白高度 (cm)", min_value=1, max_value=8, value=3)

    st.sidebar.divider()
    st.sidebar.header("🎯 勾選出題條件")

    all_concepts = sorted(list({q['concept'] for q in questions}))
    st.sidebar.subheader("1. 選擇核心觀念")
    selected_concepts = [c for c in all_concepts if st.sidebar.checkbox(c, value=True)]

    st.sidebar.subheader("2. 選擇難易度")
    selected_diffs = st.sidebar.multiselect("難度篩選", ["基礎", "進階"], default=["基礎", "進階"])

    filtered_q = [
        q for q in questions
        if q['concept'] in selected_concepts and q['difficulty'] in selected_diffs
    ]

    st.info(f"🔍 目前題庫總數：**{len(questions)}** 題 ｜ 符合左側勾選條件：**{len(filtered_q)}** 題")

    max_q = max(1, len(filtered_q))
    num_to_draw = st.sidebar.number_input("3. 要抽取幾題？", min_value=1, max_value=max_q, value=min(3, max_q))

    if st.button("🚀 產生考卷"):
        if not filtered_q:
            st.warning("⚠️ 請至少在左側勾選一個觀念！")
        else:
            st.session_state['exam'] = random.sample(filtered_q, num_to_draw)

    if 'exam' in st.session_state and st.session_state['exam']:
        exam = st.session_state['exam']
        st.divider()
        st.subheader(f"📄 預覽：{exam_title}")
        
        for i, q in enumerate(exam, 1):
            st.markdown(f"**第 {i} 題** `{q['id']}` `{q['concept']}` `【{q['difficulty']}】`")
            
            content = q['content']
            if "\\begin{tikzpicture}" in content:
                clean_text = re.sub(r'\\begin\{center\}.*?\\end\{center\}|\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', '', content, flags=re.DOTALL)
                st.markdown(clean_text)
                st.caption("🎨 *(本題包含 TikZ 幾何圖形，將於匯出 LaTeX 編譯時完整呈現)*")
            else:
                st.markdown(content)
                
            with st.expander("查看詳解"):
                st.markdown(q['solution'])

        # --- 組合專屬 LaTeX 模版 ---
        latex_code = f"""\\documentclass[12pt, a4paper]{{article}}
\\usepackage{{xeCJK}}
\\usepackage{{amsmath, amssymb}}
\\usepackage{{tikz}}
\\usepackage{{geometry}}
\\geometry{{margin=2cm}}
\\setCJKmainfont{{BiauKaiTC}} % Mac 標楷體

\\begin{{document}}
\\begin{{center}}
    {{\\LARGE \\textbf{{{exam_title}}}}}
\\end{{center}}
\\vspace{{0.5cm}}

\\begin{{enumerate}}
"""
        for q in exam:
            latex_code += f"    \\item {q['content']}\n    \\vspace{{{question_space}cm}}\n\n"
            
        latex_code += """\\end{enumerate}

\\newpage
\\begin{center}
    {\\LARGE \\textbf{解答與解析}}
\\end{center}
\\begin{enumerate}
"""
        for q in exam:
            latex_code += f"    \\item {q['solution']}\n\n"
            
        latex_code += """\\end{enumerate}
\\end{document}
"""

        st.divider()
        st.download_button(
            label="📥 點此下載 LaTeX 考卷檔 (exam.tex)",
            data=latex_code,
            file_name="exam.tex",
            mime="text/plain"
        )
        with st.expander("👀 查看 LaTeX 原始碼"):
            st.code(latex_code, language="latex")

# ==========================================
# 分頁二：新增題目入庫 (免改雙斜線神器)
# ==========================================
with tab2:
    st.subheader("➕ 新增題目至 JSON 題庫")
    st.write("直接貼上一般 LaTeX 語法即可，系統會自動處理雙斜線與排版格式！")
    
    with st.form("add_question_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_id = st.text_input("題目編號 (如 M01_003)")
        with col2:
            new_concept = st.text_input("核心觀念 (如 M01整數的運算)")
        with col3:
            new_diff = st.selectbox("難易度", ["基礎", "進階"])
            
        new_content = st.text_area("題目內容 (直接貼上 LaTeX 語法，支援 TikZ)", height=150)
        new_solution = st.text_area("解答與解析 (直接貼上 LaTeX 語法)", height=100)
        
        submitted = st.form_submit_button("💾 儲存至題庫")
        
        if submitted:
            if not new_id or not new_concept or not new_content:
                st.error("⚠️ 請填寫完整「題目編號」、「核心觀念」與「題目內容」！")
            else:
                # 組合新題目字典
                new_q = {
                    "id": new_id.strip(),
                    "concept": new_concept.strip(),
                    "difficulty": new_diff,
                    "content": new_content.strip(),
                    "solution": new_solution.strip()
                }
                questions.append(new_q)
                
                # 自動轉換格式並寫回 questions.json
                with open('questions.json', 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                    
                st.success(f"🎉 成功新增題目：{new_id}！請重新整理網頁（Cmd + R）以更新左側選單。")