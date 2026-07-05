import pandas as pd
import streamlit as st
from supabase import create_client, Client
import hashlib
from datetime import datetime

# 設定網頁
st.set_page_config(page_title="全方位資產與投資管理系統", page_icon="💼", layout="wide")

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components # 👈 1. 記得先在最上方引入這個套件
from supabase import create_client, Client
import hashlib
from datetime import datetime

# 設定網頁
st.set_page_config(page_title="全方位資產與投資管理系統", page_icon="💼", layout="wide")

# ==========================================
# 📱 PWA 行動裝置/電腦 App 下載功能注入
# ==========================================
# 這段 JavaScript 會自動偵測使用者的瀏覽器，並提示使用者可以將此網頁「新增至主畫面」下載為 App
pwa_js = """
<script>
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    // 預防 Chrome 67 之前的自動跳出提示
    e.preventDefault();
    deferredPrompt = e;
    // 建立一個提示按鈕或直接通知
    console.log('PWA App 準備就緒，可以下載安裝！');
});
</script>
"""
components.html(pwa_js, height=0) # 讓這段網頁代碼在背景默默執行

# 接下來是你原本的程式碼...
# ==========================================
# 🔌 1. 雲端資料庫連線設定
# ==========================================
SUPABASE_URL = "https://xjsmwrywbcqyoheoagkk.supabase.co"
# ...後面依此類推

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
                response = supabase.table("users").select("*").eq("username", login_user).execute()
                if response.data and response.data[0]["password"] == hash_password(login_pwd):
                    st.session_state.logged_in = True
                    st.session_state.username = login_user
                    st.success(f"🎉 歡迎回來，{login_user}！")
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤。")
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
                    check_exist = supabase.table("users").select("username").eq("username", reg_user).execute()
                    if check_exist.data:
                        st.error("❌ 該帳號已被使用。")
                    else:
                        supabase.table("users").insert({"username": reg_user, "password": hash_password(reg_pwd)}).execute()
                        st.success("🎉 註冊成功！請切換至「會員登入」頁籤。")

# ==========================================
# 📊 4. 登入成功後的主程式 (四大模組選單)
# ==========================================
else:
    st.sidebar.title(f"👤 會員：{st.session_state.username}")
    module = st.sidebar.radio(
        "🗂️ 系統核心模組",
        ["1. 💰 總資產智慧管理", "2. 📈 投資組合與報酬追蹤", "3. 🏦 貸款與利息試算中心", "4. 📝 每日生活記帳"]
    )
    st.sidebar.divider()
    if st.sidebar.button("登出系統", type="secondary", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    current_user = st.session_state.username

    # ---------------------------------------------------------
    # 模組 1：總資產智慧管理 (已加入使用者輸入自有資產功能)
    # ---------------------------------------------------------
    if module == "1. 💰 總資產智慧管理":
        st.title("💰 總資產智慧管理大盤")
        st.write("在此管理您的自有資產（活存、定存、現金等），並整合投資市值與貸款債務。")
        
        # 1. 取得使用者手動新增的自有資產數據
        own_res = supabase.table("own_assets").select("*").eq("username", current_user).execute()
        total_own_cash = sum(x["amount"] for x in own_res.data) if own_res.data else 0
        
        # 2. 取得日常記帳的收支流動餘額
        tx_res = supabase.table("transactions").select("type", "amount").eq("username", current_user).execute()
        flow_cash = sum(x["amount"] for x in tx_res.data if x["type"] == "收入") - sum(x["amount"] for x in tx_res.data if x["type"] == "支出")
        
        # 總現金 = 手動輸入的資產 + 記帳流動餘額
        actual_cash = total_own_cash + flow_cash
        
        # 3. 取得投資市值與貸款數據
        pf_res = supabase.table("portfolio").select("current_value").eq("username", current_user).execute()
        ln_res = supabase.table("loans").select("principal").eq("username", current_user).execute()
        
        inv_val = sum(x["current_value"] for x in pf_res.data) if pf_res.data else 0
        debt = sum(x["principal"] for x in ln_res.data) if ln_res.data else 0
        net_worth = (actual_cash + inv_val) - debt
        
        # 儀表板視覺輸出
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💵 可用現金總額 (含自有資產)", f"{actual_cash:,.0f} 元")
        c2.metric("📊 投資總市值", f"{inv_val:,.0f} 元")
        c3.metric("🚨 總貸款債務", f"{debt:,.0f} 元", delta_color="inverse")
        c4.metric("👑 個人淨資產 (Net Worth)", f"{net_worth:,.0f} 元")
        
        st.divider()
        
        # ---- 這裡就是讓使用者輸入與管理自有資產的地方 ----
        col_input, col_table = st.columns([1, 2])
        
        with col_input:
            st.subheader("➕ 新增/更新自有資產項目")
            st.caption("例如：銀行活存、緊急預備金、郵局定存、儲蓄險現值、黃金等")
            with st.form("own_asset_form"):
                oa_name = st.text_input("資產項目名稱 (如: 富邦銀行活存、郵局定存)")
                oa_amt = st.number_input("當前資產金額 (元)", min_value=0, step=10000, value=50000)
                if st.form_submit_button("確認儲存資產"):
                    if oa_name:
                        # 檢查是否已存在同名資產
                        exist_oa = supabase.table("own_assets").select("id").eq("username", current_user).eq("asset_name", oa_name).execute()
                        if exist_oa.data:
                            supabase.table("own_assets").update({"amount": oa_amt}).eq("id", exist_oa.data[0]["id"]).execute()
                        else:
                            supabase.table("own_assets").insert({"username": current_user, "asset_name": oa_name, "amount": oa_amt}).execute()
                        st.success(f"✅ {oa_name} 已成功記入自有資產！")
                        st.rerun()
        
        with col_table:
            st.subheader("📋 自有資產清單明細")
            if own_res.data:
                df_own = pd.DataFrame(own_res.data)
                st.dataframe(df_own[["asset_name", "amount"]], use_container_width=True)
                
                # 額外提供一個刪除按鈕
                delete_target = st.selectbox("選擇要刪除或歸零的資產項目", ["-- 請選擇 --"] + [x["asset_name"] for x in own_res.data])
                if st.button("❌ 刪除該項資產") and delete_target != "-- 請選擇 --":
                    supabase.table("own_assets").delete().eq("username", current_user).eq("asset_name", delete_target).execute()
                    st.success(f"已刪除 {delete_target}")
                    st.rerun()
            else:
                st.info("💡 目前還沒有手動輸入任何基本資產項目，請在左側表單填入你的第一個銀行活存或定存項目！")
        
        st.divider()
        st.subheader("💡 資產健康度建議")
        if debt > (actual_cash + inv_val) * 0.5:
            st.warning("⚠️ 您的負債比率偏高（超過總資產 50%），建議優先償還高利息貸款，或建立更穩健的應急現金流。")
        else:
            st.success("✅ 您的資產結構相當健康，負債比率在安全範圍內，請繼續保持定期定額投資！")

    # ---------------------------------------------------------
    # 模組 2：投資組合與報酬追蹤
    # ---------------------------------------------------------
    elif module == "2. 📈 投資組合與報酬追蹤":
        st.title("📈 投資組合與報酬追蹤系統")
        t1, t2 = st.tabs(["📊 現有庫存與報酬率", "⚙️ 定期定額複利試算"])
        
        with t1:
            st.subheader("新增/更新投資標庫存")
            with st.form("add_portfolio_form"):
                col_a, col_b, col_c = st.columns(3)
                a_name = col_a.text_input("投資標的名稱 (如: 0050, TSMC, VTI)")
                a_cost = col_b.number_input("投入總本金 (元)", min_value=0, step=1000)
                a_val = col_c.number_input("目前總市值 (元)", min_value=0, step=1000)
                if st.form_submit_button("更新投資庫存"):
                    if a_name:
                        exist = supabase.table("portfolio").select("id").eq("username", current_user).eq("asset_name", a_name).execute()
                        if exist.data:
                            supabase.table("portfolio").update({"cost_basis": a_cost, "current_value": a_val}).eq("id", exist.data[0]["id"]).execute()
                        else:
                            supabase.table("portfolio").insert({"username": current_user, "asset_name": a_name, "cost_basis": a_cost, "current_value": a_val}).execute()
                        st.success(f"📈 {a_name} 庫存資料更新成功！")
                        st.rerun()
            
            st.divider()
            st.subheader("💼 現有投資組合明細")
            pf_data = supabase.table("portfolio").select("*").eq("username", current_user).execute()
            if pf_data.data:
                df = pd.DataFrame(pf_data.data)
                df["報酬損益"] = df["current_value"] - df["cost_basis"]
                df["報酬率 (%)"] = (df["報酬損益"] / df["cost_basis"] * 100).round(2)
                st.dataframe(df[["asset_name", "cost_basis", "current_value", "報酬損益", "報酬率 (%)"]], use_container_width=True)
            else:
                st.info("目前尚無投資庫存資料，請使用上方表單新增。")

        with t2:
            st.subheader("🛠️ 定期定額資產組合比例試算")
            monthly_deposit = st.number_input("每月總投入金額 (元)", min_value=100, value=10000, step=1000)
            total_months = st.number_input("預計投資月數 (月)", min_value=1, value=36, step=1)
            
            default_portfolio = pd.DataFrame([
                {"資產名稱": "美股 ETF (如 VTI)", "配置比例 (%)": 60.0, "預期年化報酬率 (%)": 9.0},
                {"資產名稱": "高股息 ETF (如 0056)", "配置比例 (%)": 30.0, "預期年化報酬率 (%)": 6.0},
                {"資產名稱": "加密貨幣 / 現金", "配置比例 (%)": 10.0, "預期年化報酬率 (%)": 2.0},
            ])
            edited_df = st.data_editor(default_portfolio, num_rows="dynamic", use_container_width=True)
            total_allocation = edited_df["配置比例 (%)"].sum()
            if total_allocation != 100.0:
                st.warning(f"⚠️ 目前配置總比例為 {total_allocation:.1f}%。建議調整至 100%。")
            
            weighted_rate = (edited_df["配置比例 (%)"] * edited_df["預期年化報酬率 (%)"]).sum() / total_allocation / 100 if total_allocation > 0 else 0
            tp, fv = 0, 0
            mr = weighted_rate / 12
            for month in range(1, total_months + 1):
                tp += monthly_deposit
                fv = (fv + monthly_deposit) * (1 + mr)
            
            st.info(f"💡 綜合加權年化報酬率：**{weighted_rate * 100:.2f} %**")
            m1, m2, m3 = st.columns(3)
            m1.metric("總共投入本金", f"{tp:,} 元")
            m2.metric("最終本利和", f"{round(fv):,} 元")
            m3.metric("整體投報率", f"{((fv-tp)/tp*100):.2f} %" if tp > 0 else "0%")

    # ---------------------------------------------------------
    # 模組 3：貸款與利息試算中心
    # ---------------------------------------------------------
    elif module == "3. 🏦 貸款與利息試算中心":
        st.title("🏦 借款、房貸、車貸頭期款與月付款利息試算")
        col_l, col_r = st.columns([1, 1])
        with col_l:
            st.subheader("🧮 貸款條件輸入（本息平均攤還）")
            l_name = st.text_input("貸款名稱項目", value="青年首購房貸")
            l_principal = st.number_input("貸款總金額 (元)", min_value=10000, value=8000000, step=50000)
            l_rate = st.number_input("年貸款利率 (%)", min_value=0.1, value=2.2, step=0.1)
            l_months = st.number_input("貸款年限/期數 (月)", min_value=1, value=360, step=12)
            
            monthly_rate = (l_rate / 100) / 12
            if monthly_rate > 0:
                monthly_payment = (l_principal * monthly_rate * ((1 + monthly_rate) ** l_months)) / (((1 + monthly_rate) ** l_months) - 1)
            else:
                monthly_payment = l_principal / l_months
                
            total_repaid = monthly_payment * l_months
            total_interest = total_repaid - l_principal
            
            if st.button("💾 將此筆貸款存入雲端追蹤"):
                supabase.table("loans").insert({
                    "username": current_user, "loan_name": l_name, 
                    "principal": l_principal, "annual_interest_rate": l_rate, "period_months": l_months
                }).execute()
                st.success(f"🎉 {l_name} 已成功存入您的債務清單！")
                st.rerun()

        with col_r:
            st.subheader("📊 試算報告")
            st.metric("每月應付本息（月付款）", f"{round(monthly_payment):,} 元 / 月")
            st.metric("貸款總本金", f"{l_principal:,} 元")
            st.metric("合約期滿總共支付利息", f"{round(total_interest):,} 元", delta=f"總還款 {round(total_repaid):,} 元", delta_color="inverse")
            
        st.divider()
        st.subheader("📋 我的現有貸款債務清單")
        loans_data = supabase.table("loans").select("*").eq("username", current_user).execute()
        if loans_data.data:
            st.dataframe(pd.DataFrame(loans_data.data)[["loan_name", "principal", "annual_interest_rate", "period_months"]], use_container_width=True)
        else:
            st.info("目前無雲端保存的貸款項目。")

    # ---------------------------------------------------------
    # 模組 4：每日生活記帳
    # ---------------------------------------------------------
    elif module == "4. 📝 每日生活記帳":
        st.title("📝 日常隨手記帳模組")
        col_la, col_ra = st.columns([1, 2])
        with col_la:
            st.subheader("➕ 新增收支明細")
            t_date = st.date_input("日期", datetime.now())
            t_type = st.selectbox("交易類型", ["支出", "收入", "投資投入"])
            t_cat = st.selectbox("分類", ["餐飲食品", "薪資收入", "交通娛樂", "生活雜費", "房租房貸車貸", "股票基金購入"])
            t_amt = st.number_input("金額 (元)", min_value=1, value=100, step=10)
            t_note = st.text_input("備註說明")
            
            if st.button("➕ 寫入帳本", type="primary", use_container_width=True):
                supabase.table("transactions").insert({
                    "username": current_user, "date": str(t_date), "type": t_type, "category": t_cat, "amount": t_amt, "note": t_note
                }).execute()
                st.success("📝 帳目已成功寫入雲端！")
                st.rerun()

        with col_ra:
            st.subheader("📅 歷史收支流水帳明細")
            tx_data = supabase.table("transactions").select("*").eq("username", current_user).order("date", desc=True).execute()
            if tx_data.data:
                df_tx = pd.DataFrame(tx_data.data)
                inc = df_tx[df_tx["type"] == "收入"]["amount"].sum()
                exp = df_tx[df_tx["type"] == "支出"]["amount"].sum()
                st.markdown(f"🟢 **累計總收入**：`{inc:,}` 元 | 🔴 **累計總支出**：`{exp:,}` 元 | ⚖️ **收支淨額**：`{inc-exp:,}` 元")
                st.dataframe(df_tx[["date", "type", "category", "amount", "note"]], use_container_width=True)
            else:
                st.info("尚無記帳明細，快在左側記下今天的第一筆消費吧！")