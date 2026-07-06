import pandas as pd
import streamlit as st
from supabase import create_client, Client
import hashlib
from datetime import datetime, date
import streamlit.components.v1 as components
import urllib.request
import json

# 💡 安全引入自動刷新與 yfinance
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

try:
    import yfinance as yf
except ImportError:
    yf = None

# 設定網頁
st.set_page_config(page_title="全方位資產與投資管理系統", page_icon="💰", layout="wide")

# ==========================================
# ⏱️ 自動刷新機制設定 (每 30 秒畫面自動跳動更新市價與匯率)
# ==========================================
if st_autorefresh is not None:
    st_autorefresh(interval=30000, limit=1000, key="stock_market_refresh")
else:
    components.html(
        """
        <script>
        setTimeout(function(){
            window.parent.postMessage({type: 'streamlit:rerun'}, '*');
        }, 30000);
        </script>
        """,
        height=0
    )

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

# 抓取即時價格的通用函式
def get_current_price(symbol: str):
    symbol = symbol.strip()
    # 如果是純數字，代表是台股，嘗試後綴
    if symbol.isdigit():
        lookups = [f"{symbol}.TW", f"{symbol}.TWO"]
    else:
        lookups = [symbol] # 美股代號如 AAPL, TSLA 直接查詢

    for ticker_str in lookups:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_str}?interval=1d&range=2d"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                meta = data['chart']['result'][0]['meta']
                price = meta.get('regularMarketPrice')
                if price and float(price) > 0:
                    return float(price)
        except:
            pass

        if yf is not None:
            try:
                ticker = yf.Ticker(ticker_str)
                todays_data = ticker.history(period="2d")
                if not todays_data.empty:
                    latest_price = float(todays_data['Close'].iloc[-1])
                    if latest_price > 0:
                        return latest_price
            except:
                continue
    return None

# 🌟 新增：抓取即時美金對新台幣匯率 (USDTWD=X)
def get_usd_to_twd_rate():
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/USDTWD=X?interval=1d&range=2d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            meta = data['chart']['result'][0]['meta']
            rate = meta.get('regularMarketPrice')
            if rate and float(rate) > 0:
                return float(rate)
    except:
        pass
    
    if yf is not None:
        try:
            ticker = yf.Ticker("USDTWD=X")
            todays_data = ticker.history(period="2d")
            if not todays_data.empty:
                return float(todays_data['Close'].iloc[-1])
        except:
            pass
    return 32.5 # 萬一網路都失敗的保底備用匯率

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
    
    # 獲取當前即時匯率並顯示在側邊欄
    usd_twd_rate = get_usd_to_twd_rate()
    st.sidebar.metric("💵 當前即時美金匯率 (連網)", f"{usd_twd_rate:.2f} TWD")
    st.sidebar.caption("🔄 系統已啟動交易所連動，每 30 秒自動更新即時行情與匯率")
    
    module = st.sidebar.radio(
        "🗂️ 核心功能選單",
        ["🏠 總資產智慧管理大盤", "1. 📝 日常記帳 (動態連動)", "2. 🏦 資產帳戶與多類別維護", "3. 📈 投資組合 (交易所即時連動)"]
    )
    st.sidebar.divider()
    if st.sidebar.button("登出系統", type="secondary", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    try:
        assets_res = supabase.table("own_assets").select("*").eq("username", current_user).execute()
        tx_res = supabase.table("transactions").select("*").eq("username", current_user).execute()
        pf_res = supabase.table("portfolio").select("*").eq("username", current_user).execute()
    except Exception as api_err:
        st.error(f"📡 資料庫連線或欄位對照出錯。錯誤: {api_err}")
        st.stop()

    asset_list = [x["asset_name"] for x in assets_res.data] if assets_res.data else []
    raw_assets = assets_res.data if assets_res.data else []
    parsed_assets = []
    for a in raw_assets:
        name = a["asset_name"]
        if name.startswith("[") and "]" in name:
            pos = name.find("]")
            a_type = name[1:pos]
            display_name = name[pos+1:]
        else:
            a_type = "未分類現金"
            display_name = name
        
        parsed_assets.append({
            "id_key": name, 
            "資產類別": a_type, 
            "帳戶名稱": display_name, 
            "餘額 (元)": float(a["amount"])
        })
    df_assets_parsed = pd.DataFrame(parsed_assets) if parsed_assets else pd.DataFrame(columns=["id_key", "資產類別", "帳戶名稱", "餘額 (元)"])

    df_tx_all = pd.DataFrame(tx_res.data) if tx_res.data else pd.DataFrame(columns=["date", "type", "asset_name", "category", "amount", "note"])
    if not df_tx_all.empty:
        df_tx_all["date"] = pd.to_datetime(df_tx_all["date"]).dt.date
        df_tx_all["amount"] = df_tx_all["amount"].astype(float)
        df_tx = df_tx_all[~df_tx_all["category"].isin(["證券買入", "證券賣出", "餘額微調", "帳戶劃轉-轉出", "帳戶劃轉-轉入", "歷史庫存導入"])].copy()
    else:
        df_tx = df_tx_all.copy()
        
    df_pf = pd.DataFrame(pf_res.data) if pf_res.data else pd.DataFrame()

    # ---------------------------------------------------------
    # 模組 0：🏠 總資產智慧管理大盤
    # ---------------------------------------------------------
    if module == "🏠 總資產智慧管理大盤":
        st.title("💰 總資產智慧管理大盤")
        
        cash_sum = sum(float(x["amount"]) for x in raw_assets)
        invest_sum_twd = 0.0 # 改為台幣加總計價
        
        if not df_pf.empty:
            df_unreal = df_pf[df_pf["status"] == "未實現"].copy()
            if not df_unreal.empty:
                for idx, row in df_unreal.iterrows():
                    stock_id = row["asset_name"].strip()
                    current_mkt_price = get_current_price(stock_id)
                    buy_price = float(row["cost"])
                    inserted_cash = float(row["actual_cash"])
                    
                    # 判斷是否為美股
                    is_us_stock = not stock_id.isdigit()
                    multiplier = usd_twd_rate if is_us_stock else 1.0
                    
                    if current_mkt_price is not None and buy_price > 0:
                        shares = inserted_cash / buy_price
                        current_value = shares * current_mkt_price
                        invest_sum_twd += (current_value * multiplier)
                    else:
                        invest_sum_twd += (inserted_cash * multiplier)
        
        net_worth = cash_sum + invest_sum_twd
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💵 總帳戶餘額 (含各類資產)", f"{cash_sum:,.0f} 元")
        m2.metric("📊 投資總市值 (台美股折合新台幣)", f"{invest_sum_twd:,.0f} 元")
        m3.metric("🚨 總貸款債務", "0 元")
        m4.metric("👑 個人淨資產 (Net Worth)", f"{net_worth:,.0f} 元")
        
        st.divider()
        st.subheader("📊 多元資產類別分佈比例")
        if not df_assets_parsed.empty:
            df_summary = df_assets_parsed.groupby("資產類別")["餘額 (元)"].sum().reset_index()
            if invest_sum_twd > 0:
                df_summary = pd.concat([df_summary, pd.DataFrame([{"資產類別": "證券投資 (台美股加總)", "餘額 (元)": invest_sum_twd}])], ignore_index=True)
            
            df_summary["所佔比例"] = df_summary["餘額 (元)"].apply(lambda x: f"{(x / net_worth * 100):.1f} %" if net_worth > 0 else "0%")
            st.table(df_summary.rename(columns={"餘額 (元)": "總金額 (元)"}))
        else:
            st.info("歡迎使用本系統！請先前往「2. 🏦 資產帳戶維護」建立您的第一個資產帳戶。")

    # ---------------------------------------------------------
    # 模組 1：📝 日常記帳
    # ---------------------------------------------------------
    elif module == "1. 📝 日常記帳 (動態連動)":
        st.title("📝 隨手日常記帳中心")
        
        if not asset_list:
            st.warning("⚠️ 您目前沒有任何資產帳戶，請先前往「2. 🏦 資產帳戶與多類別維護」建立帳戶！")
        else:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("📥 新增日常收支")
                with st.form("tx_form", clear_on_submit=True):
                    tx_date = st.date_input("記帳日期", value=date.today())
                    tx_type = st.selectbox("交易類型", ["支出", "收入"])
                    
                    asset_labels = {}
                    for x in raw_assets:
                        n = x["asset_name"]
                        asset_labels[n] = n.replace("[", "").replace("]", " -> ")
                    tx_asset = st.selectbox("使用帳戶(資產)", options=list(asset_labels.keys()), format_func=lambda x: asset_labels[x])
                    
                    tx_cate = st.text_input("分類 (如: 餐飲、交通、薪水)")
                    tx_amt = st.number_input("金額 (元)", min_value=1, value=100)
                    tx_note = st.text_input("備註")
                    
                    if st.form_submit_button("確認記帳"):
                        supabase.table("transactions").insert({
                            "username": current_user, "date": str(tx_date), "type": tx_type,
                            "asset_name": tx_asset, "category": tx_cate, "amount": tx_amt, "note": tx_note
                        }).execute()
                        
                        current_asset_amt = next(x["amount"] for x in raw_assets if x["asset_name"] == tx_asset)
                        new_amt = current_asset_amt + tx_amt if tx_type == "收入" else current_asset_amt - tx_amt
                        supabase.table("own_assets").update({"amount": new_amt}).eq("username", current_user).eq("asset_name", tx_asset).execute()
                        
                        st.success("🎉 記帳成功，資產已即時連動變更！")
                        st.rerun()
            with c2:
                st.subheader("📋 本日最新日常記帳明細")
                today_tx = df_tx[df_tx["date"] == date.today()] if not df_tx.empty else pd.DataFrame()
                if not today_tx.empty:
                    st.dataframe(today_tx[["date", "type", "asset_name", "category", "amount", "note"]], use_container_width=True)
                else:
                    st.info("💡 今天還沒有常規消費記帳明細喔！")

    # ---------------------------------------------------------
    # 模組 2：🏦 資產帳戶維護
    # ---------------------------------------------------------
    elif module == "2. 🏦 資產帳戶與多類別維護":
        st.title("🏦 資產帳戶維護與多維度報表")
        
        tab_asset1, tab_asset2 = st.tabs(["➕ 建立新帳戶", "🔄 帳戶資金劃轉"])
        
        with tab_asset1:
            st.subheader("建立新資產帳戶（支援多種類別）")
            with st.form("new_asset_categorical", clear_on_submit=True):
                col_a, col_b, col_c = st.columns(3)
                asset_class = col_a.selectbox("選擇資產類別", ["現金口袋", "活期存款", "數位帳戶", "定期存款", "外幣資產", "虛擬貨幣", "實體資產(機車/汽車)", "其他資產"])
                custom_name = col_b.text_input("輸入帳戶/資產名稱 (如: 第一銀行、台新 Richart、美金現鈔)")
                init_balance = col_c.number_input("初始餘額 / 價值 (元)", min_value=0, value=0)
                
                submit_btn = st.form_submit_button("💾 立即新增此資產帳戶", use_container_width=True, type="primary")
                
                if submit_btn:
                    if custom_name.strip():
                        combined_name = f"[{asset_class}]{custom_name.strip()}"
                        if combined_name in asset_list:
                            st.error("❌ 該資產名稱已存在！")
                        else:
                            try:
                                supabase.table("own_assets").insert({"username": current_user, "asset_name": combined_name, "amount": init_balance}).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "收入", "asset_name": combined_name, "category": "帳戶初始化", "amount": init_balance, "note": f"開戶全新多類別資產：{asset_class}"}).execute()
                                
                                st.success(f"🎉 成功建立 [{asset_class}] {custom_name} 帳戶！")
                                st.rerun()
                            except Exception as ex: st.error(f"資料庫寫入失敗: {ex}")
                    else: st.warning("⚠️ 請輸入資產帳戶名稱。")
                    
        with tab_asset2:
            st.subheader("🔄 內部資產帳戶資金劃轉")
            if len(asset_list) < 2:
                st.info("💡 至少需要建立兩個資產帳戶才能使用資金劃轉功能。")
            else:
                with st.form("transfer_form", clear_on_submit=True):
                    col_t1, col_t2, col_t3 = st.columns(3)
                    from_asset = col_t1.selectbox("來源帳戶 (轉出)", asset_list, format_func=lambda x: x.replace("[", "").replace("]", " -> "))
                    to_asset = col_t2.selectbox("目的帳戶 (轉入)", asset_list, format_func=lambda x: x.replace("[", "").replace("]", " -> "))
                    transfer_amt = col_t3.number_input("劃轉金額 (元)", min_value=1, value=1000)
                    transfer_note = st.text_input("劃轉備註 (例如：手動轉帳、存入數位高利活存)", value="內部帳戶劃轉")
                    
                    if st.form_submit_button("🚀 確認執行劃轉"):
                        if from_asset == to_asset:
                            st.error("❌ 來源帳戶與目的帳戶不能相同！")
                        else:
                            try:
                                amt_from = next(x["amount"] for x in raw_assets if x["asset_name"] == from_asset)
                                amt_to = next(x["amount"] for x in raw_assets if x["asset_name"] == to_asset)
                                
                                supabase.table("own_assets").update({"amount": amt_from - transfer_amt}).eq("username", current_user).eq("asset_name", from_asset).execute()
                                supabase.table("own_assets").update({"amount": amt_to + transfer_amt}).eq("username", current_user).eq("asset_name", to_asset).execute()
                                
                                supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "支出", "asset_name": from_asset, "category": "帳戶劃轉-轉出", "amount": transfer_amt, "note": f"{transfer_note} (流向: {to_asset})"}).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "收入", "asset_name": to_asset, "category": "帳戶劃轉-轉入", "amount": transfer_amt, "note": f"{transfer_note} (來源: {from_asset})"}).execute()
                                
                                st.success(f"🎉 成功由 {from_asset} 劃轉 {transfer_amt:,.0f} 元至 {to_asset}！")
                                st.rerun()
                            except Exception as ex: st.error(f"劃轉失敗: {ex}")

        st.divider()
        st.subheader("💳 我的帳戶資產分佈明細")
        if not df_assets_parsed.empty:
            st.dataframe(df_assets_parsed[["資產類別", "帳戶名稱", "餘額 (元)"]], use_container_width=True)
            
            st.write("🔧 **帳戶進階設定管理 (編輯名稱、調整餘額、刪除帳戶)**")
            target_asset = st.selectbox("選擇要處理的帳戶", options=df_assets_parsed["id_key"].tolist(), format_func=lambda x: x.replace("[", "").replace("]", " -> "), key="asset_manager_select")
            current_row = df_assets_parsed[df_assets_parsed["id_key"] == target_asset].iloc[0]
            
            edit_col1, edit_col2 = st.columns(2)
            new_name = edit_col1.text_input("重命名此資產名稱 (免填分類標籤)", value=current_row["帳戶名稱"])
            new_balance = edit_col2.number_input("直接微調新餘額 (元)", min_value=0.0, value=float(current_row["餘額 (元)"]))
            
            btn_col1, btn_col2 = st.columns([1, 1])
            
            if btn_col1.button("💾 儲存變更設定", use_container_width=True, type="primary"):
                old_balance = float(current_row["餘額 (元)"])
                fixed_combined_name = f"[{current_row['資產類別']}]{new_name}"
                
                if new_balance != old_balance:
                    diff = new_balance - old_balance
                    supabase.table("transactions").insert({
                        "username": current_user, "date": str(date.today()), "type": "資產調整",
                        "asset_name": fixed_combined_name, "category": "餘額微調", "amount": abs(diff), "note": f"手動調整餘額，差額: {diff}"
                    }).execute()
                
                supabase.table("own_assets").update({"asset_name": fixed_combined_name, "amount": new_balance}).eq("username", current_user).eq("asset_name", target_asset).execute()
                st.success("⚙️ 帳戶資訊與餘額更新完畢！")
                st.rerun()
                
            if btn_col2.button("🗑️ 徹底刪除此資產帳戶", use_container_width=True, type="secondary"):
                try:
                    supabase.table("own_assets").delete().eq("username", current_user).eq("asset_name", target_asset).execute()
                    supabase.table("transactions").delete().eq("username", current_user).eq("asset_name", target_asset).execute()
                    st.success(f"💥 已成功將帳戶「{target_asset}」及其關聯記帳明細完整移除！")
                    st.rerun()
                except Exception as del_err: st.error(f"刪除失敗，錯誤訊息: {del_err}")
        else:
            st.info("💡 目前尚未建立任何資產帳戶，請使用上方表單建立一個吧！")

    # ---------------------------------------------------------
    # 模組 3：📈 投資組合 (整合 💱 匯率自動換算功能)
    # ---------------------------------------------------------
    elif module == "3. 📈 投資組合 (交易所即時連動)":
        st.title("📈 交易所即時連動投資組合")
        st.info(f"💡 買入股票屬於資產型態轉換。當前聯網即時美金匯率： **{usd_twd_rate:.2f}** TWD。系統會自動偵測美金股票代號並即時換算。")
        
        tab_inv1, tab_inv2 = st.tabs(["🛒 常規日常交易下單", "📥 導入系統前舊投資持股"])
        
        with tab_inv1:
            st.subheader("金融資產交易下單（動態連動扣款/入款）")
            with st.form("invest_form", clear_on_submit=True):
                col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns(5)
                inv_date = col_i1.date_input("交易日期", value=date.today())
                inv_type = col_i2.selectbox("交易方向", ["買入", "賣出"])
                inv_name = col_i3.text_input("股票代號 (台股如: 2330 / 美股如: AAPL)", key="stock_code_regular")
                inv_price = col_i4.number_input("買入/賣出單價 (原幣別價)", min_value=0.1, value=100.0)
                inv_qty = col_i5.number_input("交易股數", min_value=1, value=1000)
                inv_asset_link = st.selectbox("連動扣款/入款資產帳戶", asset_list, format_func=lambda x: x.replace("[", "").replace("]", " -> "))
                
                if st.form_submit_button("送出交易紀錄"):
                    if inv_name and inv_asset_link:
                        total_cash_flow = inv_price * inv_qty
                        curr_asset_amt = next(x["amount"] for x in raw_assets if x["asset_name"] == inv_asset_link)
                        
                        if inv_type == "買入":
                            supabase.table("own_assets").update({"amount": curr_asset_amt - total_cash_flow}).eq("username", current_user).eq("asset_name", inv_asset_link).execute()
                            supabase.table("portfolio").insert({
                                "username": current_user, "date": str(inv_date), "asset_name": inv_name.strip().upper(),
                                "type": "買入", "cost": inv_price, "actual_cash": total_cash_flow, "status": "未實現"
                            }).execute()
                            supabase.table("transactions").insert({"username": current_user, "date": str(inv_date), "type": "投資轉換", "asset_name": inv_asset_link, "category": "證券買入", "amount": total_cash_flow, "note": f"購入庫存 {inv_name.upper()} {inv_qty}股，成本 {inv_price}"}).execute()
                            st.success(f"🎉 成功買入 {inv_name.upper()}！")
                        
                        elif inv_type == "賣出":
                            unrealized_res = supabase.table("portfolio").select("*").eq("username", current_user).eq("asset_name", inv_name.strip().upper()).eq("status", "未實現").execute()
                            if unrealized_res.data:
                                target_stock = unrealized_res.data[0]
                                supabase.table("own_assets").update({"amount": curr_asset_amt + total_cash_flow}).eq("username", current_user).eq("asset_name", inv_asset_link).execute()
                                supabase.table("portfolio").update({"type": "賣出", "cost": inv_price, "actual_cash": total_cash_flow, "status": "已實現"}).eq("id", target_stock["id"]).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(inv_date), "type": "投資結算", "asset_name": inv_asset_link, "category": "證券賣出", "amount": total_cash_flow, "note": f"賣出庫存 {inv_name.upper()}，實收 {total_cash_flow}"}).execute()
                                st.success(f"🎉 成功賣出 {inv_name.upper()}！")
                            else: st.error(f"❌ 錯誤：您目前並無 {inv_name.upper()} 的持股庫存！")
                        st.rerun()
                        
        with tab_inv2:
            st.subheader("📥 導入使用系統前購入的歷史庫存")
            st.caption("💡 此功能僅增加未實現庫存市值，**絕不扣除**任何帳戶金額。")
            with st.form("history_invest_form", clear_on_submit=True):
                col_h1, col_h2, col_h3, col_h4 = st.columns(4)
                hist_date = col_h1.date_input("當初購入日期", value=date.today())
                hist_name = col_h2.text_input("股票代號 (台股如: 2454 / 美股如: NVDA)", key="stock_code_history")
                hist_price = col_h3.number_input("當初買入平均單價 (原幣別價)", min_value=0.1, value=100.0)
                hist_qty = col_h4.number_input("持有股數", min_value=1, value=1000)
                
                if st.form_submit_button("📥 立即加入歷史庫存庫"):
                    if hist_name.strip():
                        total_hist_cost = hist_price * hist_qty
                        try:
                            supabase.table("portfolio").insert({
                                "username": current_user, "date": str(hist_date), "asset_name": hist_name.strip().upper(),
                                "type": "買入", "cost": hist_price, "actual_cash": total_hist_cost, "status": "未實現"
                            }).execute()
                            supabase.table("transactions").insert({
                                "username": current_user, "date": str(date.today()), "type": "收入", 
                                "asset_name": "投資組合庫存", "category": "歷史庫存導入", "amount": total_hist_cost, "note": f"系統初始化：導入舊持有股票 {hist_name.upper()} 共 {hist_qty} 股"
                            }).execute()
                            
                            st.success(f"🎉 歷史庫存 {hist_name.upper()} 導入成功！已納入即時大盤計算。")
                            st.rerun()
                        except Exception as ex: st.error(f"導入失敗: {ex}")
                    else: st.warning("⚠️ 請填寫股票代號。")

        st.divider()
        st.subheader("💼 交易所即時連動大盤庫存 (美股已即時換算新台幣，每 30 秒自動更新)")
        p_col1, p_col2 = st.columns(2)
        
        df_unreal = df_pf[df_pf["status"] == "未實現"].copy() if not df_pf.empty else pd.DataFrame()
        
        with p_col1:
            st.write("🔍 **未實現損益（各幣別皆自動換算為新台幣呈現）**")
            if not df_unreal.empty:
                display_currency = []
                live_prices_twd = []
                live_market_values_twd = []
                live_profits_twd = []
                cost_sum_twd = [] # 用來存換算成台幣後的本金
                
                for index, row in df_unreal.iterrows():
                    stock_id = row["asset_name"].strip()
                    current_mkt_price = get_current_price(stock_id)
                    buy_price = float(row["cost"])
                    inserted_cash = float(row["actual_cash"])
                    
                    # 判斷是否為美股 (英文代號則為美股)
                    is_us_stock = not stock_id.isdigit()
                    currency_tag = "USD" if is_us_stock else "TWD"
                    multiplier = usd_twd_rate if is_us_stock else 1.0
                    
                    if current_mkt_price is not None and buy_price > 0:
                        shares = inserted_cash / buy_price
                        current_value = shares * current_mkt_price
                        profit = current_value - inserted_cash
                    else:
                        current_mkt_price = buy_price
                        current_value = inserted_cash
                        profit = 0.0
                    
                    display_currency.append(currency_tag)
                    # 全數乘上匯率乘數，轉為新台幣
                    live_prices_twd.append(f"{current_mkt_price * multiplier:,.2f} 元")
                    live_market_values_twd.append(current_value * multiplier)
                    live_profits_twd.append(profit * multiplier)
                    cost_sum_twd.append(inserted_cash * multiplier)
                
                df_unreal["計價幣別"] = display_currency
                df_unreal["交易所當前市價(台幣)"] = live_prices_twd
                df_unreal["當前最新總市值(台幣)"] = live_market_values_twd
                df_unreal["即時未實現損益(台幣)"] = live_profits_twd
                df_unreal["投入本金(台幣)"] = cost_sum_twd
                
                st.dataframe(
                    df_unreal[["asset_name", "計價幣別", "date", "cost", "投入本金(台幣)", "交易所當前市價(台幣)", "當前最新總市值(台幣)", "即時未實現損益(台幣)"]]
                    .rename(columns={"asset_name": "股票代號", "date": "購入日期", "cost": "買入單價(原幣)"}),
                    use_container_width=True
                )
                
                # 計算台美股完美大加總
                total_cost_twd_all = sum(cost_sum_twd)
                total_market_twd_all = sum(live_market_values_twd)
                total_profit_twd_all = total_market_twd_all - total_cost_twd_all
                total_roi_all = (total_profit_twd_all / total_cost_twd_all * 100) if total_cost_twd_all > 0 else 0
                
                st.metric("📊 台美全庫存即時總損益 (新台幣大加總)", f"{total_profit_twd_all:,.0f} 元", f"綜合即時總報酬率：{total_roi_all:.2f} %")
            else:
                st.info("目前無未實現持股。")

        with p_col2:
            st.write("💰 **已實現損益（歷史平倉獲利結算）**")
            df_real = df_pf[df_pf["status"] == "已實現"].copy() if not df_pf.empty else pd.DataFrame()
            if not df_real.empty:
                df_real["cost"] = df_real["cost"].astype(float)
                df_real["actual_cash"] = df_real["actual_cash"].astype(float)
                st.dataframe(df_real[["date", "asset_name", "actual_cash"]].rename(columns={"date": "結算日期", "asset_name": "股票代號", "actual_cash": "賣出變現總額(原幣)"}), use_container_width=True)
            else: 
                st.info("目前尚無已實現的賣出獲利紀錄。")

        # 庫存手動刪除進階功能
        if not df_unreal.empty:
            st.divider()
            st.subheader("🔧 庫存進階設定管理")
            
            df_unreal["selector_label"] = df_unreal.apply(
                lambda r: f"代號: {r['asset_name']} ({r['計價幣別']}) | 購入日: {r['date']} | 投入本金(台幣): {float(r['投入本金(台幣)']):,.0f}元", axis=1
            )
            target_stock_label = st.selectbox("選擇要徹底刪除的持股庫存紀錄", options=df_unreal["selector_label"].tolist())
            
            selected_row = df_unreal[df_unreal["selector_label"] == target_stock_label].iloc[0]
            target_id = selected_row["id"]
            target_code = selected_row["asset_name"]
            
            if st.button(f"🗑️ 徹底刪除代號 {target_code} 的這筆持股庫存", type="secondary", use_container_width=True):
                try:
                    supabase.table("portfolio").delete().eq("id", target_id).eq("username", current_user).execute()
                    st.success(f"💥 已成功將該筆股票庫存紀錄自系統中完整抹除！")
                    st.rerun()
                except Exception as del_err:
                    st.error(f"刪除庫存失敗: {del_err}")