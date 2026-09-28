import streamlit as st
import streamlit.components.v1 as components
import json
import random
import re
import subprocess
import tempfile
import os
import platform
import base64

st.set_page_config(page_title="數學智慧組卷系統", layout="wide")
st.title("📚 數學智慧組卷系統")

# 1. 讀取題庫並確保 session_state 同步
if 'questions_db' not in st.session_state:
    with open('questions.json', 'r', encoding='utf-8') as file:
        loaded_q = json.load(file)
    for q in loaded_q:
        if q.get('unit') == "M03 一元一次方程式":
            q['unit'] = "M04 一元一次方程式"
    st.session_state['questions_db'] = loaded_q

questions = st.session_state['questions_db']

m_units = [
    "M01 整數的運算", "M02 最大公因數與最小公倍數", "M03 分數的運算", "M04 一元一次方程式",
    "M05 統計圖表與資料分析", "M06 二元一次聯立方程式", "M07 直角坐標與二元一次方程式的圖形",
    "M08 比與比例式", "M09 一元一次不等式", "M10 垂直、線對稱與三視圖", "M11 乘法公式與多項式",
    "M12 平方根與畢氏定理", "M13 因式分解", "M14 一元二次方程式", "M15 統計資料處理",
    "M16 數列與級數", "M17 函數", "M18 三角形的基本性質", "M19 平行與四邊形",
    "M20 相似形", "M21 圓形", "M22 幾何與證明", "M23 二次函數", "M24 統計與機率", "M25 生活中的立體圖形"
]

# 輔助函式：使用 PDF.js 將 PDF 渲染為高解析度畫布（突破 Chrome/Safari iframe 空白限制）
def render_pdf_preview(pdf_bytes, height=750):
    b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 16px;
                background-color: #525659;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .page-badge {{
                color: #ffffff;
                background: rgba(0, 0, 0, 0.65);
                padding: 4px 14px;
                border-radius: 14px;
                font-size: 13px;
                font-weight: 600;
                margin: 8px 0 6px 0;
                letter-spacing: 0.5px;
            }}
            canvas {{
                background-color: white;
                box-shadow: 0 4px 14px rgba(0,0,0,0.45);
                margin-bottom: 18px;
                max-width: 100%;
                height: auto !important;
                border-radius: 2px;
            }}
            #loading {{
                color: #ffffff;
                font-size: 15px;
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <div id="loading">⏳ 正在繪製 PDF 預覽頁面...</div>
        <div id="pdf-container" style="display:flex; flex-direction:column; align-items:center; width:100%;"></div>
        <script>
            const pdfData = atob("{b64_pdf}");
            const uint8Array = new Uint8Array(pdfData.length);
            for (let i = 0; i < pdfData.length; i++) {{
                uint8Array[i] = pdfData.charCodeAt(i);
            }}

            const pdfjsLib = window['pdfjs-dist/build/pdf'];
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';

            pdfjsLib.getDocument({{data: uint8Array}}).promise.then(async function(pdf) {{
                document.getElementById('loading').style.display = 'none';
                const container = document.getElementById('pdf-container');
                for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {{
                    const page = await pdf.getPage(pageNum);
                    const viewport = page.getViewport({{scale: 1.6}});

                    const badge = document.createElement('div');
                    badge.className = 'page-badge';
                    badge.innerText = `📄 第 ${{pageNum}} 頁 / 共 ${{pdf.numPages}} 頁`;
                    container.appendChild(badge);

                    const canvas = document.createElement('canvas');
                    const context = canvas.getContext('2d');
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    container.appendChild(canvas);

                    await page.render({{canvasContext: context, viewport: viewport}}).promise;
                }}
            }}).catch(function(err) {{
                document.getElementById('loading').innerText = '⚠️ 預覽載入失敗：' + err.message;
            }});
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=height, scrolling=True)

# 輔助函式：美化網頁預覽（支援 \quad, \CJKsout 與 LaTeX 換行 \\）
def clean_for_web(text):
    text = re.sub(r'\$\s+([^$]+?)\$', r'$\1$', text)
    text = re.sub(r'\$([^$]+?)\s+\$', r'$\1$', text)
    text = re.sub(r'\\CJKunderline\{(.*?)\}', r'<u>\1</u>', text)
    text = re.sub(r'\\CJKsout\{(.*?)\}', r'<del>\1</del>', text)
    text = re.sub(r'\\sout\{(.*?)\}', r'<del>\1</del>', text)
    text = re.sub(
        r'\\rule\[.*?\]\{.*?\}\{.*?\}\\raisebox\{.*?\}\{\\makebox\[.*?\]\[.*?\]\{\\makebox\[.*?\]\[.*?\]\{\\textbf\{(\(\d+\))\}\}\}\}',
        r' <u>&nbsp;&nbsp;&nbsp;&nbsp;<b>\1</b>&nbsp;&nbsp;&nbsp;&nbsp;</u> ',
        text
    )
    text = re.sub(r'\\rule\[.*?\]\{.*?\}\{.*?\}', r' <u>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</u> ', text)
    text = text.replace('\\qquad', '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;')
    text = text.replace('\\quad', '&nbsp;&nbsp;&nbsp;&nbsp;')
    text = text.replace('\\[0.5em]', '<br>')
    text = re.sub(r'\\\\\s*(?!\\hline)', '<br>', text)
    return text

# 輔助函式：將來源標籤插入在題幹文字最後面（靠右對齊 + 深灰色）
def append_source_right(content, source_str, show_source):
    if not show_source or not source_str:
        return content
    tag_tex = f"\\penalty50\\hspace*{{1em}}\\hfill\\mbox{{{{\\small\\color{{darkgray}}【{source_str}】}}}}"
    
    # 若為選擇題且有換行選項，將出處放在第一行題幹尾端（選項之前）
    if "\\\\\n(A)" in content:
        parts = content.split("\\\\\n(A)", 1)
        return parts[0] + tag_tex + "\\\\\n(A)" + parts[1]
        
    for marker in ["\n{\\centering", "\n\\begin{center}"]:
        if marker in content:
            parts = content.split(marker, 1)
            return parts[0] + tag_tex + marker + parts[1]
    return content + tag_tex

# 輔助函式：自動產生 tabularx 答案卷表格（支援選擇題與填充題不同標頭格式）
def build_answer_grid(q_list, start_num, cols_per_row=4, cell_height=0.8, is_teacher=True, label_fmt="({n})"):
    if not q_list:
        return ""
    total = len(q_list)
    cols = min(total, cols_per_row)
    col_spec = "|" + "Y|" * cols
    
    latex = f"\\noindent\\begin{{tabularx}}{{\\textwidth}}{{{col_spec}}}\n\\hline\n"
    for i in range(0, total, cols):
        chunk = q_list[i:i+cols]
        num_cells = [f"\\textbf{{{label_fmt.format(n=start_num + i + j)}}}" for j in range(len(chunk))]
        while len(num_cells) < cols:
            num_cells.append("")
        latex += " & ".join(num_cells) + " \\\\ \\hline\n"
        
        if is_teacher:
            ans_cells = [f"{{\\color{{red}}{q.get('answer', '')}}}" for q in chunk]
        else:
            ans_cells = ["" for _ in chunk]
        while len(ans_cells) < cols:
            ans_cells.append("")
        latex += " & ".join(ans_cells) + f" \\\\[{cell_height}cm] \\hline\n"
        
    latex += "\\end{tabularx}\n"
    return latex

# 輔助函式：組裝完整 LaTeX 考卷程式碼（支援答案卷自動單頁滿版 Auto-Fit）
def generate_latex(exam_questions, title, range_text, doc_class, calc_space=2.5, choice_cols=10, choice_height=0.4, ans_cols=4, ans_height=0.8, non_choice_height=3.8, auto_fit_ans=True, show_source=True, is_teacher=True):
    version_tag = "（教用詳解版）" if is_teacher else "（學生試題卷）"
    ans_sheet_tag = "答案卷（教用版）" if is_teacher else "答案卷"
    
    if doc_class == "跨電腦通用獨立模版 (推薦)":
        preamble = """\\documentclass[12pt, a4paper]{article}
\\usepackage{xeCJK}
\\setCJKmainfont{BiauKaiTC} % Mac 標楷體
"""
    else:
        preamble = "\\documentclass{../../共用素材/mathtest}\n"

    preamble += f"""\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{array}}
\\usepackage{{tabularx}}
\\usepackage[table]{{xcolor}}
\\usepackage{{tikz}}
\\usepackage{{graphicx}}
\\usepackage[margin=1.8cm]{{geometry}}
\\usepackage{{xeCJKfntef}}
\\usepackage{{enumitem}}

\\definecolor{{darkgray}}{{RGB}}{{90, 90, 90}}

\\newsavebox{{\\topgridsbox}}
\\newsavebox{{\\ncstemsbox}}
\\newsavebox{{\\ansfullpagebox}}
\\newlength{{\\availheight}}
\\newlength{{\\autoncheight}}

\\linespread{{1.5}}
\\everymath{{\\displaystyle}}
\\setlist[enumerate]{{itemsep=1.2em, parsep=0.4em}}

\\begin{{document}}

\\section*{{{title}{version_tag}}}

\\noindent 範圍：{range_text} \\hfill 班級：\\rule[-2ex]{{1.8cm}}{{0.4pt}} \\quad 座號：\\rule[-2ex]{{1.5cm}}{{0.4pt}} \\quad 姓名：\\rule[-2ex]{{2.2cm}}{{0.4pt}}
\\vspace{{0.2cm}}
"""

    choice_qs = [q for q in exam_questions if q.get("type") == "選擇題"]
    fill_qs = [q for q in exam_questions if q.get("type", "填充題") == "填充題"]
    non_choice_qs = [q for q in exam_questions if q.get("type") == "非選題"]

    cn_nums = ["一", "二", "三", "四"]
    body = ""
    sec_idx = 0

    # 1. 試題卷：選擇題
    if choice_qs:
        sec_title = cn_nums[sec_idx]
        sec_idx += 1
        body += f"\n\\subsection*{{{sec_title}、選擇題：}}\n\n\\begin{{enumerate}}[leftmargin=*]\n"
        for idx, q in enumerate(choice_qs, 1):
            q_content_with_tag = append_source_right(q['content'], q.get('source', ''), show_source)
            ans_clean = q.get('answer', '').strip().replace('(', '').replace(')', '')
            if is_teacher:
                item_label = f"[({{\\color{{red}}\\textbf{{{ans_clean}}}}})\\ \\ {idx}.]"
            else:
                item_label = f"[(\\quad\\ \\ )\\ \\ {idx}.]"
                
            body += f"\\item{item_label} \\begin{{minipage}}[t]{{\\linewidth}}\n"
            body += f"{q_content_with_tag}\n"
            
            if is_teacher:
                sol_tex = q.get('solution', '').replace('\n', '\\\\\n    ')
                body += f"""\\par\\vspace{{0.4em}}
    【觀念】{q.get('unit', '')} > {q['concept']} （難度：{q['difficulty']}）\\\\
    【解析】\\\\
    {{\\color{{blue}}
    {sol_tex}
    }}\\\\
    【答案】{{\\color{{red}}{q.get('answer', '')}}}
\\end{{minipage}}\n\n"""
            else:
                body += f"\\par\\vspace{{{calc_space}cm}}\n\\end{{minipage}}\n\n"
        body += "\\end{enumerate}\n"

    # 2. 試題卷：填充題
    blank_counter = 1
    if fill_qs:
        sec_title = cn_nums[sec_idx]
        sec_idx += 1
        body += f"\n\\subsection*{{{sec_title}、填充題：}}\n\n\\begin{{enumerate}}[leftmargin=*]\n"
        for q in fill_qs:
            q_content = re.sub(
                r'\\textbf\{\(\d+\)\}',
                f'\\\\textbf{{({blank_counter})}}',
                q['content']
            )
            blank_counter += 1
            q_content_with_tag = append_source_right(q_content, q.get('source', ''), show_source)
            
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
                body += f"\\par\\vspace{{{calc_space}cm}}\n\\end{{minipage}}\n\n"
                
        body += "\\end{enumerate}\n"

    # ==========================================
    # 答案卷組裝（支援自動單頁滿版引擎）
    # ==========================================
    ans_sheet = f"""
\\newpage
\\newgeometry{{top=1.2cm, bottom=1.2cm, left=1.5cm, right=1.5cm}}

\\section*{{{title} {ans_sheet_tag}}}

\\noindent 班級：\\rule[-2ex]{{2cm}}{{0.4pt}} \\quad 座號：\\rule[-2ex]{{2cm}}{{0.4pt}} \\quad 姓名：\\rule[-2ex]{{2.5cm}}{{0.4pt}} \\hfill 得分：\\rule[-2ex]{{2cm}}{{0.4pt}}
\\par\\vspace{{0.2em}}

\\newcolumntype{{Y}}{{>{{\\centering\\arraybackslash}}X}}
"""
    # 先組裝「選擇題 + 填充題」區塊
    top_grids_tex = ""
    ans_sec_idx = 0
    if choice_qs:
        sec_title = cn_nums[ans_sec_idx]
        ans_sec_idx += 1
        top_grids_tex += f"\\vspace{{0.2em}}\n\\noindent \\textbf{{{sec_title}、選擇題：}}\n\\vspace{{0.15em}}\n\n"
        choice_qs_for_grid = []
        for q in choice_qs:
            q_copy = dict(q)
            q_copy['answer'] = q.get('answer', '').replace('(', '').replace(')', '')
            choice_qs_for_grid.append(q_copy)
        top_grids_tex += build_answer_grid(choice_qs_for_grid, 1, cols_per_row=choice_cols, cell_height=choice_height, is_teacher=is_teacher, label_fmt="{n}.")

    grid_counter = 1
    if fill_qs:
        sec_title = cn_nums[ans_sec_idx]
        ans_sec_idx += 1
        top_grids_tex += f"\n\\vspace{{0.4em}}\n\\noindent \\textbf{{{sec_title}、填充題：}}\n\\vspace{{0.15em}}\n\n"
        top_grids_tex += build_answer_grid(fill_qs, grid_counter, cols_per_row=ans_cols, cell_height=ans_height, is_teacher=is_teacher, label_fmt="({n})")
        grid_counter += len(fill_qs)

    # 輔助內部函式：組裝非選題區塊
    def build_nc_section(sec_title_str, height_expr):
        nc_tex = f"\n\\vspace{{0.4em}}\n\\noindent \\textbf{{{sec_title_str}、非選應用題：（須寫出計算過程）}}\n\\vspace{{0.15em}}\n\n"
        nc_counter = 1
        for q in non_choice_qs:
            q_nc_with_tag = append_source_right(q['content'], q.get('source', ''), show_source)
            nc_tex += "\\noindent\\begin{minipage}{\\textwidth}\n"
            nc_tex += "{\\renewcommand\\arraystretch{1.25}\n\\begin{tabularx}{\\textwidth}{|X|}\n\\hline\n"
            nc_tex += f"\\textbf{{{nc_counter}.}} {q_nc_with_tag} \\\\ \\hline\n"
            if is_teacher:
                sol_nc = q.get('solution', '').replace('\n', '\\newline\n')
                ans_nc = q.get('answer', '')
                nc_tex += f"""\\textbf{{【觀念】}} {q.get('unit', '')} > {q['concept']} （難度：{q['difficulty']}） \\\\
\\textbf{{【解析】}} \\newline
{{\\color{{blue}}
{sol_nc}
}} \\newline
\\textbf{{【答案】}} {{\\color{{red}}{ans_nc}}} \\\\ \\hline\n"""
            else:
                nc_tex += f"\\rule{{0pt}}{{{height_expr}}} \\\\ \\hline\n"
            nc_tex += "\\end{tabularx}}\n\\vspace{0.25cm}\n\\end{minipage}\n\n"
            nc_counter += 1
        return nc_tex

    # 判斷是否啟用「學生答案卷自動單頁滿版」
    if auto_fit_ans and (not is_teacher):
        ans_sheet += f"\\begin{{lrbox}}{{\\topgridsbox}}\n\\begin{{minipage}}{{\\textwidth}}\n{top_grids_tex}\n\\end{{minipage}}\n\\end{{lrbox}}\n"
        if non_choice_qs:
            sec_title = cn_nums[ans_sec_idx]
            dummy_nc_tex = build_nc_section(sec_title, "0pt")
            real_nc_tex = build_nc_section(sec_title, "\\autoncheight")
            num_nc = len(non_choice_qs)
            ans_sheet += f"""\\begin{{lrbox}}{{\\ncstemsbox}}
\\begin{{minipage}}{{\\textwidth}}
{dummy_nc_tex}
\\end{{minipage}}
\\end{{lrbox}}
\\setlength{{\\availheight}}{{\\dimexpr \\textheight - 2.5cm - \\ht\\topgridsbox - \\dp\\topgridsbox - \\ht\\ncstemsbox - \\dp\\ncstemsbox \\relax}}
\\setlength{{\\autoncheight}}{{\\dimexpr \\availheight / {num_nc} \\relax}}
\\ifdim\\autoncheight<1.8cm \\setlength{{\\autoncheight}}{{1.8cm}}\\fi
\\ifdim\\autoncheight>9.0cm \\setlength{{\\autoncheight}}{{9.0cm}}\\fi
"""
            full_ans_body = "\\noindent\\usebox{\\topgridsbox}\\par\n" + real_nc_tex
        else:
            full_ans_body = "\\noindent\\usebox{\\topgridsbox}\\par\n"

        # 外層防爆頁保護：若總高度超過單頁可用高度，自動微幅等比例縮小至單頁
        ans_sheet += f"""\\begin{{lrbox}}{{\\ansfullpagebox}}
\\begin{{minipage}}{{\\textwidth}}
{full_ans_body}
\\end{{minipage}}
\\end{{lrbox}}
\\ifdim\\dimexpr\\ht\\ansfullpagebox+\\dp\\ansfullpagebox\\relax > \\dimexpr\\textheight-2.3cm\\relax
    \\noindent\\resizebox*{{!}}{{\\dimexpr\\textheight-2.3cm\\relax}}{{\\usebox{{\\ansfullpagebox}}}}
\\else
    \\noindent\\usebox{{\\ansfullpagebox}}
\\fi
"""
    else:
        # 手動模式或教用詳解卷
        ans_sheet += top_grids_tex
        if non_choice_qs:
            sec_title = cn_nums[ans_sec_idx]
            ans_sheet += build_nc_section(sec_title, f"{non_choice_height}cm")

    ans_sheet += "\n\\restoregeometry\n\\end{document}\n"
    return preamble + body + ans_sheet

# 輔助函式：在背景呼叫 XeLaTeX 直接編譯成 PDF
def compile_to_pdf(tex_code):
    if platform.system() == "Linux":
        tex_code = tex_code.replace("{BiauKaiTC}", "{AR PL UKai TW}")
        tex_code = tex_code.replace("\\documentclass{../../共用素材/mathtest}", "\\documentclass[12pt, a4paper]{article}\n\\usepackage{xeCJK}\n\\setCJKmainfont{AR PL UKai TW}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "exam.tex")
        pdf_path = os.path.join(tmpdir, "exam.pdf")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_code)
        try:
            res = subprocess.run(
                ["xelatex", "-interaction=nonstopmode", "exam.tex"],
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30
            )
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    return True, f.read(), res.stdout
            else:
                return False, None, res.stdout + "\n" + res.stderr
        except FileNotFoundError:
            return False, None, "找不到 xelatex 編譯器！若在雲端請確認已在 GitHub 建立 packages.txt 並重啟 App。"
        except Exception as e:
            return False, None, str(e)


# ==========================================
# 若題庫有經過線上修改，於頂部顯示同步回 GitHub 提醒
# ==========================================
if st.session_state.get('db_modified', False):
    with st.warning("⚠️ 你剛剛修改或合併了題庫！目前變更已套用至本次組卷；若要永久保存至雲端，請展開下方複製最新 JSON 貼回 GitHub 的 `questions.json`："):
        updated_json_str = json.dumps(questions, ensure_ascii=False, indent=2)
        st.download_button("📥 下載更新後的 questions.json", data=updated_json_str, file_name="questions.json", mime="application/json")
        with st.expander("📋 點此複製更新後的 questions.json 原始碼"):
            st.code(updated_json_str, language="json")

# ==========================================
# 網頁介面：三個分頁籤
# ==========================================
tab1, tab2, tab3 = st.tabs(["📝 挑選與組卷", "➕ 單題新增", "🤖 AI 批次匯入與規格書"])

with tab1:
    st.sidebar.header("📝 考卷版面與自動排版設定")
    exam_title = st.sidebar.text_input("考卷主標題", value="國中數學七上段考精選卷")
    exam_range = st.sidebar.text_input("考試範圍", value="M01 整數的運算")
    show_source_tag = st.sidebar.checkbox("在每題尾端靠右印出處 (深灰色【113國風】)", value=True)
    
    st.sidebar.subheader("📐 空間與答案卷格子微調")
    auto_fit_toggle = st.sidebar.checkbox(
        "✨ 答案卷自動單頁滿版 (Auto-Fit)",
        value=True,
        help="自動計算剩餘垂直空間並均分給非選題作答框，且強制鎖定學生答案卷為 1 頁不溢頁！"
    )
    calc_space_slider = st.sidebar.slider("學生卷每題下方計算留白 (cm)", min_value=0.2, max_value=6.0, value=2.0, step=0.2)
    choice_cols_slider = st.sidebar.slider("答案卷【選擇題每列幾格】", min_value=5, max_value=10, value=10, step=1)
    choice_height_slider = st.sidebar.slider("答案卷【選擇格高度】(cm)", min_value=0.3, max_value=1.2, value=0.4, step=0.1)
    ans_cols_slider = st.sidebar.slider("答案卷【填充題每列幾格】", min_value=2, max_value=8, value=4, step=1)
    ans_height_slider = st.sidebar.slider("答案卷【填充格高度】(cm)", min_value=0.4, max_value=1.8, value=0.8, step=0.1)
    nc_height_slider = st.sidebar.slider(
        "答案卷【非選題框高度】(cm)",
        min_value=2.5, max_value=8.0, value=3.8, step=0.2,
        disabled=auto_fit_toggle
    )
    
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

    all_types = ["選擇題", "填充題", "非選題"]
    selected_types = st.sidebar.multiselect("✏️ 題型", all_types, default=all_types)

    all_units = sorted(list({q.get('unit', '未分類') for q in questions}))
    selected_units = st.sidebar.multiselect("📂 核心大單元 (可複選)", all_units, default=all_units)

    all_concepts = sorted(list({
        q['concept'] for q in questions
        if q.get('unit') in selected_units
    }))
    st.sidebar.subheader("🔍 細部考點（可複選）")
    selected_concepts = [c for c in all_concepts if st.sidebar.checkbox(c, value=True)]

    filtered_q = [
        q for q in questions
        if q.get('school', '未分類') in selected_schools
        and q.get('difficulty', '基礎') in selected_diffs
        and q.get('type', '填充題') in selected_types
        and q.get('unit') in selected_units
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
        type_badge = {"選擇題": "🔘 選擇題", "填充題": "✏️ 填充題", "非選題": "📐 非選題"}

        for q in filtered_q:
            chk_key = f"chk_{q['id']}"
            if chk_key not in st.session_state:
                st.session_state[chk_key] = False

            with st.container(border=True):
                c1, c2 = st.columns([1, 18])
                is_checked = c1.checkbox("", key=chk_key)
                with c2:
                    d_label = diff_badge.get(q.get('difficulty', '基礎'), q.get('difficulty', ''))
                    t_label = type_badge.get(q.get('type', '填充題'), q.get('type', '填充題'))
                    st.markdown(f"**`{q['id']}`** ｜ `{t_label}` ｜ `{d_label}` ｜ `{q.get('unit', '')}` ▸ `{q['concept']}`")
                    
                    preview_text = clean_for_web(q['content'])
                    source_html = f"<span style='float:right; color:#5a5a5a; font-size:0.9em;'>【{q.get('source', '')}】</span>" if (show_source_tag and q.get('source')) else ""
                    
                    if "\\begin{tikzpicture}" in preview_text or "\\begin{tabular}" in preview_text:
                        clean_t = re.sub(r'\\begin\{center\}.*?\\end\{center\}|\{\\centering.*?\\par\}', '', preview_text, flags=re.DOTALL)
                        st.markdown(clean_t + source_html, unsafe_allow_html=True)
                        st.caption("🎨 *(本題包含表格或 TikZ 圖形，匯出時將完整呈現)*")
                    else:
                        st.markdown(preview_text + source_html, unsafe_allow_html=True)
                        
                    col_exp1, col_exp2 = st.columns(2)
                    with col_exp1:
                        with st.expander(f"👀 查看答案與解析（答案：{q.get('answer', '')}）"):
                            st.markdown(clean_for_web(q['solution']), unsafe_allow_html=True)
                    with col_exp2:
                        with st.expander("✏️ 快速修改此題（題型 / 難度 / 觀念 / 內容）"):
                            with st.form(f"edit_form_{q['id']}"):
                                ec1, ec2, ec3, ec4 = st.columns(4)
                                with ec1:
                                    curr_t_idx = all_types.index(q.get('type', '填充題')) if q.get('type') in all_types else 1
                                    edit_type = st.selectbox("題型", all_types, index=curr_t_idx, key=f"ed_type_{q['id']}")
                                with ec2:
                                    curr_d_idx = diff_order.index(q.get('difficulty', '基礎')) if q.get('difficulty') in diff_order else 0
                                    edit_diff = st.selectbox("難度", diff_order, index=curr_d_idx, key=f"ed_diff_{q['id']}")
                                with ec3:
                                    curr_u_idx = m_units.index(q.get('unit')) if q.get('unit') in m_units else 0
                                    edit_unit = st.selectbox("大單元", m_units, index=curr_u_idx, key=f"ed_unit_{q['id']}")
                                with ec4:
                                    edit_concept = st.text_input("細部考點", value=q.get('concept', ''), key=f"ed_con_{q['id']}")
                                
                                edit_content = st.text_area("題目內容 (LaTeX)", value=q.get('content', ''), height=100, key=f"ed_cnt_{q['id']}")
                                edit_ans = st.text_input("簡答", value=q.get('answer', ''), key=f"ed_ans_{q['id']}")
                                edit_sol = st.text_area("解析 (LaTeX)", value=q.get('solution', ''), height=100, key=f"ed_sol_{q['id']}")
                                
                                if st.form_submit_button("💾 儲存修改"):
                                    q['type'] = edit_type
                                    q['difficulty'] = edit_diff
                                    q['unit'] = edit_unit
                                    q['concept'] = edit_concept.strip()
                                    q['content'] = edit_content.strip()
                                    q['answer'] = edit_ans.strip()
                                    q['solution'] = edit_sol.strip()
                                    with open('questions.json', 'w', encoding='utf-8') as f:
                                        json.dump(questions, f, ensure_ascii=False, indent=2)
                                    st.session_state['db_modified'] = True
                                    st.rerun()

                if is_checked:
                    selected_exam.append(q)
    else:
        max_q = max(1, len(filtered_q))
        num_to_draw = st.number_input("要隨機抽取幾題？", min_value=1, max_value=max_q, value=min(10, max_q))
        if st.button("🎲 立即隨機抽題"):
            st.session_state['random_exam'] = random.sample(filtered_q, num_to_draw)
        selected_exam = st.session_state.get('random_exam', [])

    # ==========================================
    # 匯出區塊：支援一鍵生成 PDF、線上預覽與下載 .tex
    # ==========================================
    if selected_exam:
        st.divider()
        st.subheader(f"🖨️ 步驟 3：匯出考卷（目前已選 {len(selected_exam)} 題）")
        
        teacher_tex = generate_latex(
            selected_exam, exam_title, exam_range, doc_class,
            calc_space=calc_space_slider,
            choice_cols=choice_cols_slider, choice_height=choice_height_slider,
            ans_cols=ans_cols_slider, ans_height=ans_height_slider,
            non_choice_height=nc_height_slider, auto_fit_ans=auto_fit_toggle,
            show_source=show_source_tag, is_teacher=True
        )
        student_tex = generate_latex(
            selected_exam, exam_title, exam_range, doc_class,
            calc_space=calc_space_slider,
            choice_cols=choice_cols_slider, choice_height=choice_height_slider,
            ans_cols=ans_cols_slider, ans_height=ans_height_slider,
            non_choice_height=nc_height_slider, auto_fit_ans=auto_fit_toggle,
            show_source=show_source_tag, is_teacher=False
        )

        if st.button("⚡ 點此直接編譯生成 PDF 考卷（學生卷 + 教用卷）", type="primary", use_container_width=True):
            with st.spinner("⏳ 正在呼叫 XeLaTeX 引擎編譯 PDF 中，請稍候約 3~5 秒..."):
                ok_s, pdf_s, log_s = compile_to_pdf(student_tex)
                ok_t, pdf_t, log_t = compile_to_pdf(teacher_tex)
                if ok_s and ok_t:
                    st.session_state['pdf_student'] = pdf_s
                    st.session_state['pdf_teacher'] = pdf_t
                    st.success("🎉 PDF 編譯成功！可直接於下方線上預覽或點擊下載：")
                else:
                    st.error("⚠️ PDF 編譯失敗，請檢查下方錯誤訊息（若在雲端請確認已建立 packages.txt）：")
                    with st.expander("查看 LaTeX 編譯紀錄 (Log)"):
                        st.text(log_s or log_t)

        if 'pdf_student' in st.session_state and 'pdf_teacher' in st.session_state:
            p_col1, p_col2 = st.columns(2)
            with p_col1:
                st.download_button(
                    label="📕 下載【學生空白卷 PDF】",
                    data=st.session_state['pdf_student'],
                    file_name=f"{exam_title}_學生卷.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            with p_col2:
                st.download_button(
                    label="📘 下載【教師詳解卷 PDF】",
                    data=st.session_state['pdf_teacher'],
                    file_name=f"{exam_title}_教用卷.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

            # 使用 PDF.js 畫布渲染引擎線上直接預覽（解決瀏覽器封鎖 iframe base64 PDF 問題）
            with st.expander("🖥️ 線上直接預覽 PDF 版面（免下載確認）", expanded=True):
                prev_tab1, prev_tab2 = st.tabs(["📕 學生空白卷預覽", "📘 教師詳解卷預覽"])
                with prev_tab1:
                    render_pdf_preview(st.session_state['pdf_student'], height=780)
                with prev_tab2:
                    render_pdf_preview(st.session_state['pdf_teacher'], height=780)

        st.write("或者下載 `.tex` 原始檔至 VS Code 微調：")
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                label="📥 下載【學生卷 .tex 原始檔】",
                data=student_tex,
                file_name="exam_student.tex",
                mime="text/plain",
                use_container_width=True
            )
        with dl_col2:
            st.download_button(
                label="📥 下載【教用卷 .tex 原始檔】",
                data=teacher_tex,
                file_name="exam_teacher.tex",
                mime="text/plain",
                use_container_width=True
            )
            
        with st.expander("👀 預覽生成的 LaTeX 原始碼"):
            sub_t1, sub_t2 = st.tabs(["教用詳解版原始碼", "學生試題卷原始碼"])
            with sub_t1:
                st.code(teacher_tex, language="latex")
            with sub_t2:
                st.code(student_tex, language="latex")

# ==========================================
# 分頁二：單題新增
# ==========================================
with tab2:
    st.subheader("➕ 單題新增至題庫")
    with st.form("add_question_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            new_id = st.text_input("題目編號 (如 113GF_7A_1_01)")
            new_school = st.text_input("學校全稱", value="國風國中")
        with col2:
            new_source = st.text_input("簡短出處", value="113國風")
            new_unit = st.selectbox("核心大單元 (M01~M25)", m_units)
        with col3:
            new_concept = st.text_input("細部考點 (如 負數與數線)")
            new_diff = st.selectbox("學生體感難度", ["基礎", "中等", "進階", "資優"])
            
        new_type = st.selectbox("題型", ["選擇題", "填充題", "非選題"])
        new_content = st.text_area("題目內容 (直接貼上 LaTeX 語法)", height=120)
        new_answer = st.text_input("簡答 (用於填入答案卷表格)")
        new_solution = st.text_area("詳細解析 (直接貼上 LaTeX 語法)", height=120)
        
        if st.form_submit_button("💾 儲存至題庫"):
            if not new_id or not new_concept or not new_content:
                st.error("⚠️ 請填寫完整欄位！")
            else:
                questions.append({
                    "id": new_id.strip(),
                    "school": new_school.strip(),
                    "source": new_source.strip(),
                    "unit": new_unit,
                    "concept": new_concept.strip(),
                    "difficulty": new_diff,
                    "type": new_type,
                    "content": new_content.strip(),
                    "answer": new_answer.strip(),
                    "solution": new_solution.strip()
                })
                with open('questions.json', 'w', encoding='utf-8') as f:
                    json.dump(questions, f, ensure_ascii=False, indent=2)
                st.session_state['db_modified'] = True
                st.success(f"🎉 成功新增題目：{new_id}！")

# ==========================================
# 分頁三：AI 批次匯入與防失憶規格書
# ==========================================
with tab3:
    st.subheader("🤖 步驟 1：複製「AI 轉檔防失憶規格書」")
    ai_prompt_spec = """請幫我將以下的 LaTeX 數學考卷題目，拆解並轉換為 JSON 陣列格式。請嚴格遵守以下所有規則：

1. 每道題目必須包含以下 9 個欄位：
- "id": 格式為 "學年+學校代號_年級學期_段考次_題號"（上學期為A，下學期為B，如七上一段第1題為 "113GF_7A_1_01"）。
- "school": 學校全稱（如 "國風國中"）。
- "source": 簡短出處（如 "113國風"）。
- "unit": 嚴格從以下【M01~M25 核心觀念代碼表】挑選：
  M01 整數的運算 / M02 最大公因數與最小公倍數 / M03 分數的運算 / M04 一元一次方程式 / M05 統計圖表與資料分析 / M06 二元一次聯立方程式 / M07 直角坐標與二元一次方程式的圖形 / M08 比與比例式 / M09 一元一次不等式 / M10 垂直、線對稱與三視圖 / M11 乘法公式與多項式 / M12 平方根與畢氏定理 / M13 因式分解 / M14 一元二次方程式 / M15 統計資料處理 / M16 數列與級數 / M17 函數 / M18 三角形的基本性質 / M19 平行與四邊形 / M20 相似形 / M21 圓形 / M22 幾何與證明 / M23 二次函數 / M24 統計與機率 / M25 生活中的立體圖形
- "concept": 細部考點（請勿重複寫大單元名稱！）。
- "difficulty": 依學生體感難度分為 "基礎"、"中等"、"進階"、"資優" 四級。
- "type": 分為 "選擇題"、"填充題" 或 "非選題"。
- "content": 題目 LaTeX 內容：
  * 若為「選擇題」：不需要加填充底線，題幹與選項間請用 \\\\n 換行，選項間以 \\quad 隔開。
  * 若為「填充題」：所有底線請統一替換為帶有動態題號的格式：\\rule[-2ex]{3cm}{0.4pt}\\raisebox{-0.8ex}{\\makebox[0pt][r]{\\makebox[3cm][c]{\\textbf{(1)}}}}
- "answer": 簡答（選擇題如 "D"，填充題如 "$18x - 27$"）。
- "solution": 詳細解析 LaTeX 內容。

2. LaTeX 轉 JSON 防呆鐵律：
- 所有 LaTeX 指令單斜線 \\ 必須轉義為雙斜線 \\\\。
- 換行請統一使用單斜線 \\n（不可寫成 \\\\n）。
- 嚴格檢查所有 $...$，錢字號內側前後絕對不可有空白，且 \\rule 必須在 $...$ 數學模式之外！"""

    with st.expander("📋 點此展開【AI 轉檔萬用提示詞（含 M01~M25 代碼表）】"):
        st.code(ai_prompt_spec, language="markdown")

    st.divider()
    st.subheader("📥 步驟 2：一鍵自動合併新考卷 JSON")
    pasted_json = st.text_area("請在此貼上新考卷的 JSON 陣列 `[ ... ]`：", height=200)
    
    if st.button("🔄 立即與現有題庫自動合併"):
        try:
            new_items = json.loads(pasted_json)
            if not isinstance(new_items, list):
                st.error("⚠️ 格式錯誤：最外層必須是 `[ ... ]` 陣列！")
            else:
                merged_dict = {q['id']: q for q in questions}
                for item in new_items:
                    merged_dict[item['id']] = item
                merged_list = list(merged_dict.values())
                st.session_state['questions_db'] = merged_list
                st.session_state['db_modified'] = True
                
                with open('questions.json', 'w', encoding='utf-8') as f:
                    json.dump(merged_list, f, ensure_ascii=False, indent=2)
                
                merged_json_str = json.dumps(merged_list, ensure_ascii=False, indent=2)
                st.success(f"🎉 合併成功！共計 **{len(merged_list)}** 題！")
                
                st.download_button(
                    label=f"📥 點此下載合併後的完整 questions.json（共 {len(merged_list)} 題）",
                    data=merged_json_str,
                    file_name="questions.json",
                    mime="application/json",
                    use_container_width=True
                )
                with st.expander("👀 點此複製合併後的完整 questions.json 原始碼（直接貼上 GitHub）", expanded=True):
                    st.code(merged_json_str, language="json")
        except Exception as e:
            st.error(f"⚠️ JSON 解析失敗：{e}")
