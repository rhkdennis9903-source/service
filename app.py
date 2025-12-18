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

# =========================================================
# 0) 基礎設定
# =========================================================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1zXHavJqhOBq1-m_VR7sxMkeOHdXoD9EmQCEM1Nl816I/edit?usp=sharing"

PROVIDER_NAME = "高如慧"
BANK_NAME = "中國信託商業銀行"
BANK_CODE = "822"
ACCOUNT_NUMBER = "783540208870"
REMOTE_SUPPORT_URL = "https://remotedesktop.google.com/support10"
CREATIVES_UPLOAD_URL = "https://metaads-dtwbm3ntmprhjvpv6ptmec.streamlit.app/" # 素材上傳網址

st.set_page_config(page_title="廣告投放服務系統", page_icon="📝", layout="centered")

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

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False

# =========================================================
# 2) 核心邏輯：資料映射 (Mapping)
# =========================================================
# 欄位對應說明 (0-based index from gspread records / 1-based for update_cells)
# ...原有欄位...
# 25 (Z): chk_remote
# 26 (AA): chk_creatives (NEW)

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
    
    row = [
        s("Email"), s("case_id"), s("party_a"), PROVIDER_NAME, s("plan"), 
        str(s("start_date")), s("pay_day"), str(s("pay_date")) if s("pay_date") else "",
        "FALSE", "FALSE", "FALSE", "FALSE", # chk boxes init
        "", "", "", "", "", "", "", "", "", # Phase 2 strings init
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # last_update_at
        "contract", # msg_type
        s("plan"), # plan_raw
        f"{s('case_id')} ({s('party_a')})", # display_label
        "FALSE", # chk_remote (Z欄)
        "FALSE"  # chk_creatives (AA欄) - NEW
    ]
    ws.append_row(row)

def update_phase2(row_num, p2_data):
    """更新：修改指定列的 Phase 2 欄位"""
    ws = get_worksheet()
    
    cells = []
    def Cell(col, val): return gspread.Cell(row_num, col, str(val))

    # Checkboxes (I:9 ~ L:12)
    cells.append(Cell(9, p2_data["chk_ad_account"]))
    cells.append(Cell(10, p2_data["chk_pixel"]))
    cells.append(Cell(11, p2_data["chk_fanpage"]))
    cells.append(Cell(12, p2_data["chk_bm"]))
    
    # Text Fields (M:13 ~ U:21)
    cells.append(Cell(13, p2_data["fanpage_url"]))
    cells.append(Cell(14, p2_data["landing_url"]))
    cells.append(Cell(15, p2_data["comp1"]))
    cells.append(Cell(16, p2_data["comp2"]))
    cells.append(Cell(17, p2_data["comp3"]))
    cells.append(Cell(18, p2_data["who_problem"]))
    cells.append(Cell(19, p2_data["what_problem"]))
    cells.append(Cell(20, p2_data["how_solve"]))
    cells.append(Cell(21, p2_data["budget"]))
    
    # Update Time (V:22)
    cells.append(Cell(22, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    # Remote (Z:26)
    cells.append(Cell(26, p2_data["chk_remote"]))

    # Creatives (AA:27) - NEW
    cells.append(Cell(27, p2_data["chk_creatives"]))

    ws.update_cells(cells)

# =========================================================
# 3) Word 生成 (保持不變)
# =========================================================
def set_run_font(run, size=12, bold=False):
    run.font.name = "Microsoft JhengHei"
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft JhengHei")

def generate_docx_bytes(party_a, email, payment_opt, start_dt, pay_day, pay_dt, case_num):
    doc = Document()
    style = doc.styles["Normal"]
    style.paragraph_format.line_spacing = 1.5
    
    heading = doc.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = heading.add_run("廣告投放服務合約書")
    set_run_font(run, size=18, bold=True)
    
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = sub.add_run(f"案件編號：{case_num}")
    set_run_font(run, size=10)
    doc.add_paragraph("")

    if payment_opt == "17,000元/月（每月付款）":
        end = start_dt + timedelta(days=30)
        period_txt = f"自 {start_dt} 起至 {end} 止，共 1 個月（自動續約）。"
        price_txt = "1. 費用：NT$17,000／月。"
        pay_txt = f"2. 付款時間：每月 {pay_day} 日前。"
    else:
        end = start_dt + timedelta(days=90)
        period_txt = f"自 {start_dt} 起至 {end} 止，共 3 個月。"
        price_txt = "1. 費用：NT$45,000／三個月。"
        pay_txt = f"2. 付款時間：{pay_dt} 前。"

    doc.add_paragraph(f"甲方：{party_a}").runs[0].font.name = "Microsoft JhengHei"
    doc.add_paragraph(f"乙方：{PROVIDER_NAME}").runs[0].font.name = "Microsoft JhengHei"
    doc.add_paragraph("")
    doc.add_paragraph("雙方同意依下列條款進行廣告投放合作：")
    
    items = ["一、合約期間", period_txt, "二、服務內容", "廣告上架、監控優化、簡易週報。", "三、費用", price_txt, pay_txt]
    for i in items:
        p = doc.add_paragraph(i)
        set_run_font(p.runs[0])

    doc.add_paragraph("\n")
    table = doc.add_table(rows=1, cols=2)
    c1 = table.cell(0, 0)
    c1.paragraphs[0].add_run(f"甲方：{party_a}\n信箱：{email}\n\n簽名：__________").font.name = "Microsoft JhengHei"
    c2 = table.cell(0, 1)
    c2.paragraphs[0].add_run(f"乙方：{PROVIDER_NAME}\n\n簽名：__________").font.name = "Microsoft JhengHei"

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.getvalue()

# =========================================================
# 4) 主程式與 Sidebar 邏輯
# =========================================================
if "user" not in st.session_state:
    st.session_state.user = None 

with st.sidebar:
    st.title("系統入口")
    mode = st.radio("模式", ["客戶登入", "新客戶建檔"])
    st.markdown("---")

    if mode == "新客戶建檔":
        reg_name = st.text_input("客戶名稱")
        reg_email = st.text_input("聯絡信箱 (限 Gmail)")
        if st.button("開始建檔"):
            if not reg_name or not reg_email.endswith("@gmail.com"):
                st.error("請輸入名稱且信箱需為 Gmail")
            else:
                row_num, _ = find_user_row(reg_email)
                if row_num:
                    st.error("此信箱已註冊，請直接登入")
                else:
                    st.session_state.user = {"email": reg_email, "name": reg_name, "role": "new"}
                    st.rerun()

    else: # 登入
        login_email = st.text_input("信箱")
        login_pass = st.text_input("密碼", type="password")
        if st.button("登入"):
            if login_pass != "dennis":
                st.error("密碼錯誤")
            else:
                row_num, data = find_user_row(login_email)
                if row_num:
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
                    st.error("找不到資料")

    if st.session_state.user:
        if st.button("登出"):
            st.session_state.user = None
            st.rerun()

# =========================================================
# 5) 頁面顯示邏輯
# =========================================================
if not st.session_state.user:
    st.title("📝 廣告服務系統")
    st.info("👈 請由左側登入或建檔")
    st.stop()

user = st.session_state.user
role = user["role"]
raw = user.get("raw_data", {})

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
    
    def get_val(k, default):
        return raw.get(k, default) if role == "login" else default

    c1, c2 = st.columns(2)
    with c1:
        party_name = st.text_input("客戶名稱", value=user["name"], disabled=True)
    with c2:
        email_disp = st.text_input("信箱", value=user["email"], disabled=True)

    plan_opts = ["17,000元/月（每月付款）", "45,000元/三個月（一次付款）"]
    curr_plan = get_val("plan", plan_opts[0])
    try:
        plan_idx = plan_opts.index(curr_plan)
    except:
        plan_idx = 0
    
    plan = st.radio("方案", plan_opts, index=plan_idx, disabled=(role=="login"))
    
    d_start = datetime.now().date() + timedelta(days=7)
    if role == "login" and raw.get("start_date"):
        try:
            d_start = datetime.strptime(raw["start_date"], "%Y-%m-%d").date()
        except: pass
        
    start_date = st.date_input("啟動日", value=d_start, disabled=(role=="login"))
    
    pay_day = 5
    pay_date = None
    if "每月" in plan:
        pd_val = int(raw.get("pay_day", 5)) if role == "login" else 5
        pay_day = st.slider("付款日", 1, 28, pd_val, disabled=(role=="login"))
    else:
        d_pay = start_date
        if role == "login" and raw.get("pay_date"):
            try:
                d_pay = datetime.strptime(raw["pay_date"], "%Y-%m-%d").date()
            except: pass
        pay_date = st.date_input("付款日期", value=d_pay, disabled=(role=="login"))

    if role == "new":
        if st.button("生成案件並存檔", type="primary"):
            date_str = datetime.now().strftime("%Y%m%d")
            safe_name = "".join([c for c in user["name"] if c.isalnum()]).strip()
            case_id = f"{safe_name}_{date_str}"
            
            data_to_save = {
                "Email": user["email"], "case_id": case_id, "party_a": user["name"],
                "plan": plan, "start_date": start_date, "pay_day": pay_day, "pay_date": pay_date
            }
            
            try:
                save_phase1_new(data_to_save)
                body = f"新客戶建檔完成：\n名稱：{user['name']}\n案件號：{case_id}\n方案：{plan}"
                send_email(f"【新案件】{user['name']} 已建檔", body)
                st.success(f"建檔成功！案件號：{case_id}")
                st.info("請重新登入以進入第二階段")
            except Exception as e:
                st.error(f"存檔失敗: {e}")

    if role == "login":
        st.info(f"案件號：{raw.get('case_id')}")
        if st.button("下載合約 Word"):
            docx = generate_docx_bytes(
                user["name"], user["email"], plan, 
                start_date, pay_day, pay_date, raw.get("case_id")
            )
            st.download_button("⬇️ 下載合約", docx, f"合約_{raw.get('case_id')}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

# -----------------
# 第二階段
# -----------------
elif nav == "第二階段｜啟動前確認":
    st.header("第二階段｜啟動資料")
    st.caption("填寫完畢請按下方「更新資料」")
    
    def b(k): return str(raw.get(k, "FALSE")).upper() == "TRUE"
    def s(k): return raw.get(k, "")

    # 第一列確認事項
    c1, c2 = st.columns(2)
    with c1:
        ad = st.checkbox("廣告帳號 OK", value=b("chk_ad_account"))
        px = st.checkbox("像素 OK", value=b("chk_pixel"))
    with c2:
        fp = st.checkbox("粉專 OK", value=b("chk_fanpage"))
        bm = st.checkbox("BM OK", value=b("chk_bm"))

    st.markdown("---")
    # 遠端 與 素材 (特殊項目)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**1. 遠端設定**")
        rem = st.checkbox("遠端桌面設定 OK", value=b("chk_remote"))
        st.caption(f"[教學連結]({REMOTE_SUPPORT_URL})")
    
    with c4:
        st.markdown("**2. 素材上傳**")
        # NEW: 素材上傳 checkbox
        creatives_done = st.checkbox("已前往上傳素材", value=b("chk_creatives"))
        st.caption(f"[點擊前往上傳系統]({CREATIVES_UPLOAD_URL})")

    st.markdown("---")
    
    fp_url = st.text_input("粉專連結", value=s("fanpage_url"))
    ld_url = st.text_input("導向頁連結", value=s("landing_url"))
    
    st.markdown("### 競品")
    cp1 = st.text_input("競品1", value=s("comp1"))
    cp2 = st.text_input("競品2", value=s("comp2"))
    cp3 = st.text_input("競品3", value=s("comp3"))
    
    st.markdown("### 定位")
    who = st.text_area("對象", value=s("who_problem"))
    what = st.text_area("問題", value=s("what_problem"))
    how = st.text_area("解法", value=s("how_solve"))
    bud = st.text_input("預算", value=s("budget"))
    
    if st.button("💾 更新資料並通知", type="primary"):
        p2_payload = {
            "chk_ad_account": ad, "chk_pixel": px, "chk_fanpage": fp, "chk_bm": bm,
            "chk_remote": rem,
            "chk_creatives": creatives_done, # NEW
            "fanpage_url": fp_url, "landing_url": ld_url,
            "comp1": cp1, "comp2": cp2, "comp3": cp3,
            "who_problem": who, "what_problem": what, "how_solve": how,
            "budget": bud
        }
        
        try:
            update_phase2(user["row_num"], p2_payload)
            
            body = f"""客戶 {user['name']} 更新了第二階段資料：
- 案件號：{raw.get('case_id')}
- 遠端桌面：{'OK' if rem else '未完成'}
- 素材上傳：{'OK' if creatives_done else '未完成'}
- 粉專連結：{fp_url}
- 預算：{bud}

詳細內容請見 Google Sheet。
"""
            send_email(f"【更新】{user['name']} 第二階段資料", body)
            st.success("更新成功！已發送通知。")
            st.rerun()
            
        except Exception as e:
            st.error(f"更新失敗: {e}")
