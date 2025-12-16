import streamlit as st
from datetime import datetime, timedelta
import io
import json  # 新增：用於處理更穩定的備份資料
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn 

# =========================================================
# 0) 基礎設定
# =========================================================
PROVIDER_NAME = "高如慧"  
BANK_NAME = "中國信託商業銀行"
BANK_CODE = "822"
ACCOUNT_NUMBER = "783540208870"
PHASE2_TUTORIAL_URL = "https://youtu.be/caoZAO8tyNs"

# =========================================================
# 1) Page config
# =========================================================
st.set_page_config(
    page_title="廣告投放合作工具",
    page_icon="📝",
    layout="centered"
)

st.title("📝 廣告投放合作工具")
st.caption("第一階段：合約生成｜第二階段：啟動前確認與資料蒐集")
st.markdown("---")

# =========================================================
# 2) Session state 初始化
# =========================================================
if "generated" not in st.session_state:
    st.session_state.generated = False
    st.session_state.client_message = ""
    st.session_state.payment_message = ""
    st.session_state.docx_bytes = b""
    st.session_state.last_party_a_name = ""

# =========================================================
# 3) Word 字型設定函式
# =========================================================
def set_run_font(run, size=12, bold=False):
    run.font.name = "Microsoft JhengHei"
    run.font.size = Pt(size)
    run.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft JhengHei")

# =========================================================
# 4) 生成 Word 邏輯
# =========================================================
def generate_docx_bytes(party_a, payment_opt, start_dt, pay_day, pay_dt):
    doc = Document()
    style = doc.styles["Normal"]
    style.paragraph_format.line_spacing = 1.5

    heading = doc.add_paragraph()
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = heading.add_run("廣告投放服務合約書")
    set_run_font(run, size=18, bold=True)
    doc.add_paragraph("")

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
        refund_text = "2. 季付方案屬優惠性質之預付服務費，一經支付後即不予退還。即使甲方於合約期間內提前終止或未使用完畢服務內容，亦同；惟因乙方重大違約致服務無法履行者，不在此限。"

    p = doc.add_paragraph()
    run = p.add_run(f"甲方（委託暨付款方）：{party_a}\n")
    set_run_font(run, size=12, bold=True)
    run = p.add_run(f"乙方（服務執行者）：{PROVIDER_NAME}")
    set_run_font(run, size=12, bold=True)
    doc.add_paragraph("")

    p = doc.add_paragraph()
    run = p.add_run("茲因甲方委託乙方提供數位廣告投放服務，雙方本於誠信原則，同意訂立本合約，並共同遵守下列條款：")
    set_run_font(run)

    def add_clause(title, contents):
        p_title = doc.add_paragraph()
        run_title = p_title.add_run(title)
        set_run_font(run_title, size=12, bold=True)
        for content in contents:
            if content:
                p_item = doc.add_paragraph()
                p_item.paragraph_format.left_indent = Cm(0.75)
                run_item = p_item.add_run(content)
                set_run_font(run_item)

    add_clause("第一條　合約期間", [period_text])

    doc.add_paragraph("")
    p = doc.add_paragraph()
    run = p.add_run("第二條　服務內容")
    set_run_font(run, bold=True)
    p = doc.add_paragraph()
    run = p.add_run("乙方同意為甲方提供以下廣告投放服務：")
    set_run_font(run)

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
        "1. 廣告素材建議：乙方得依投放成效、競品與市場狀況，提供素材與文案方向建議。",
        "2. 到達頁面優化建議：於轉換成效異常或下降時，提供頁面優化方向。"
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
    add_clause("第十一條　通知方式", [
        "本合約相關通知，得以電子郵件、LINE、Messenger 或其他雙方約定之通訊方式為之，於發送時即生效力。"
    ])
    add_clause("第十二條　合約變更", [
        "本合約之任何修改或補充，應經雙方書面同意後始生效力。"
    ])
    add_clause("第十三條　不可抗力", [
        "因天災、戰爭、政府行為、網路中斷、平台系統異常或其他不可抗力因素，致任一方無法履行本合約義務時，該方不負違約責任；惟應儘速通知並於事由消滅後恢復履行。"
    ])
    add_clause("第十四條　爭議處理", [
        "本合約之解釋與適用，以中華民國法律為準據法。雙方如有爭議，應先行協商；協商不成以臺灣臺北地方法院為第一審管轄法院。"
    ])

    doc.add_paragraph("")
    doc.add_paragraph("")

    table = doc.add_table(rows=1, cols=2)
    table.autofit = False

    cell_a = table.cell(0, 0)
    run = cell_a.paragraphs[0].add_run(
        f"甲方（委託暨付款方）：\n{party_a}\n\n簽名：___________________\n\n日期：_____ 年 ___ 月 ___ 日"
    )
    set_run_font(run, size=12)

    cell_b = table.cell(0, 1)
    run = cell_b.paragraphs[0].add_run(
        f"乙方（服務執行者）：\n{PROVIDER_NAME}\n\n簽名：___________________\n\n日期：_____ 年 ___ 月 ___ 日"
    )
    set_run_font(run, size=12)

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

# =========================================================
# Sidebar：兩階段導覽
# =========================================================
with st.sidebar:
    st.header("導覽")
    nav = st.radio(
        "請選擇階段：",
        ["第一階段｜合約", "第二階段｜啟動前確認"],
        index=0
    )

# =========================================================
# 第一階段｜合約
# =========================================================
if nav == "第一階段｜合約":

    st.header("服務內容說明")

    st.subheader("✅ 固定工作")
    st.markdown("""
    - **廣告上架**
    - **廣告監控 / 維護 / 優化**
    - **簡易週報**（成果摘要、下週優化方向）
    """)

    st.subheader("📌 非固定工作（視狀況提供）")
    st.markdown("""
    - **廣告素材建議**
      - 依投放成效、競品、市場狀況提出方向
    - **到達頁面優化建議**
      - 監控轉換成效
    """)

    st.warning("📌 稅務提醒：乙方為自然人，無須開立發票。甲方自行處理勞報或相關稅務。")
    st.markdown("---")

    st.header("💰 付款方案")
    payment_option = st.radio(
        "方案選擇：",
        options=["17,000元/月（每月付款）", "45,000元/三個月（一次付款）"]
    )

    st.header("📅 時間設定")
    default_start = datetime.now().date() + timedelta(days=7)
    start_date = st.date_input("合作啟動日", value=default_start)

    payment_day = None
    payment_date = None

    if payment_option == "17,000元/月（每月付款）":
        payment_day = st.slider("每月付款日", 1, 28, 5)
    else:
        default_pay = start_date - timedelta(days=3)
        if default_pay < datetime.now().date():
            default_pay = datetime.now().date()
        payment_date = st.date_input("付款日期", value=default_pay)

    st.markdown("---")

    st.header("🧾 甲方資訊")
    party_a_name = st.text_input("甲方名稱", placeholder="公司或個人名稱")

    st.header("👤 乙方資訊")
    st.text_input("乙方", value=PROVIDER_NAME, disabled=True)
    c1, c2 = st.columns(2)
    c1.text_input("銀行", value=f"{BANK_NAME} ({BANK_CODE})", disabled=True)
    c2.text_input("帳號", value=ACCOUNT_NUMBER, disabled=True)

    st.markdown("---")

    st.header("✅ 生成合約")

    if st.button("📝 生成 Word 合約", type="primary", use_container_width=True):
        if not party_a_name.strip():
            st.error("請輸入甲方名稱")
        else:
            if payment_option == "17,000元/月（每月付款）":
                client_msg = f"""請直接複製以下內容，使用 LINE 傳給我（{PROVIDER_NAME}）：

【合約確認】
甲方：{party_a_name}
乙方：{PROVIDER_NAME}
方案：17,000元/月
啟動：{start_date.strftime('%Y-%m-%d')}
付款：每月 {payment_day} 日
"""
            else:
                client_msg = f"""請直接複製以下內容，使用 LINE 傳給我（{PROVIDER_NAME}）：

【合約確認】
甲方：{party_a_name}
乙方：{PROVIDER_NAME}
方案：45,000元/季
啟動：{start_date.strftime('%Y-%m-%d')}
付款：{payment_date.strftime('%Y-%m-%d')} 前
"""

            payment_msg = f"""【收款資訊】
銀行：{BANK_NAME} ({BANK_CODE})
帳號：{ACCOUNT_NUMBER}
"""

            docx_bytes = generate_docx_bytes(
                party_a_name, payment_option, start_date, payment_day, payment_date
            )

            st.session_state.client_message = client_msg
            st.session_state.payment_message = payment_msg
            st.session_state.docx_bytes = docx_bytes
            st.session_state.generated = True
            st.session_state.last_party_a_name = party_a_name

            st.success("✅ Word 合約已生成！")

    if st.session_state.generated:
        st.markdown("---")
        st.subheader("📤 給甲方看的訊息（請複製後用 LINE 傳給我）")
        st.code(st.session_state.client_message, language=None)

        st.subheader("💳 收款資訊（可複製）")
        st.code(st.session_state.payment_message, language=None)

        filename = f"廣告投放合約_{st.session_state.last_party_a_name}_{datetime.now().strftime('%Y%m%d')}.docx"
        st.download_button(
            label="⬇️ 下載 Word 合約 (.docx)",
            data=st.session_state.docx_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
        st.info("💡 下載後，建議直接在 Word 中『另存新檔 -> PDF』，即可獲得完美排版。")
    
    # 重置按鈕改為只清空合約相關
    if st.button("重置（清除合約資料）", use_container_width=True):
        st.session_state.generated = False
        st.session_state.client_message = ""
        st.session_state.payment_message = ""
        st.session_state.docx_bytes = b""
        st.session_state.last_party_a_name = ""
        st.rerun()

# =========================================================
# 第二階段｜啟動前確認（修正縮排，確保切換正常）
# =========================================================
elif nav == "第二階段｜啟動前確認":
    
    st.header("🚀 第二階段｜啟動前確認 & 資料蒐集")
    st.caption("📌 可分次填寫；下方回傳內容會即時更新")

    # ---------- Sidebar：備份 / 還原 (JSON版) ----------
    with st.sidebar:
        with st.expander("📂 暫存 / 還原 (JSON版)", expanded=False):
            st.caption("將下方的「備份碼」貼到這裡還原：")
            backup_input = st.text_area(
                "貼上備份碼",
                height=150,
                placeholder='{"ad_account": true, ...}'
            )

            def restore_from_json(text: str):
                if not text.strip():
                    return
                try:
                    data = json.loads(text)
                    for k, v in data.items():
                        st.session_state[k] = v
                    st.success("✅ 資料已還原！")
                except json.JSONDecodeError:
                    st.error("❌ 格式錯誤，請確認複製了完整的備份碼")

            if st.button("🔄 執行還原"):
                restore_from_json(backup_input)
                st.rerun() # 強制刷新介面以顯示還原資料

    # ---------- 教學影片 ----------
    st.video(PHASE2_TUTORIAL_URL)

    # ---------- 確認事項 ----------
    st.subheader("✅ 確認事項（照實勾選）")
    col1, col2 = st.columns(2)
    with col1:
        ad_account = st.checkbox("廣告帳號已開啟", key="ad_account")
        pixel = st.checkbox("像素事件已埋放", key="pixel")
    with col2:
        fanpage = st.checkbox("粉專已建立", key="fanpage")
        bm = st.checkbox("企業管理平台已建立", key="bm")

    # ---------- 資料填寫 ----------
    st.subheader("🧾 須提供事項")
    fanpage_url = st.text_input("粉專網址", key="fanpage_url")
    landing_url = st.text_input("廣告導向頁", key="landing_url")

    st.markdown("**競爭對手粉專**")
    comp1 = st.text_input("競品 1", key="comp1")
    comp2 = st.text_input("競品 2", key="comp2")
    comp3 = st.text_input("競品 3", key="comp3")

    who_problem = st.text_area("解決誰的問題？", key="who_problem")
    what_problem = st.text_area("要解決什麼問題？", key="what_problem")
    how_solve = st.text_area("如何解決？", key="how_solve")
    budget = st.text_input("第一個月預算", key="budget")

    # ---------- 備份內容（JSON生成） ----------
    # 建立一個字典來存放資料
    backup_data = {
        "ad_account": ad_account,
        "pixel": pixel,
        "fanpage": fanpage,
        "bm": bm,
        "fanpage_url": fanpage_url,
        "landing_url": landing_url,
        "comp1": comp1,
        "comp2": comp2,
        "comp3": comp3,
        "who_problem": who_problem,
        "what_problem": what_problem,
        "how_solve": how_solve,
        "budget": budget
    }
    
    # 轉成 JSON 字串，ensure_ascii=False 確保中文正常顯示
    backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2)

    st.subheader("🗂️ 備份用內容（請複製存到筆記本）")
    st.text_area("👇 全選複製這一段代碼：", value=backup_json, height=150)

    # ---------- 回傳訊息（即時生成） ----------
    def s(x): return x if x and x.strip() else "（未填）"
    def status(v): return "✅ 已完成" if v else "⬜ 未完成"

    reply_text = f"""請直接複製以下內容，使用 LINE 回傳給我（{PROVIDER_NAME}）：

【第二階段啟動資料】
甲方：{st.session_state.get("last_party_a_name","（未填）")}

【確認事項】
- 廣告帳號：{status(ad_account)}
- 像素事件：{status(pixel)}
- 粉專：{status(fanpage)}
- BM：{status(bm)}

【資料】
- 粉專網址：{s(fanpage_url)}
- 導向頁：{s(landing_url)}

【競品】
1) {s(comp1)}
2) {s(comp2)}
3) {s(comp3)}

【定位】
- 對象：{s(who_problem)}
- 問題：{s(what_problem)}
- 解法：{s(how_solve)}

【首月預算】
- {s(budget)}
"""

    st.subheader("📤 回傳內容（即時更新，可直接複製）")
    st.code(reply_text)
