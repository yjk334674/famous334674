import pandas as pd
import streamlit as st
from supabase import create_client, Client
import hashlib
from datetime import datetime, date

# 設定網頁
st.set_page_config(page_title="全方位資產與投資管理系統", page_icon="💰", layout="wide")

# ==========================================
# 🔌 1. 雲端資料庫連線設定
# ==========================================
SUPABASE_URL = "https://xjsmwrywbcqyoheoagkk.supabase.co"
SUPABASE_KEY = "sb_publishable_Crb3xKBHC2yva0Q_phK-cA_KQiiTN7t"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error("資料庫連線設定失敗，請檢查 URL 與 KEY 是否正確。")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 👤 2. 會員登入狀態管理
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ==========================================
# 🚪 3. 前端註冊 / 登入介面
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 歡迎使用全方位資產管理系統")
    tab1, tab2 = st.tabs(["🔑 會員登入", "📝 快速註冊"])
    
    with tab1:
        login_user = st.text_input("帳號 (使用者名稱)", key="login_user")
        login_pwd = st.text_input("密碼", type="password", key="login_pwd")
        
        if st.button("立即登入", type="primary", use_container_width=True):
            if login_user and login_pwd:
                try:
                    response = supabase.table("user").select("*").eq("username", login_user).execute()
                    if response.data:
                        user_record = response.data[0]
                        if user_record["password"] == hash_password(login_pwd):
                            st.session_state.logged_in = True
                            st.session_state.username = login_user
                            st.success(f"🎉 登入成功！")
                            st.rerun()
                        else: st.error("❌ 密碼錯誤")
                    else: st.error("❌ 找不到帳號，請確認拼字或先前往註冊。")
                except Exception as ex: st.error(f"資料庫錯誤: {ex}")
            else: st.warning("⚠️ 請填寫完整帳號與密碼。")
                
    with tab2:
        reg_user = st.text_input("設定新帳號", key="reg_user")
        reg_pwd = st.text_input("設定新密碼", type="password", key="reg_pwd")
        reg_pwd_confirm = st.text_input("確認新密碼", type="password", key="reg_pwd_confirm")
        
        if st.button("註冊新帳號", use_container_width=True):
            if reg_user and reg_pwd and reg_pwd_confirm:
                if reg_pwd != reg_pwd_confirm: st.error("❌ 兩次輸入的密碼不一致")
                else:
                    try:
                        check_exist = supabase.table("user").select("username").eq("username", reg_user).execute()
                        if check_exist.data: st.error("❌ 該帳號已被使用，請換一個名字。")
                        else:
                            supabase.table("user").insert({"username": reg_user, "password": hash_password(reg_pwd)}).execute()
                            st.success("🎉 註冊成功！請切換至「會員登入」頁籤進行登入。")
                    except Exception as ex: st.error(f"註冊失敗，詳細錯誤: {ex}")
            else: st.warning("⚠️ 請填寫所有註冊欄位。")

# ==========================================
# 📊 4. 主程式控制核心 (會員登入後)
# ==========================================
else:
    current_user = st.session_state.username
    st.sidebar.title(f"👤 會員：{current_user}")
    module = st.sidebar.radio(
        "🗂️ 核心功能選單",
        ["🏠 總資產智慧管理大盤", "1. 📝 日常記帳 (動態連動)", "2. 🏦 資產帳戶維護", "3. 📈 投資組合 (損益計算)"]
    )
    st.sidebar.divider()
    if st.sidebar.button("登出系統", type="secondary", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # 🔄 全域核心資料拉取與防呆
    try:
        assets_res = supabase.table("own_assets").select("*").eq("username", current_user).execute()
        tx_res = supabase.table("transactions").select("*").eq("username", current_user).execute()
        pf_res = supabase.table("portfolio").select("*").eq("username", current_user).execute()
    except Exception as api_err:
        st.error(f"📡 資料庫連線或欄位對照出錯，請確認後台。錯誤: {api_err}")
        st.stop()

    asset_list = [x["asset_name"] for x in assets_res.data] if assets_res.data else []
    df_tx = pd.DataFrame(tx_res.data) if tx_res.data else pd.DataFrame(columns=["date", "type", "asset_name", "category", "amount", "note"])
    if not df_tx.empty:
        df_tx["date"] = pd.to_datetime(df_tx["date"]).dt.date
        df_tx["amount"] = df_tx["amount"].astype(float)
        
    df_pf = pd.DataFrame(pf_res.data) if pf_res.data else pd.DataFrame()

    # ---------------------------------------------------------
    # 模組 0：🏠 總資產智慧管理大盤 (對應圖 2 畫面)
    # ---------------------------------------------------------
    if module == "🏠 總資產智慧管理大盤":
        st.title("💰 總資產智慧管理大盤")
        st.write("實時匯總您的現金、投資市值，計算您的個人淨資產。")
        
        # 數據計算
        cash_sum = sum(float(x["amount"]) for x in assets_res.data) if assets_res.data else 0.0
        invest_sum = 0.0
        if not df_pf.empty:
            df_unreal = df_pf[df_pf["status"] == "未實現"]
            if not df_unreal.empty:
                invest_sum = df_unreal["actual_cash"].astype(float).sum()
        
        net_worth = cash_sum + invest_sum
        
        # 頂部四大指標看盤 (圖 2 風格)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💵 可用現金餘額", f"{cash_sum:,.0f} 元")
        m2.metric("📊 投資總市值", f"{invest_sum:,.0f} 元")
        m3.metric("🚨 總貸款債務", "0 元")
        m4.metric("👑 個人淨資產 (Net Worth)", f"{net_worth:,.0f} 元")
        
        st.divider()
        st.subheader("💡 資產健康度建議")
        if net_worth == 0:
            st.info("歡迎使用本系統！請先前往「2. 🏦 資產帳戶維護」建立您的第一個資產帳戶（如：現金、銀行存款）。")
        else:
            st.success("✅ 您的資產結構相當健康，負債比率在安全範圍內，請繼續保持定期定額投資！")

    # ---------------------------------------------------------
    # 模組 1：📝 日常記帳
    # ---------------------------------------------------------
    elif module == "1. 📝 日常記帳 (動態連動)":
        st.title("📝 隨手日常記帳中心")
        st.write("在此記帳會**自動同步增減**您的資產帳戶餘額。")
        
        if not asset_list:
            st.warning("⚠️ 您目前沒有任何資產帳戶，請先前往「2. 🏦 資產帳戶維護」建立帳戶！")
        else:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("📥 新增日常收支")
                with st.form("tx_form", clear_on_submit=True):
                    tx_date = st.date_input("記帳日期", value=date.today())
                    tx_type = st.selectbox("交易類型", ["支出", "收入"])
                    tx_asset = st.selectbox("使用帳戶(資產)", asset_list)
                    tx_cate = st.text_input("分類 (如: 餐飲、交通、薪水)")
                    tx_amt = st.number_input("金額 (元)", min_value=1, value=100)
                    tx_note = st.text_input("備註")
                    
                    if st.form_submit_button("確認記帳"):
                        # 寫入一筆記帳到新重建的 transactions
                        supabase.table("transactions").insert({
                            "username": current_user, "date": str(tx_date), "type": tx_type,
                            "asset_name": tx_asset, "category": tx_cate, "amount": tx_amt, "note": tx_note
                        }).execute()
                        
                        current_asset_amt = next(x["amount"] for x in assets_res.data if x["asset_name"] == tx_asset)
                        new_amt = current_asset_amt + tx_amt if tx_type == "收入" else current_asset_amt - tx_amt
                        supabase.table("own_assets").update({"amount": new_amt}).eq("username", current_user).eq("asset_name", tx_asset).execute()
                        
                        st.success("🎉 記帳成功，資產已即時連動變更！")
                        st.rerun()
            with c2:
                st.subheader("📋 本日最新記帳明細")
                today_tx = df_tx[df_tx["date"] == date.today()] if not df_tx.empty else pd.DataFrame()
                if not today_tx.empty:
                    st.dataframe(today_tx[["date", "type", "asset_name", "category", "amount", "note"]], use_container_width=True)
                else:
                    st.info("💡 今天還沒有記帳明細喔！")

    # ---------------------------------------------------------
    # 模組 2：🏦