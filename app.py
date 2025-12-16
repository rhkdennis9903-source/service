import json
import base64

# =========================================================
# 第二階段｜啟動前確認（即時輸出 × 可備份還原）
# =========================================================
st.header("🚀 第二階段｜啟動前確認 & 資料蒐集")
st.caption("📌 可分次填寫；下方回傳內容會即時更新")

# ---------- 確保 session_state keys 存在（避免 restore/讀取時缺 key） ----------
DEFAULTS_PHASE2 = {
    "ad_account": False,
    "pixel": False,
    "fanpage": False,
    "bm": False,
    "fanpage_url": "",
    "landing_url": "",
    "comp1": "",
    "comp2": "",
    "comp3": "",
    "who_problem": "",
    "what_problem": "",
    "how_solve": "",
    "budget": "",
}
for k, v in DEFAULTS_PHASE2.items():
    st.session_state.setdefault(k, v)

# ---------- 備份 / 還原（Sidebar） ----------
def _phase2_state_dict():
    """只取 Phase2 需要的欄位，避免把整個 session_state 都帶走。"""
    return {k: st.session_state.get(k, DEFAULTS_PHASE2[k]) for k in DEFAULTS_PHASE2.keys()}

def _encode_backup(data: dict) -> str:
    """
    把 dict -> JSON -> base64，確保可含換行、特殊符號，且不會被 splitlines 搞壞。
    """
    raw = json.dumps(data, ensure_ascii=False)
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")

def _decode_backup(text: str) -> dict:
    """
    支援兩種：
    1) base64(JSON)（建議）
    2) 直接貼 JSON（容錯）
    """
    t = (text or "").strip()
    if not t:
        return {}

    # 嘗試 base64
    try:
        raw = base64.b64decode(t.encode("utf-8")).decode("utf-8")
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # 嘗試直接 JSON
    try:
        obj = json.loads(t)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    raise ValueError("備份內容格式不正確（請貼上完整備份字串）")

def restore_phase2(data: dict):
    """只還原 Phase2 需要的 keys；其他一律忽略。"""
    if not isinstance(data, dict):
        return
    for k in DEFAULTS_PHASE2.keys():
        if k in data:
            st.session_state[k] = data[k]

with st.sidebar:
    st.subheader("🗒️ 暫存 / 還原")

    st.caption("建議：先按「還原」確認無誤，再開始填寫，避免覆蓋你正在輸入的內容。")

    backup_input = st.text_area(
        "貼上你之前備份的內容（base64 或 JSON 都可）",
        height=240,
        placeholder="把你存在筆記本的備份內容貼回來"
    )

    c_restore, c_clear = st.columns(2)
    with c_restore:
        do_restore = st.button("♻️ 還原", use_container_width=True)
    with c_clear:
        do_clear = st.button("🧹 清空本階段", use_container_width=True)

    if do_restore:
        try:
            restored = _decode_backup(backup_input)
            restore_phase2(restored)
            st.success("✅ 已還原（僅套用本階段欄位）")
            st.rerun()
        except Exception as e:
            st.error(f"❌ 還原失敗：{e}")

    if do_clear:
        for k, v in DEFAULTS_PHASE2.items():
            st.session_state[k] = v
        st.success("✅ 已清空本階段欄位")
        st.rerun()

# ---------- 教學影片 ----------
st.video(PHASE2_TUTORIAL_URL)

# ---------- 確認事項 ----------
st.subheader("✅ 確認事項（照實勾選）")
col1, col2 = st.columns(2)
with col1:
    st.checkbox("廣告帳號已開啟", key="ad_account")
    st.checkbox("像素事件已埋放", key="pixel")
with col2:
    st.checkbox("粉專已建立", key="fanpage")
    st.checkbox("企業管理平台已建立", key="bm")

# ---------- 資料填寫 ----------
st.subheader("🧾 須提供事項")
st.text_input("粉專網址", key="fanpage_url")
st.text_input("廣告導向頁", key="landing_url")

st.markdown("**競爭對手粉專**")
st.text_input("競品 1", key="comp1")
st.text_input("競品 2", key="comp2")
st.text_input("競品 3", key="comp3")

st.text_area("解決誰的問題？", key="who_problem")
st.text_area("要解決什麼問題？", key="what_problem")
st.text_area("如何解決？", key="how_solve")
st.text_input("第一個月預算", key="budget")

# ---------- 備份內容（即時） ----------
phase2_data = _phase2_state_dict()
backup_b64 = _encode_backup(phase2_data)

st.subheader("🗂️ 備份用內容（請複製存到筆記本）")
st.caption("✅ 這段可完整還原（含多行文字），建議直接存這段。")
st.code(backup_b64, language=None)

with st.expander("（可選）查看備份的 JSON 原文", expanded=False):
    st.code(json.dumps(phase2_data, ensure_ascii=False, indent=2), language="json")

# ---------- 回傳訊息（即時生成） ----------
def s(x: str) -> str:
    x = (x or "").strip()
    return x if x else "（未填）"

def status(v: bool) -> str:
    return "✅ 已完成" if v else "⬜ 未完成"

party_a = st.session_state.get("last_party_a_name", "")
party_a_show = party_a.strip() if party_a and party_a.strip() else "（未填｜請先在合約頁填甲方名稱）"

reply_text = f"""請直接複製以下內容，使用 LINE 回傳給我（{PROVIDER_NAME}）：

【第二階段啟動資料】
甲方：{party_a_show}

【確認事項】
- 廣告帳號：{status(st.session_state.ad_account)}
- 像素事件：{status(st.session_state.pixel)}
- 粉專：{status(st.session_state.fanpage)}
- BM：{status(st.session_state.bm)}

【資料】
- 粉專網址：{s(st.session_state.fanpage_url)}
- 導向頁：{s(st.session_state.landing_url)}

【競品】
1) {s(st.session_state.comp1)}
2) {s(st.session_state.comp2)}
3) {s(st.session_state.comp3)}

【定位】
- 對象：{s(st.session_state.who_problem)}
- 問題：{s(st.session_state.what_problem)}
- 解法：{s(st.session_state.how_solve)}

【首月預算】
- {s(st.session_state.budget)}
"""

st.subheader("📤 回傳內容（即時更新，可直接複製）")
st.code(reply_text, language=None)
