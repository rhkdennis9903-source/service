import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta, date
import io
import smtplib
from email.mime.text import MIMEText
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
import time

# =========================================================
# 0) 基礎設定
# =========================================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1zXHavJqhOBq1-m_VR7sxMkeOHdXoD9EmQCEM1Nl816I/edit?usp=sharing"

PROVIDER_NAME = "高如慧"
BANK_NAME = "中國信託商業銀行"
BANK_CODE = "822"
ACCOUNT_NUMBER = "783540208870"
REMOTE_SUPPORT_URL = "https://remotedesktop.google.com/support10"
CREATIVES_UPLOAD_URL = "https://metaads-dtwbm3ntmprhjvpv6ptmec.streamlit.app/" 
BM_TUTORIAL_URL = "https://www.youtube.com/watch?v=你的影片ID" 

st.set_page_config(
    page_title="廣告投放服務｜合約＋啟動資料收集",
    page_icon="📝",
    layout="centered"
)

# =========================================================
# 1) 工具函式：Sheet 連線與資料處理
# =========================================================
@st.cache_resource
def get_gsheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client

def get_worksheet():
    client = get_gsheet_client()
    sheet = client.open_by_url(SHEET_URL)
    return sheet.get_worksheet(0)

def send_email(subject, body):
    """寄送通知信給管理員"""
    try:
        sender = st.secrets["email"]["sender_email"]
        password = st.secrets["email"]["sender_password"]
        receiver = st.secrets["email"]["receiver_email"]

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = receiver

        # 使用 SSL 連線 (Port 465)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email 發送失敗 (請截圖給管理員): {e}")
        return False

# =========================================================
# 2) 核心邏輯：資料映射 (Mapping)
# =========================================================
def find_user_row(email):
    """回傳 (row_index, row_data_dict) 或 (None, None)"""
    ws = get_worksheet()
    records = ws.get_all_records()
    for i, record in enumerate(records):
        if record.get("Email") == email:
            return i + 2, record
    return None, None

def save_phase1_new(data_dict):
    """建檔：新增一列"""
    ws = get_worksheet()
    def s(key): return data_dict.get(key, "")
    
    default_password = "dennis"

    row = [
        s("Email"), s("case_id"), s("party_a"), PROVIDER_NAME, s("plan"), 
        str(s("start_date")), s("pay_day"), str(s("pay_date")) if s("pay_date") else "",
        "FALSE", "FALSE", "FALSE", "FALSE", # chk boxes init
        "", "", "", "", "", "", "", "", "", # Phase 2 strings init
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # last_update_at
        "contract", # msg_type
        s("plan"), # plan_raw
        f"{s('case_id')} ({s('party_a')})", # display_label
        "FALSE", # chk_remote
        "FALSE", # chk_creatives
        default_password # password
    ]
    ws.append_row(row)

def update_phase2(row_num, p2_data):
    """更新：修改指定列的 Phase 2 欄位"""
    ws = get_worksheet()
    
    cells = []
    def Cell(col, val): return gspread.Cell(row_num, col, str(val))

    cells.append(Cell(9, p2_data["chk_ad_account"]))
    cells.append(Cell(10, p2_data["chk_pixel"]))
    cells.append(Cell(11, p2_data["chk_fanpage"]))
    cells.append(Cell(12, p2_data["chk_bm"]))
    
    cells.append(Cell(13, p2_data["fanpage_url"]))
    cells.append(Cell(14, p2_data["landing_url"]))
    cells.append(Cell(15, p2_data["comp1"]))
    cells.append(Cell(16, p2_data["comp2"]))
    cells.append(Cell(17, p2_data["comp3"]))
    cells.append(Cell(18, p2_data["who_problem"]))
    cells.append(Cell(19, p2_data["what_problem"]))
    cells.append(Cell(20, p2_data["how_solve"]))
    cells.append(Cell(21, p2_data["budget"]))
    
    cells.append(Cell(22, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    cells.append(Cell(26, p2_data["chk_remote"]))
    cells.append(Cell(27, p2_data["chk_creatives"]))

    ws.update_cells(cells)

def update_password(row_num, new_password):
    """更新密碼"""
    ws = get_worksheet()
    ws.update_cell(row_num, 28, new_password)

# =========================================================
# 3) Word 生成 (詳細版內容 + 窄邊界優化)
# =========================================================
def set_run_font(run, size=10.5, bold=False):
    run.font.name = "Microsoft JhengHei"
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft JhengHei")

def generate_docx_bytes(party_a, email, payment_opt, start_dt, pay_day, pay_dt, case_num):
    doc = Document()
    
    # 版面設定：窄邊界
    section = doc.sections[0]
    section.top_margin = Cm(1.27)
    section.bottom_margin = Cm(1.27)
    section.left_margin = Cm(1.27)
    section.right_margin = Cm(1.27)

    style = doc.styles['Normal']
    style.paragraph_format.line_spacing = 1.15
    style.paragraph_format.space_after = Pt(2)

    # --- 標題 ---
    heading = doc.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = heading.add_run("廣告投放服務合約書")
    set_run_font(run, size=16, bold=True)
    
    if case_num:
        sub_head = doc.add_paragraph()
        sub_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_sub = sub_head.add_run(f"案件編號：{case_num}")
        set_run_font(run_sub, size=9)
    doc.add_paragraph("")

    # --- 變數邏輯 ---
    if payment_opt == "17,000元/月（每月付款）":
        end_dt = start_dt + timedelta(days=30)
        period_text = (
            f"自 {start_dt.strftime('%Y 年 %m 月 %d 日')} 起至 {end_dt.strftime('%Y 年 %m 月 %d 日')} 止，共 1 個月。"
            "届期如雙方無異議，則本合約自動續行 1 個月，以此類推。"
        )
        price_text = "1. 甲方同意支付乙方服務費用 新台幣壹萬柒仟元整（NT$17,000）／月。"
        pay_time_text = f"2. 付款時間：甲方應於每月 {pay_day} 日前支付當月服務費用至乙方指定帳戶。"
        first_pay_text = f"3. 首期款項應於合作啟動日（{start_dt.strftime('%Y 年 %m 月 %d 日')}）前支付完成。"
        refund_text = "2. 月付方案：已支付之當期費用不予退還。"
    else:
        end_dt = start_dt + timedelta(days=90)
        period_text = (
            f"自 {start_dt.strftime('%Y 年 %m 月 %d 日')} 起至 {end_dt.strftime('%Y 年 %m 月 %d 日')} 止，共 3 個月。"
            "届期如雙方有意續約，應於届滿前 7 日另行協議。"
        )
        price_text = "1. 甲方同意支付乙方服務費用 新台幣肆萬伍仟元整（NT$45,000）／三個月。"
        pay_time_text = f"2. 付款時間：甲方應於 {pay_dt.strftime('%Y 年 %m 月 %d 日')} 前一次支付完成。"
        first_pay_text = None
        refund_text = (
            "2. 季付方案屬優惠性質之預付服務費，一經支付後即不予退還。"
            "即使甲方於合約期間內提前終止或未使用完畢服務內容，亦同；"
            "惟因乙方重大違約致服務無法履行者，不在此限。"
        )

    # --- 立約人 ---
    p = doc.add_paragraph()
    run = p.add_run(f"甲方（委託暨付款方）：{party_a}\n")
    set_run_font(run, bold=True)
    run = p.add_run(f"乙方（服務執行者）：{PROVIDER_NAME}")
    set_run_font(run, bold=True)
    
    p = doc.add_paragraph()
    run = p.add_run("茲因甲方委託乙方提供數位廣告投放服務，雙方本於誠信原則，同意訂立本合約，並共同遵守下列條款：")
    set_run_font(run)

    def add_clause(title, contents):
        p_title = doc.add_paragraph()
        run_title = p_title.add_run(title)
        set_run_font(run_title, bold=True)
        for content in contents:
            if content:
                p_item = doc.add_paragraph()
                p_item.paragraph_format.left_indent = Cm(0.75)
                run_item = p_item.add_run(content)
                set_run_font(run_item)

    # --- 條款 ---
    add_clause("第一條　合約期間", [period_text])

    p = doc.add_paragraph()
    run = p.add_run("第二條　服務內容")
    set_run_font(run, bold=True)
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.75)
    run = p.add_run("一、固定工作項目")
    set_run_font(run, bold=True)
    items_fixed = [
        "1. 廣告上架：依甲方需求於指定平台建立並上架廣告活動。",
        "2. 廣告監控／維護／優化：定期監控成效數據，進行必要之調整與優化。",
        "3. 簡易週報：每週提供廣告成效摘要及下週優化方向。"
    ]
    for item in items_fixed:
        p = doc.add_paragraph(item)
        p.paragraph_format.left_indent = Cm(1.5)
        set_run_font(p.runs[0])

    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(0.75)
    run = p.add_run("二、非固定工作項目（視實際狀況提供）")
    set_run_font(run, bold=True)
    items_non = [
        "1. 廣告文案與素材優化：本服務雖以投放操作為主，惟視整體成效需求，乙方得主動提出文案修改建議（如：提供不同版本文案供甲方選擇或修訂）。",
        "2. 網頁調整建議：為確保廣告宣傳訴求一致並協助達成成效，乙方得針對廣告到達頁面（Landing Page）提供調整建議。"
    ]
    for item in items_non:
        p = doc.add_paragraph(item)
        p.paragraph_format.left_indent = Cm(1.5)
        set_run_font(p.runs[0])

    add_clause("第三條　服務範圍與限制", [
        "1. 本服務範圍以 Meta（Facebook／Instagram）廣告投放為主；若需擴展至其他平台，雙方另行協議。",
        "2. 廣告投放預算由甲方自行支付予廣告平台，不包含於本合約服務費用內。",
        "3. 廣告素材（圖片、影片等）之製作原則上由甲方提供，乙方提供方向與建議。",
        "4. 甲方應提供必要帳號權限、素材與資訊，以確保服務得以順利執行。"
    ])
    add_clause("第四條　配合事項與作業方式", [
        "1. 甲方同意配合乙方所需之資料提供、權限設定與必要操作，以確保服務品質。",
        "2. 若因平台政策、帳號狀況或其他不可控因素需採替代作業方式（例如：由甲方匯出報表供乙方監控），甲方同意合理配合。"
    ])
    add_clause("第五條　費用與付款方式", [
        price_text,
        pay_time_text,
        first_pay_text,
        "4. 逾期付款者，乙方得暫停服務至款項付清為止；因此造成之廣告中斷或成效波動，乙方不負賠償責任。"
    ])
    
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Cm(1.5)
    run = p.add_run(f"乙方指定收款帳戶：\n銀行：{BANK_NAME}（{BANK_CODE}）\n帳號：{ACCOUNT_NUMBER}")
    set_run_font(run)

    add_clause("第六條　付款方式與稅務責任", [
        "1. 乙方為自然人，依法無須開立統一發票。",
        "2. 本合約費用之付款方式、帳務處理及相關稅務申報，均由甲方依其自身狀況及相關法令自行決定並負責。",
        "3. 甲方得依其帳務或實務需求，選擇是否以勞務報酬方式支付或其他合法方式付款；乙方將於合理需求下配合提供必要之收款或服務文件。",
        "4. 乙方不負責判斷、建議或保證任何稅務處理方式之合法性。"
    ])
    add_clause("第七條　成效聲明與免責", [
        "1. 乙方將盡專業所能優化廣告成效，但投放成效受市場環境、競爭狀況、消費者行為、平台演算法等多重因素影響，乙方不保證特定之轉換率、ROAS 或銷售成果。",
        "2. 因平台政策變更、帳號異常、不可抗力因素等非乙方可控原因導致之廣告中斷或成效下降，乙方不負賠償責任。",
        "3. 甲方提供之素材、商品或服務如違反平台政策或法令規定，導致廣告被拒絕或帳號受處分，乙方不負相關責任。"
    ])
    add_clause("第八條　保密條款", [
        "1. 合作期間所涉及之商業資訊、廣告數據、行銷策略及客戶資料等，均屬機密資訊，僅得用於本合作目的。",
        "2. 本保密義務於合約終止後仍持續有效 2 年。"
    ])
    add_clause("第九條　智慧財產權", [
        "1. 乙方提供之廣告文案、策略建議、報告等成果，甲方於付清全部款項後，得於本案範圍內使用。",
        "2. 甲方提供之品牌素材、商標、圖片等，其權利仍歸甲方所有。"
    ])
    add_clause("第十條　合約終止", [
        "1. 任一方如欲提前終止本合約，應於終止日前 14 日以書面（含電子郵件、通訊軟體訊息）通知他方。",
        refund_text,
        "3. 如因一方重大違約致他方權益受損，受損方得立即終止合約並請求損害賠償。"
    ])
    add_clause("第十一條　通知方式", ["本合約相關通知，得以電子郵件、LINE、Messenger 或其他雙方約定之通訊方式為之，於發送時即生效力。"])
    add_clause("第十二條　合約變更", ["本合約之任何修改或補充，應經雙方書面同意後始生效力。"])
    add_clause("第十三條　不可抗力", ["因天災、戰爭、政府行為、網路中斷、平台系統異常或其他不可抗力因素，致任一方無法履行本合約義務時，該方不負違約責任；惟應儘速通知並於事由消滅後恢復履行。"])
    add_clause("第十四條　爭議處理", ["本合約之解釋與適用，以中華民國法律為準據法。雙方如有爭議，應先行協商；協商不成以臺灣臺北地方法院為第一審管轄法院。"])

    doc.add_paragraph("")
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    c1 = table.cell(0, 0)
    p = c1.paragraphs[0]
    run = p.add_run(f"甲方（委託暨付款方）：\n{party_a}\n信箱：{email}\n\n簽名：___________________\n\n日期：_____ 年 ___ 月 ___ 日")
    set_run_font(run)

    c2 = table.cell(0, 1)
    p = c2.paragraphs[0]
    run = p.add_run(f"乙方（服務執行者）：\n{PROVIDER_NAME}\n\n簽名：___________________\n\n日期：_____ 年 ___ 月 ___ 日")
    set_run_font(run)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# =========================================================
# 4) 主程式與 Sidebar 邏輯
# =========================================================
if "user" not in st.session_state:
    st.session_state.user = None 

# 用於顯示成功訊息的 Flag
if "phase1_success_msg" not in st.session_state:
    st.session_state.phase1_success_msg = None
if "phase2_success_msg" not in st.session_state:
    st.session_state.phase2_success_msg = None

with st.sidebar:
    st.title("系統入口")

    if st.session_state.user:
        st.success(f"🟢 已登入：{st.session_state.user['name']}")
        
        with st.expander("🔑 修改密碼"):
            new_pw = st.text_input("新密碼", type="password", key="new_pw_input")
            if st.button("確認修改"):
                if len(new_pw) < 4:
                    st.error("密碼太短")
                elif st.session_state.user.get("row_num"):
                    try:
                        update_password(st.session_state.user["row_num"], new_pw)
                        st.success("修改成功！")
                    except Exception as e:
                        st.error(f"錯誤: {e}")
        
        st.markdown("---")
        if st.button("登出系統"):
            st.session_state.user = None
            st.rerun()

    else:
        mode = st.radio("模式", ["客戶登入", "新客戶建檔"])
        st.markdown("---")

        if mode == "新客戶建檔":
            reg_name = st.text_input("客戶名稱")
            reg_email = st.text_input("聯絡信箱 (限 Gmail)")
            if st.button("開始建檔"):
                if not reg_name or not reg_email.endswith("@gmail.com"):
                    st.error("格式錯誤：請輸入名稱且信箱必須是 Gmail")
                else:
                    row_num, _ = find_user_row(reg_email)
                    if row_num:
                        st.error("此信箱已註冊，請直接登入 (預設密碼: dennis)")
                    else:
                        st.session_state.user = {"email": reg_email, "name": reg_name, "role": "new"}
                        st.rerun()

        else: # 登入
            with st.form("login_form"):
                login_email = st.text_input("信箱")
                login_pass = st.text_input("密碼", type="password")
                submit = st.form_submit_button("登入")
                
                if submit:
                    row_num, data = find_user_row(login_email)
                    if not row_num:
                        st.error("找不到此信箱")
                    else:
                        db_pass = str(data.get("password", "")).strip()
                        if not db_pass: db_pass = "dennis"
                        
                        if login_pass == db_pass:
                            st.session_state.user = {
                                "email": data["Email"], 
                                "name": data["party_a"], 
                                "role": "login",
                                "row_num": row_num,
                                "raw_data": data
                            }
                            st.success("登入成功")
                            st.rerun()
                        else:
                            st.error("密碼錯誤")

# =========================================================
# 5) 頁面顯示邏輯
# =========================================================
if not st.session_state.user:
    st.title("📝 廣告投放服務｜合約＋啟動資料收集")
    st.caption("✅ Word 合約產出（下載後自行另存 PDF）＋ 第二階段啟動資料（可備份／還原）")
    st.markdown("---")
    st.info("👈 請由左側登入或建檔 (預設密碼: dennis)")
    st.stop()

# 取得 User 資料
user = st.session_state.user
role = user["role"]
raw = user.get("raw_data", {})

st.title("📝 廣告投放服務系統")
st.markdown(f"**目前使用者：{user['name']} ({user['email']})**")
st.markdown("---")

nav_options = ["第一階段｜合約"]
if role == "login":
    nav_options.append("第二階段｜啟動前確認")
nav = st.radio("流程：", nav_options, horizontal=True)
st.markdown("---")

# -----------------
# 第一階段
# -----------------
if nav == "第一階段｜合約":
    st.header(f"第一階段 ({'檢視模式' if role == 'login' else '建檔模式'})")
    
    # 成功訊息顯示區 (保留供客戶複製)
    if st.session_state.phase1_success_msg:
        st.success("✅ 建檔成功！請複製以下訊息：")
        st.code(st.session_state.phase1_success_msg)
        st.markdown("---")

    st.info("""
    💡 **第一階段操作流程**：
    1. **詳閱服務內容**：確認雙方權利義務與工作範圍。
    2. **選擇付款方案**：選擇月繳或季繳，並設定合作日期。
    3. **生成案件編號**：(新客戶) 輸入甲方名稱與信箱後，先點擊生成案件編號。
    4. **生成正式合約**：自動產出 Word 檔（含編號與信箱）。
    5. **確認與傳送**：下載合約後，請複製底部的「確認訊息」回傳給乙方。
    """)

    st.subheader("✅ 固定工作")
    st.markdown("""
- **廣告上架**
- **廣告監控 / 維護 / 優化**
- **簡易週報**（成果摘要、下週優化方向）
""")

    st.subheader("📌 非固定工作（視狀況提供）")
    st.markdown("""
- **廣告文案與素材優化**
  - 本合作雖以廣告投放為主，但若判斷整體成效有需求，我會主動提出**文案修改建議**（我會給出幾個版本讓你選和修改）。
- **網頁調整建議**
  - 為了符合宣傳訴求與達成成效，我會視情況提供網頁的**具體調整建議**。
""")

    st.info("""
現況提醒：目前我的 FB 個人帳號仍然被停用，但我仍需要每天監控你的廣告成果。
因此我會先教你怎麼每天匯出我需要的數據（我會幫你設定好，你每天按一次匯出就可以）。
若需要調整後台，我會先和你約時間，透過遠端連線由我直接操作你的電腦來調整廣告後台設定；
遠端前我會先準備好完整調整規劃，實際連線操作會非常快。
""")

    st.warning("📌 稅務提醒：乙方為自然人，無須開立發票。甲方自行處理勞報或相關稅務。")
    st.markdown("---")

    # 表單區
    def get_val(k, default):
        return raw.get(k, default) if role == "login" else default

    c1, c2 = st.columns(2)
    with c1:
        party_name = st.text_input("甲方名稱（公司或個人）", value=user["name"], disabled=True)
    with c2:
        email_disp = st.text_input("甲方聯絡信箱", value=user["email"], disabled=True)

    plan_opts = ["17,000元/月（每月付款）", "45,000元/三個月（一次付款）"]
    curr_plan = get_val("plan", plan_opts[0])
    try:
        plan_idx = plan_opts.index(curr_plan)
    except:
        plan_idx = 0
    
    st.subheader("💰 付款方案")
    plan = st.radio("方案選擇：", plan_opts, index=plan_idx, disabled=(role=="login"))
    
    st.subheader("📅 時間設定")
    d_start = datetime.now().date() + timedelta(days=7)
    if role == "login" and raw.get("start_date"):
        try:
            d_start = datetime.strptime(raw["start_date"], "%Y-%m-%d").date()
        except: pass
        
    start_date = st.date_input("合作啟動日", value=d_start, disabled=(role=="login"))
    
    pay_day = 5
    pay_date = None
    if "每月" in plan:
        pd_val = int(raw.get("pay_day", 5)) if role == "login" else 5
        pay_day = st.slider("每月付款日", 1, 28, pd_val, disabled=(role=="login"))
    else:
        d_pay = start_date
        if role == "login" and raw.get("pay_date"):
            try:
                d_pay = datetime.strptime(raw["pay_date"], "%Y-%m-%d").date()
            except: pass
        pay_date = st.date_input("付款日期", value=d_pay, disabled=(role=="login"))

    # 生成按鈕
    if role == "new":
        if st.button("🎲 生成案件編號並存檔", type="primary"):
            with st.spinner("資料建立中，並同步發送通知信..."):
                date_str = datetime.now().strftime("%Y%m%d")
                safe_name = "".join([c for c in user["name"] if c.isalnum()]).strip()
                case_id = f"{safe_name}_{date_str}"
                
                data_to_save = {
                    "Email": user["email"], "case_id": case_id, "party_a": user["name"],
                    "plan": plan, "start_date": start_date, "pay_day": pay_day, "pay_date": pay_date
                }
                
                try:
                    save_phase1_new(data_to_save)
                    
                    # 寄信
                    body_email = f"新客戶建檔完成：\n名稱：{user['name']}\n案件號：{case_id}\n方案：{plan}"
                    send_email(f"【新案件】{user['name']} 已建檔", body_email)
                    
                    # 準備 LINE 訊息 (放入 Session)
                    msg_line = f"""【合約確認】
案件編號：{case_id}
甲方：{user['name']}
信箱：{user['email']}
乙方：{PROVIDER_NAME}
方案：{plan}
啟動：{start_date}"""
                    st.session_state.phase1_success_msg = msg_line
                    st.rerun()

                except Exception as e:
                    st.error(f"存檔失敗: {e}")

    if role == "login":
        st.info(f"案件編號：{raw.get('case_id')}")
        if st.button("📝 生成 Word 合約"):
            docx = generate_docx_bytes(
                user["name"], user["email"], plan, 
                start_date, pay_day, pay_date, raw.get("case_id")
            )
            st.download_button("⬇️ 下載 Word 合約 (.docx)", docx, f"合約_{raw.get('case_id')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# -----------------
# 第二階段
# -----------------
elif nav == "第二階段｜啟動前確認":
    st.header("第二階段｜啟動資料")
    
    # 成功訊息顯示區
    if st.session_state.phase2_success_msg:
        st.success("✅ 更新成功！請複製以下訊息回傳：")
        st.code(st.session_state.phase2_success_msg)
        st.balloons()
        # 清除訊息以免下次進來還在，但因為是 rerun 後顯示，這次會留著
        st.session_state.phase2_success_msg = None 

    st.info("""
    💡 **第二階段操作流程**：
    1. **確認基本資料**：確保上方案件編號與信箱正確。
    2. **確認資產現況**：勾選您目前的廣告帳號、粉專等設定狀態。
    3. **填寫行銷情報**：輸入粉專連結、競品資訊以及簡單的市場定位（受眾/痛點）。
    4. **更新並通知**：填寫完畢後，點擊最下方的「更新資料並通知」。
    """)

    st.info("""
    **現況提醒（合作方式）**：
    1) **每日監控**：我會幫你設定數據匯出，你每天按一次即可。
    2) **調整優化**：透過遠端連線 (Google Remote Desktop) 操作你的電腦調整後台。
    3) **效率**：遠端前我會準備好，操作會非常快。
    """)
    
    def b(k): return str(raw.get(k, "FALSE")).upper() == "TRUE"
    def s(k): return raw.get(k, "")

    # 教學影片
    if BM_TUTORIAL_URL.strip():
        with st.expander("📺 [教學影片] 如何設定企業管理平台 (BM)？"):
            st.video(BM_TUTORIAL_URL)

    # 第一列確認事項
    st.subheader("✅ 確認事項（照實勾選）")
    c1, c2 = st.columns(2)
    with c1:
        ad = st.checkbox("廣告帳號已開啟", value=b("chk_ad_account"))
        px = st.checkbox("像素事件已埋放", value=b("chk_pixel"))
    with c2:
        fp = st.checkbox("粉專已建立", value=b("chk_fanpage"))
        bm = st.checkbox("企業管理平台已建立", value=b("chk_bm"))

    st.markdown("---")
    # 遠端 與 素材
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**1. 遠端設定**")
        rem = st.checkbox("已完成 Google 遠端桌面設定", value=b("chk_remote"))
        st.caption(f"[教學連結]({REMOTE_SUPPORT_URL})")
    
    with c4:
        st.markdown("**2. 素材上傳**")
        creatives_done = st.checkbox("已前往上傳素材", value=b("chk_creatives"))
        st.caption(f"[點擊前往上傳系統]({CREATIVES_UPLOAD_URL})")

    st.markdown("---")
    
    st.subheader("🧾 須提供事項")
    fp_url = st.text_input("粉專網址", value=s("fanpage_url"))
    ld_url = st.text_input("廣告導向頁", value=s("landing_url"))
    
    st.subheader("競爭對手粉專")
    cp1 = st.text_input("競品 1", value=s("comp1"))
    cp2 = st.text_input("競品 2", value=s("comp2"))
    cp3 = st.text_input("競品 3", value=s("comp3"))
    
    st.subheader("定位與預算")
    who = st.text_area("解決誰的問題？", value=s("who_problem"))
    what = st.text_area("要解決什麼問題？", value=s("what_problem"))
    how = st.text_area("如何解決？", value=s("how_solve"))
    bud = st.text_input("第一個月預算", value=s("budget"))
    
    if st.button("💾 更新資料並通知", type="primary"):
        with st.spinner("⏳ 資料同步中，並發送 Email 通知信..."):
            p2_payload = {
                "chk_ad_account": ad, "chk_pixel": px, "chk_fanpage": fp, "chk_bm": bm,
                "chk_remote": rem,
                "chk_creatives": creatives_done,
                "fanpage_url": fp_url, "landing_url": ld_url,
                "comp1": cp1, "comp2": cp2, "comp3": cp3,
                "who_problem": who, "what_problem": what, "how_solve": how,
                "budget": bud
            }
            
            try:
                update_phase2(user["row_num"], p2_payload)
                
                body_email = f"""客戶 {user['name']} 更新了第二階段資料：
- 案件號：{raw.get('case_id')}
- 遠端桌面：{'OK' if rem else '未完成'}
- 素材上傳：{'OK' if creatives_done else '未完成'}
- 粉專連結：{fp_url}
- 預算：{bud}

詳細內容請見 Google Sheet。
"""
                send_email(f"【更新】{user['name']} 第二階段資料", body_email)
                
                # 準備 LINE 訊息 (放入 Session)
                msg_line = f"""【資料更新】
案件編號：{raw.get('case_id')}
信箱：{user['email']}
--
遠端桌面：{'OK' if rem else '未完成'}
素材上傳：{'OK' if creatives_done else '未完成'}
粉專網址：{fp_url}
預算：{bud}
"""
                st.session_state.phase2_success_msg = msg_line
                st.rerun()
                
            except Exception as e:
                st.error(f"更新失敗: {e}")
