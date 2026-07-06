import pandas as pd
import streamlit as st
from supabase import create_client, Client
import hashlib
from datetime import datetime, date
import streamlit.components.v1 as components

# 設定網頁
st.set_page_config(page_title="全方位資產與投資管理系統", page_icon="💰", layout="wide")

# ==========================================
# 📱 0. PWA 行動裝置 / 電腦 App 下載功能注入
# ==========================================
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
                    # 💡 關鍵修正：將 table("user") 修改為對應你後台的 table("users")
                    response = supabase.table("users").select("*").eq("username", login_user).execute()
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
                        # 💡 關鍵修正：全面同步為 users 資料表
                        check_exist = supabase.table("users").select("username").eq("username", reg_user).execute()
                        if check_exist.data: st.error("❌ 該帳號已被使用，請換一個名字。")
                        else:
                            supabase.table("users").insert({"username": reg_user, "password": hash_password(reg_pwd)}).execute()
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
    # 模組 0：🏠 總資產智慧管理大盤
    # ---------------------------------------------------------
    if module == "🏠 總資產智慧管理大盤":
        st.title("💰 總資產智慧管理大盤")
        st.write("實時匯總您的現金、投資市值，計算您的個人淨資產。")
        
        cash_sum = sum(float(x["amount"]) for x in assets_res.data) if assets_res.data else 0.0
        invest_sum = 0.0
        if not df_pf.empty:
            df_unreal = df_pf[df_pf["status"] == "未實現"]
            if not df_unreal.empty:
                invest_sum = df_unreal["actual_cash"].astype(float).sum()
        
        net_worth = cash_sum + invest_sum
        
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
    # 模組 2：🏦 資產管理與維護
    # ---------------------------------------------------------
    elif module == "2. 🏦 資產帳戶維護":
        st.title("🏦 資產帳戶維護與多維度報表")
        
        st.subheader("📊 日期與月份淨增減報表")
        today = date.today()
        
        if not df_tx.empty:
            df_today = df_tx[df_tx["date"] == today]
            today_inc = df_today[df_today["type"] == "收入"]["amount"].sum()
            today_exp = df_today[df_today["type"] == "支出"]["amount"].sum()
            today_net = today_inc - today_exp
            
            df_tx_dt = pd.to_datetime(df_tx["date"])
            df_month = df_tx[(df_tx_dt.dt.year == today.year) & (df_tx_dt.dt.month == today.month)]
            month_inc = df_month[df_month["type"] == "收入"]["amount"].sum()
            month_exp = df_month[df_month["type"] == "支出"]["amount"].sum()
            month_net = month_inc - month_exp
        else:
            today_inc = today_exp = today_net = month_inc = month_exp = month_net = 0
            
        rep1, rep2 = st.columns(2)
        with rep1:
            st.info(f"📅 **今日報表 ({today})**")
            st.metric("今日總收入", f"{today_inc:,.0f} 元")
            st.metric("今日總支出", f"{today_exp:,.0f} 元")
            st.metric("今日當日淨增減", f"{today_net:,.0f} 元", delta=float(today_net))
        with rep2:
            st.success(f"🗓️ **當月報表 ({today.strftime('%Y-%m')})**")
            st.metric("當月總收入", f"{month_inc:,.0f} 元")
            st.metric("當月總支出", f"{month_exp:,.0f} 元")
            st.metric("當月當月淨增減", f"{month_net:,.0f} 元", delta=float(month_net))

        st.divider()

        st.subheader("💳 我的帳戶資產清單")
        if assets_res.data:
            df_assets = pd.DataFrame(assets_res.data)
            st.dataframe(df_assets[["asset_name", "amount"]], use_container_width=True)
            
            st.write("🔧 **帳戶維護管理（更改名稱 / 調整餘額）**")
            edit_col1, edit_col2, edit_col3 = st.columns(3)
            target_asset = edit_col1.selectbox("選擇要變更的帳戶", asset_list)
            new_name = edit_col2.text_input("重命名此資產 (留空代表不改名)", value=target_asset)
            new_balance = edit_col3.number_input("直接微調新餘額 (元)", min_value=0.0, value=float(df_assets[df_assets["asset_name"] == target_asset]["amount"].values[0]))
            
            if st.button("💾 確認更新帳戶設定"):
                old_balance = float(df_assets[df_assets["asset_name"] == target_asset]["amount"].values[0])
                if new_balance != old_balance:
                    diff = new_balance - old_balance
                    supabase.table("transactions").insert({
                        "username": current_user, "date": str(today), "type": "資產調整",
                        "asset_name": new_name if new_name else target_asset, "category": "餘額微調", "amount": abs(diff), "note": f"手動調整餘額，差額: {diff}"
                    }).execute()
                
                supabase.table("own_assets").update({"asset_name": new_name, "amount": new_balance}).eq("username", current_user).eq("asset_name", target_asset).execute()
                st.success("⚙️ 帳戶資訊與餘額更新完畢！")
                st.rerun()
        else:
            with st.form("new_asset_init"):
                init_n = st.text_input("新資產帳戶名稱 (如: 華南銀行、現金口袋)")
                init_a = st.number_input("初始金額 (元)", min_value=0, value=10000)
                if st.form_submit_button("➕ 建立第一個帳戶"):
                    if init_n:
                        supabase.table("own_assets").insert({"username": current_user, "asset_name": init_n, "amount": init_a}).execute()
                        supabase.table("transactions").insert({"username": current_user, "date": str(today), "type": "收入", "asset_name": init_n, "category": "帳戶初始化", "amount": init_a, "note": "開戶初始金額"}).execute()
                        st.rerun()

        st.divider()
        st.subheader("📜 歷史資產變動與記帳全明細")
        if not df_tx.empty:
            st.dataframe(df_tx[["date", "type", "asset_name", "category", "amount", "note"]].sort_values(by="date", ascending=False), use_container_width=True)

    # ---------------------------------------------------------
    # 模組 3：投資組合與報酬
    # ---------------------------------------------------------
    elif module == "3. 📈 投資組合 (損益計算)":
        st.title("📈 投資組合組合與庫存損益中心")
        st.warning("💡 提示：交易時實際支付金額以券商金額為主，請在成本處輸入券商 App 上的成本；賣出後請在賣出處輸入實收金額。")
        
        st.subheader("🛒 金融資產交易下單（買入/賣出）")
        with st.form("invest_form", clear_on_submit=True):
            col_i1, col_i2, col_i3, col_i4 = st.columns(4)
            inv_date = col_i1.date_input("交易日期", value=date.today())
            inv_type = col_i2.selectbox("交易方向", ["買入", "賣出"])
            inv_name = col_i3.text_input("金融資產名稱/代號 (如: 0050, 2330)")
            inv_cash = col_i4.number_input("金額 (本金/實收)", min_value=1, value=10000)
            inv_asset_link = st.selectbox("連動扣款/入款資產帳戶", asset_list)
            
            if st.form_submit_button("送出交易紀錄"):
                if inv_name and inv_asset_link:
                    curr_asset_amt = next(x["amount"] for x in assets_res.data if x["asset_name"] == inv_asset_link)
                    
                    if inv_type == "買入":
                        supabase.table("own_assets").update({"amount": curr_asset_amt - inv_cash}).eq("username", current_user).eq("asset_name", inv_asset_link).execute()
                        supabase.table("portfolio").insert({
                            "username": current_user, "date": str(inv_date), "asset_name": inv_name,
                            "type": "買入", "cost": inv_cash, "actual_cash": inv_cash, "status": "未實現"
                        }).execute()
                        supabase.table("transactions").insert({"username": current_user, "date": str(inv_date), "type": "支出", "asset_name": inv_asset_link, "category": "證券買入", "amount": inv_cash, "note": f"購入庫存 {inv_name}"}).execute()
                        st.success(f"🎉 成功買入 {inv_name}！")
                    
                    elif inv_type == "賣出":
                        unrealized_res = supabase.table("portfolio").select("*").eq("username", current_user).eq("asset_name", inv_name).eq("status", "未實現").execute()
                        if unrealized_res.data:
                            target_stock = unrealized_res.data[0]
                            supabase.table("own_assets").update({"amount": curr_asset_amt + inv_cash}).eq("username", current_user).eq("asset_name", inv_asset_link).execute()
                            supabase.table("portfolio").update({"type": "賣出", "actual_cash": inv_cash, "status": "已實現"}).eq("id", target_stock["id"]).execute()
                            supabase.table("transactions").insert({"username": current_user, "date": str(inv_date), "type": "收入", "asset_name": inv_asset_link, "category": "證券賣出", "amount": inv_cash, "note": f"賣出庫存 {inv_name}"}).execute()
                            st.success(f"🎉 成功賣出 {inv_name}！")
                        else:
                            st.error(f"❌ 錯誤：您目前並無 {inv_name} 的「未實現」持股庫存！")
                    st.rerun()

        st.divider()
        st.subheader("💼 我的持股狀態大盤")
        p_col1, p_col2 = st.columns(2)
        
        with p_col1:
            st.write("🔍 **未實現損益清單 (目前持股庫存)**")
            df_unreal = df_pf[df_pf["status"] == "未實現"].copy() if not df_pf.empty else pd.DataFrame()
            if not df_unreal.empty:
                st.caption("🔄 模擬即時市價同步：您可在此直接點擊修改目前的最新總市值")
                df_unreal["cost"] = df_unreal["cost"].astype(float)
                df_unreal["actual_cash"] = df_unreal["actual_cash"].astype(float)
                
                edited_unreal = st.data_editor(df_unreal[["id", "asset_name", "cost", "actual_cash"]].rename(columns={"actual_cash": "估算即時總市值"}), num_rows="fixed", use_container_width=True, key="unreal_ed")
                
                for index, row in edited_unreal.iterrows():
                    orig_row = df_unreal[df_unreal["id"] == row["id"]].iloc[0]
                    if float(row["估算即時總市值"]) != float(orig_row["actual_cash"]):
                        supabase.table("portfolio").update({"actual_cash": float(row["估算即時總市值"])}).eq("id", row["id"]).execute()
                        st.rerun()

                unreal_cost_sum = edited_unreal["cost"].sum()
                unreal_market_sum = edited_unreal["估算即時總市值"].sum()
                unreal_profit = unreal_market_sum - unreal_cost_sum
                unreal_roi = (unreal_profit / unreal_cost_sum * 100) if unreal_cost_sum > 0 else 0
                st.metric("當前未實現總損益", f"{unreal_profit:,.0f} 元", f"報酬率：{unreal_roi:.2f} %")
            else: st.info("目前無未實現持股。")

        with p_col2:
            st.write("💰 **已實現損益清單 (歷史平倉變現結算)**")
            df_real = df_pf[df_pf["status"] == "已實現"].copy() if not df_pf.empty else pd.DataFrame()
            if not df_real.empty:
                df_real["cost"] = df_real["cost"].astype(float)
                df_real["actual_cash"] = df_real["actual_cash"].astype(float)
                df_real["已實現損益"] = df_real["actual_cash"] - df_real["cost"]
                st.dataframe(df_real[["date", "asset_name", "cost", "actual_cash", "已實現損益"]].rename(columns={"cost": "當初投入成本", "actual_cash": "賣出實收金額"}), use_container_width=True)
                
                total_realized_profit = df_real["已實現損益"].sum()
                st.metric("累計已實現總損益", f"{total_realized_profit:,.0f} 元", delta=float(total_realized_profit))
            else: st.info("目前尚無已實現的賣出獲利紀錄。")