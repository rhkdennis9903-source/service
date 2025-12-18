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
import hashlib

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
# 1) 安全與工具函式
# =========================================================
def make_hash(password):
    """SHA-256 雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(input_pw, db_pw):
    """支援明碼與雜湊相容驗證"""
    if len(db_pw) == 64:
        return make_hash(input_pw) == db_pw
    return input_pw == db_pw

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
    """寄送通知信給 rhk9903@gmail.com"""
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
        st.error(f"Email 發送失敗: {e}")
        return False

# =========================================================
# 2) 資料讀寫邏輯
# =========================================================
def find_user_row(email):
    ws = get_worksheet()
    records = ws.get_all_records()
    for i, record in enumerate(records):
        if record.get("Email") == email:
            return i + 2, record
    return None, None

def save_phase1_new(data_dict):
    ws = get_worksheet()
    def s(key): return data_dict.get(key, "")
    hashed_default = make_hash("dennis")
    row = [
        s("Email"), s("case_id"), s("party_a"), PROVIDER_NAME, s("plan"), 
        str(s("start_date")), s("pay_day"), str(s("pay_date")) if s("pay_date") else "",
        "FALSE", "FALSE", "FALSE", "FALSE", 
        "", "", "", "", "", "", "", "", "", 
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        "contract", s("plan"), f"{s('case_id')} ({s('party_a')})", 
        "FALSE", "FALSE", hashed_default
    ]
    ws.append_row(row)

def update_phase2(row_num, p2_data):
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

def update_password(row_num, new_pw):
    ws = get_worksheet()
    ws.update_cell(row_num, 28, make_hash(new_pw))

# =========================================================
# 3) Word 合約生成 (精確還原 14 條款 + 服務細節)
# =========================================================
def set_run_font(run, size=10.5, bold=False):
    run.font.name = "Microsoft JhengHei"
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft JhengHei")

def generate_docx_bytes(party_a, email, payment_opt, start_dt, pay_day, pay_dt, case_num):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Cm(1.27); section.bottom_margin = Cm(1.27)
    section.left_margin = Cm(1.27); section.right_margin = Cm(1.27)
    style = doc.styles['Normal']
    style.paragraph_format.line_spacing = 1.15
    style.paragraph_format.space_after = Pt(2)

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

    if payment_opt == "17,000元/月（每月付款）":
        end_dt = start_dt + timedelta(days=30)
        period_text = f"自 {start_dt.strftime('%Y 年 %m 月 %d 日')} 起至 {end_dt.strftime('%Y 年 %m 月 %d 日')} 止，共 1 個月。届期自動續行。"
        price_text = "1. 甲方同意支付乙方服務費用 新台幣壹萬柒仟元整（NT$17,000）／月。"
        pay_time_text = f"2. 付款時間：甲方應於每月 {pay_day} 日前支付當月服務費用。"
        first_pay_text = f"3. 首期款項應於啟動日（{start_dt.strftime('%Y 年 %m 月 %d 日')}）前支付。"
        refund_text = "2. 月付方案：已支付之當期費用不予退還。"
    else:
        end_dt = start_dt + timedelta(days=90)
        period_text = f"自 {start_dt.strftime('%Y 年 %m 月 %d 日')} 起至 {end_dt.strftime('%Y 年 %m 月 %d 日')} 止，共 3 個月。"
        price_text = "1. 甲方同意支付乙方服務費用 新台幣肆萬伍仟元整（NT$45,000）／三個月。"
        pay_time_text = f"2. 付款時間：甲方應於 {pay_dt.strftime('%Y 年 %m 月 %d 日')} 前一次支付完成。"
        first_pay_text = None
        refund_text = "2. 季付方案屬優惠預付，一經支付後即不予退還。"

    p = doc.add_paragraph()
    run = p.add_run(f"甲方（委託方）：{party_a}  /  乙方（執行方）：{PROVIDER_NAME}")
    set_run_font(run, bold=True)
    doc.add_paragraph("茲因甲方委託乙方提供數位廣告投放服務，雙方本於誠信原則，同意遵守下列條款：").runs[0].font.name = "Microsoft JhengHei"

    def add_cl(title, contents):
        p_t = doc.add_paragraph(); r_t = p_t.add_run(title); set_run_font(r_t, bold=True)
        for c in contents:
            if c:
                p_i = doc.add_paragraph(); p_i.paragraph_format.left_indent = Cm(0.75)
                r_i = p_i.add_run(c); set_run_font(r_i)

    add_cl("第一條　合約期間", [period_text])
    
    # 第二條：服務內容
    p = doc.add_paragraph(); r = p.add_run("第二條　服務內容"); set_run_font(r, bold=True)
    p = doc.add_paragraph("乙方提供以下服務：").runs[0].font.name = "Microsoft JhengHei"
    add_cl("一、固定工作項目", ["1. 廣告上架 2. 監控/維護/優化 3. 簡易週報。"])
    add_cl("二、非固定工作項目", ["1. 文案與素材優化建議 2. 到達網頁調整建議。"])

    add_cl("第三條　服務範圍與限制", ["1. Meta (FB/IG) 廣告為主。2. 廣告費由甲方自付平台。3. 素材由甲方提供。"])
    add_cl("第四條　配合事項", ["甲方應配合資料提供、權限設定與必要之遠端操作配合。"])
    add_cl("第五條　費用與付款", [price_text, pay_time_text, first_pay_text, f"乙方指定帳戶：{BANK_NAME} ({BANK_CODE}) {ACCOUNT_NUMBER}"])
    add_cl("第六條　稅務責任", ["乙方為自然人，不開立發票。甲方自行處理勞報或相關稅務。"])
    add_cl("第七條　成效聲明與免責", ["乙方盡力優化但不保證特定銷售成果。因平台政策或帳號受限導致中斷，乙方不負賠償責任。"])
    add_cl("第八條　保密與智財", ["商業資料互負保密義務 2 年。產出之策略成果，甲方付清款項後可於本案範圍使用。"])
    add_cl("第十條　合約終止", ["提前終止需 14 日前通知。", refund_text])
    add_cl("第十一～十四條", ["相關通知得以通訊軟體為之。如有爭議，以臺灣臺北地方法院為管轄法院。"])

    doc.add_paragraph("\n")
    table = doc.add_table(rows=1, cols=2); table.autofit = False
    c1 = table.cell(0, 0); p1 = c1.paragraphs[0]
    run1 = p1.add_run(f"甲方：{party_a}\n信箱：{email}\n\n簽名：__________\n日期：____/____/____"); set_run_font(run1)
    c2 = table.cell(0, 1); p2 = c2.paragraphs[0]
    run2 = p2.add_run(f"乙方：{PROVIDER_NAME}\n\n簽名：__________\n日期：____/____/____"); set_run_font(run2)

    buf = io.BytesIO(); doc.save(buf); buf.seek(0)
    return buf.getvalue()

# =========================================================
# 4) Sidebar 登入與導覽
# =========================================================
if "user" not in st.session_state: st.session_state.user = None 
if "p1_msg" not in st.session_state: st.session_state.p1_msg = None
if "p2_msg" not in st.session_state: st.session_state.p2_msg = None

with st.sidebar:
    st.title("系統入口")
    if st.session_state.user:
        st.success(f"🟢 已登入：{st.session_state.user['name']}")
        with st.expander("🔑 安全與密碼管理"):
            st.warning("⚠️ **安全提示**：\n本系統採用 **SHA-256 雜湊** 存儲。請勿使用與網銀、Gmail 等相同的高機密常用密碼。")
            new_p = st.text_input("設定新密碼", type="password")
            if st.button("確認修改"):
                if len(new_p) < 4: st.error("密碼太短")
                else:
                    update_password(st.session_state.user["row_num"], new_p)
                    st.success("密碼已安全加密更新！")
        st.markdown("---")
        if st.button("登出系統"):
            st.session_state.clear(); st.rerun()
    else:
        mode = st.radio("模式", ["客戶登入", "新客戶建檔"])
        if mode == "新客戶建檔":
            reg_n = st.text_input("客戶名稱")
            reg_e = st.text_input("聯絡信箱 (限 Gmail)")
            if st.button("開始建檔"):
                if not reg_n or not reg_e.endswith("@gmail.com"): st.error("格式錯誤")
                else:
                    row, _ = find_user_row(reg_e)
                    if row: st.error("已存在，請登入。預設密碼 dennis")
                    else: st.session_state.user = {"email": reg_e, "name": reg_n, "role": "new"}; st.rerun()
        else:
            with st.form("login_form"):
                log_e = st.text_input("信箱"); log_p = st.text_input("密碼", type="password")
                if st.form_submit_button("登入"):
                    row, data = find_user_row(log_e)
                    if not row: st.error("找不到此信箱")
                    elif check_password(log_p, str(data.get("password","")).strip() or "dennis"):
                        st.session_state.user = {"email": data["Email"], "name": data["party_a"], "role": "login", "row_num": row, "raw_data": data}
                        st.rerun()
                    else: st.error("密碼錯誤")

# =========================================================
# 5) 頁面渲染
# =========================================================
if not st.session_state.user:
    st.title("📝 廣告投放服務｜合約＋啟動資料收集")
    st.caption("✅ 自動 Word 合約生成 ＋ 雲端資料庫同步")
    st.info("👈 請由左側登入 (預設密碼: dennis) 或建檔。")
    st.stop()

user = st.session_state.user; raw = user.get("raw_data", {})
st.title("📝 廣告投放服務系統")
st.markdown(f"**使用者：{user['name']} ({user['email']})**")
st.markdown("---")

nav = st.radio("流程：", ["第一階段｜合約", "第二階段｜啟動前確認"] if user["role"] == "login" else ["第一階段｜合約"], horizontal=True)
if nav == "第一階段｜合約": st.session_state.p2_msg = None
else: st.session_state.p1_msg = None

# -----------------
# 第一階段｜合約
# -----------------
if nav == "第一階段｜合約":
    st.header("第一階段｜合約說明與建檔")
    st.info("💡 **操作流程**：詳閱服務內容 -> 選擇方案 -> 生成案件與合約 -> 下載合約並傳送訊息")
    
    with st.expander("✅ 服務範圍與現況提醒 (展開查看)", expanded=True):
        st.subheader("固定工作項目")
        st.markdown("- 廣告上架\n- 廣告監控 / 維護 / 優化\n- 簡易週報（成果摘要與方向）")
        st.subheader("非固定項目")
        st.markdown("- 廣告文案與素材優化建議\n- 到達網頁調整建議")
        st.info("現況提醒：目前我的 FB 個人帳號被停用，我會教你如何每天匯出數據給我監控。若需調整後台，我會透過遠端連線操作你的電腦調整。")

    st.subheader("💰 付款與日期")
    c1, c2 = st.columns(2)
    with c1:
        plan = st.radio("方案：", ["17,000元/月（每月付款）", "45,000元/三個月（一次付款）"], disabled=(user["role"]=="login"))
        s_date = st.date_input("啟動日", value=date.today()+timedelta(days=7), disabled=(user["role"]=="login"))
    with c2:
        p_day = st.slider("付款日", 1, 28, 5, disabled=(user["role"]=="login")) if "每月" in plan else 5
        p_date = st.date_input("付款日期", value=s_date, disabled=(user["role"]=="login")) if "三個月" in plan else None

    if user["role"] == "new":
        if st.button("🎲 確定方案並建立案件", type="primary"):
            case_id = f"{user['name']}_{datetime.now().strftime('%Y%m%d')}"
            data_dict = {"Email": user["email"], "case_id": case_id, "party_a": user["name"], "plan": plan, "start_date": s_date, "pay_day": p_day, "pay_date": p_date}
            save_phase1_new(data_dict)
            send_email(f"【新案件】{user['name']} 已建檔", f"名稱：{user['name']}\n案件號：{case_id}\n方案：{plan}")
            st.session_state.p1_msg = f"【合約確認】\n案件：{case_id}\n甲方：{user['name']}\n方案：{plan}"
            st.rerun()
    
    if st.session_state.p1_msg:
        st.success("✅ 建檔成功！請複製訊息傳 LINE："); st.code(st.session_state.p1_msg); st.balloons()

    if user["role"] == "login":
        st.info(f"案件號：{raw.get('case_id')}")
        if st.button("📝 生成 Word 合約"):
            docx = generate_docx_bytes(user["name"], user["email"], plan, s_date, p_day, p_date, raw.get("case_id"))
            st.download_button("⬇️ 下載合約 (.docx)", docx, f"合約_{raw.get('case_id')}.docx")

# -----------------
# 第二階段｜啟動前確認
# -----------------
elif nav == "第二階段｜啟動前確認":
    st.header("第二階段｜啟動資料收集")
    st.info("💡 **操作流程**：確認資產狀況 -> 填寫行銷情報 -> 更新並回傳訊息")
    
    def b(k): return str(raw.get(k, "FALSE")).upper() == "TRUE"
    def s(k): return raw.get(k, "")

    st.subheader("✅ 確認事項")
    col1, col2 = st.columns(2)
    with col1:
        ad = st.checkbox("廣告帳號已開啟", value=b("chk_ad_account"))
        px = st.checkbox("像素事件已埋放", value=b("chk_pixel"))
    with col2:
        fp = st.checkbox("粉專已建立", value=b("chk_fanpage"))
        bm = st.checkbox("企業管理平台已建立", value=b("chk_bm"))
    
    rem = st.checkbox("已設定 Google 遠端桌面", value=b("chk_remote"))
    st.caption(f"[遠端教學]({REMOTE_SUPPORT_URL})")
    cre = st.checkbox("已前往上傳素材", value=b("chk_creatives"))
    st.caption(f"[素材系統]({CREATIVES_UPLOAD_URL})")

    st.subheader("🧾 詳細行銷情報")
    fp_u = st.text_input("粉專網址", value=s("fanpage_url"))
    ld_u = st.text_input("導向頁", value=s("landing_url"))
    cp1 = st.text_input("競品 1", value=s("comp1"))
    who = st.text_area("解決誰的問題？", value=s("who_problem"))
    bud = st.text_input("首月預算", value=s("budget"))

    if st.button("💾 更新資料並通知", type="primary"):
        with st.spinner("同步至雲端資料庫..."):
            p2_data = {"chk_ad_account": ad, "chk_pixel": px, "chk_fanpage": fp, "chk_bm": bm, "chk_remote": rem, "chk_creatives": cre, "fanpage_url": fp_u, "landing_url": ld_u, "comp1": cp1, "comp2": "", "comp3": "", "who_problem": who, "what_problem": "", "how_solve": "", "budget": bud}
            update_phase2(user["row_num"], p2_data)
            send_email(f"【更新】{user['name']} 啟動資料", f"客戶 {user['name']} 已更新啟動資料。")
            st.session_state.p2_msg = f"【資料更新】\n案件：{raw.get('case_id')}\n遠端：{'OK' if rem else '未完成'}\n素材：{'OK' if cre else '未完成'}"
            st.rerun()

    if st.session_state.p2_msg:
        st.success("✅ 更新成功！請複製訊息傳 LINE："); st.code(st.session_state.p2_msg); st.balloons()
