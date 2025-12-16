# =========================================================
# 第二階段｜啟動前確認（即時輸出 × 可備份還原）
# =========================================================
st.header("🚀 第二階段｜啟動前確認 & 資料蒐集")
st.caption("📌 可分次填寫；下方回傳內容會即時更新")

# =========================================================
# ✅ 新增：服務方式說明（前台白話版，放在最前面）
# =========================================================
st.markdown("---")
st.subheader("📌 服務方式說明（請先閱讀）")

st.info("""
現況提醒：目前我的 FB 個人帳號仍然被停用，但我仍需要每天監控你的廣告成果，因此會採用以下合作方式：

1) **每日監控方式**
- 我會先協助你設定好固定的「廣告數據匯出」方式
- 你每天只需要照我設定的流程按一次匯出，把數據提供給我即可（你不需要分析）

2) **調整與優化方式（遠端控制你的電腦）**
- 當我判斷需要調整廣告後台設定時，我會先跟你約定時間
- 屆時會透過遠端連線方式，由我直接操作你電腦上的廣告後台畫面進行調整

3) **為了不浪費你的時間**
- 遠端前我都會先準備好完整調整規劃
- 實際連線操作會非常快、只做必要調整
""")

# ---------- Sidebar：備份 / 還原 ----------
with st.sidebar:
    st.subheader("🗒️ 暫存 / 還原")

    backup_input = st.text_area(
        "貼上你之前備份的內容（可選）",
        height=300,
        placeholder="把你存在筆記本的內容貼回來"
    )

    def restore_from_backup(text: str):
        if not text:
            return
        lines = [l.strip() for l in text.splitlines() if "=" in l]
        for line in lines:
            k, v = line.split("=", 1)
            if k in st.session_state:
                if v in ["0", "1"]:
                    st.session_state[k] = True if v == "1" else False
                else:
                    st.session_state[k] = v

    if backup_input:
        restore_from_backup(backup_input)
        st.success("已嘗試還原內容（若欄位存在即已帶入）")

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

# ---------- 備份內容（即時） ----------
backup_text = f"""[CHECK]
ad_account={1 if ad_account else 0}
pixel={1 if pixel else 0}
fanpage={1 if fanpage else 0}
bm={1 if bm else 0}

[DATA]
fanpage_url={fanpage_url}
landing_url={landing_url}
comp1={comp1}
comp2={comp2}
comp3={comp3}
who_problem={who_problem}
what_problem={what_problem}
how_solve={how_solve}
budget={budget}
"""

st.subheader("🗂️ 備份用內容（請複製存到筆記本）")
st.code(backup_text)

# ---------- 回傳訊息（即時生成） ----------
def s(x): return x if x.strip() else "（未填）"
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
