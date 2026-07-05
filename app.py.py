import pandas as pd
import streamlit as st
from supabase import create_client, Client
import hashlib

# 設定網頁
st.set_page_config(page_title="定期定額資產組合系統", page_icon="💰", layout="centered")

# ==========================================
# 🔌 1. 雲端資料庫連線設定 (已幫你修正位置與網址)
# ==========================================
SUPABASE_URL = "https://xjsmwrywbcqyoheoagkk.supabase.co"
SUPABASE_KEY = "sb_publishable_Crb3xKBHC2yva0Q_phK-cA_KQiiTN7t"

# 初始化資料庫連線
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase: Client = init_supabase()
except Exception as e:
    st.error("資料庫連線設定失敗，請檢查 URL 與 KEY 是否正確。")

# 密碼雜湊加密函數（保護使用者隱私，不存明碼）
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ==========================================
# 👤 2. 會員登入狀態管理 (Session State)
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# ==========================================
# 🚪 3. 前端註冊 / 登入介面
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 歡迎使用定期定額資產管理系統")
    st.write("本系統採用會員制，請先登入或註冊帳號以解鎖資產試算功能。")
    
    # 使用頁籤切換 登入 與 註冊
    tab1, tab2 = st.tabs(["🔑 會員登入", "📝 快速註冊"])
    
    with tab1:
        login_user = st.text_input("帳號 (使用者名稱)", key="login_user")
        login_pwd = st.text_input("密碼", type="password", key="login_pwd")
        
        if st.button("立即登入", type="primary", use_container_width=True):
            if login_user and login_pwd:
                # 去 Supabase 查詢該帳號
                response = supabase.table("users").select("*").eq("username", login_user).execute()
                
                if response.data:
                    user_record = response.data[0]
                    # 比對加密後的密碼
                    if user_record["password"] == hash_password(login_pwd):
                        st.session_state.logged_in = True
                        st.session_state.username = login_user
                        st.success(f"🎉 登入成功！歡迎回來，{login_user}！")
                        st.rerun()
                    else:
                        st.error("❌ 密碼錯誤，請再試一次。")
                else:
                    st.error("❌ 找不到此帳號，請先前往註冊。")
            else:
                st.warning("⚠️ 請填寫完整的帳號與密碼。")
                
    with tab2:
        reg_user = st.text_input("設定新帳號", key="reg_user")
        reg_pwd = st.text_input("設定新密碼", type="password", key="reg_pwd")
        reg_pwd_confirm = st.text_input("確認新密碼", type="password", key="reg_pwd_confirm")
        
        if st.button("註冊新帳號", use_container_width=True):
            if reg_user and reg_pwd and reg_pwd_confirm:
                if reg_pwd != reg_pwd_confirm:
                    st.error("❌ 兩次輸入的密碼不一致！")
                else:
                    # 檢查帳號是否已被註冊
                    check_exist = supabase.table("users").select("username").eq("username", reg_user).execute()
                    if check_exist.data:
                        st.error("❌ 該帳號已被使用，請換一個名字。")
                    else:
                        # 將新會員資料寫入雲端資料庫
                        new_user = {
                            "username": reg_user,
                            "password": hash_password(reg_pwd)
                        }
                        supabase.table("users").insert(new_user).execute()
                        st.success("🎉 註冊成功！請切換至「會員登入」頁籤進行登入。")
            else:
                st.warning("⚠️ 請填寫所有註冊欄位。")

# ==========================================
# 📈 4. 登入成功後的主程式介面 (原有的定期定額功能)
# ==========================================
else:
    # 頂部狀態列
    st.sidebar.title(f"👤 會員：{st.session_state.username}")
    if st.sidebar.button("登出系統", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.title("💰 定期定額資產組合試算 App")
    st.write(f"你好，**{st.session_state.username}**！開始規劃你的資產配置比例吧。")
    st.divider()

    # 基礎投資參數
    col1, col2 = st.columns(2)
    with col1:
        monthly_deposit = st.number_input("每月總投入金額 (元)", min_value=100, value=10000, step=1000)
    with col2:
        total_months = st.number_input("預計投資月數 (月)", min_value=1, value=36, step=1)

    st.write("")
    st.subheader("🛠️ 自訂資產組合配置")
    
    default_portfolio = pd.DataFrame([
        {"資產名稱": "美股 ETF (如 VTI)", "配置比例 (%)": 60.0, "預期年化報酬率 (%)": 9.0},
        {"資產名稱": "高股息 ETF (如 0056)", "配置比例 (%)": 30.0, "預期年化報酬率 (%)": 6.0},
        {"資產名稱": "加密貨幣 / 現金", "配置比例 (%)": 10.0, "預期年化報酬率 (%)": 2.0},
    ])

    edited_df = st.data_editor(default_portfolio, num_rows="dynamic", use_container_width=True)

    # 計算邏輯
    total_allocation = edited_df["配置比例 (%)"].sum()

    if total_allocation != 100.0:
        st.warning(f"⚠️ 目前配置總比例為 **{total_allocation:.1f}%**。建議調整至 **100%**。")

    weighted_annual_rate = (edited_df["配置比例 (%)"] * edited_df["預期年化報酬率 (%)"]).sum() / total_allocation / 100 if total_allocation > 0 else 0

    total_principal = 0
    future_value = 0
    monthly_rate = weighted_annual_rate / 12

    for month in range(1, total_months + 1):
        total_principal += monthly_deposit
        future_value = (future_value + monthly_deposit) * (1 + monthly_rate)

    total_interest = round(future_value) - total_principal
    roi = ((future_value - total_principal) / total_principal) * 100 if total_principal > 0 else 0

    st.divider()

    # 結果輸出
    st.subheader("📊 組合試算結果總覽")
    st.info(f"💡 這套組合的**綜合加權年化報酬率**約為：**{weighted_annual_rate * 100:.2f} %**")

    m1, m2, m3 = st.columns(3)
    m1.metric("預計投資期間", f"{total_months} 個月", f"約 {total_months/12:.1f} 年", delta_color="off")
    m2.metric("總共投入本金", f"{total_principal:,} 元")
    m3.metric("最終本利和", f"{round(future_value):,} 元")

    m4, m5 = st.columns(2)
    m4.metric("賺取總利息", f"{total_interest:,} 元")
    m5.metric("整體投報率", f"{roi:.2f} %")
