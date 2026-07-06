import pandas as pd
import streamlit as st
from supabase import create_client, Client
import hashlib
from datetime import datetime, date, timedelta
import streamlit.components.v1 as components
import urllib.request
import json
import random

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
st.set_page_config(page_title="🦉 富豪多鄰國：自訂挑戰版", page_icon="🦉", layout="wide")

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

def get_current_price(symbol: str):
    symbol = symbol.strip()
    if symbol.isdigit():
        lookups = [f"{symbol}.TW", f"{symbol}.TWO"]
    else:
        lookups = [symbol]

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
    return 32.5

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
    st.title("🦉 歡迎來到 富豪多鄰國 Asset-Duolingo")
    st.subheader("自訂你的儲蓄賽道，讓理財變得像玩遊戲一樣好玩！")
    tab1, tab2 = st.tabs(["🔑 會員登入", "📝 快速註冊"])
    
    with tab1:
        login_user = st.text_input("帳號 (使用者名稱)", key="login_user")
        login_pwd = st.text_input("密碼", type="password", key="login_pwd")
        
        if st.button("立即登入並接受 DuDu 監督", type="primary", use_container_width=True):
            if login_user and login_pwd:
                try:
                    response = supabase.table("users").select("*").eq("username", login_user).execute()
                    if response.data:
                        user_record = response.data[0]
                        if user_record["password"] == hash_password(login_pwd):
                            st.session_state.logged_in = True
                            st.session_state.username = login_user
                            st.success(f"🎉 歡迎回來！DuDu 正在盯著你的荷包喔！")
                            st.rerun()
                        else: st.error("❌ 密碼錯誤，DuDu 在瞪你囉！")
                    else: st.error("❌ 找不到帳號，快去註冊加入挑戰！")
                except Exception as ex: st.error(f"資料庫錯誤: {ex}")
            else: st.warning("⚠️ 請填寫完整帳號與密碼。")
                
    with tab2:
        reg_user = st.text_input("設定新帳號", key="reg_user")
        reg_pwd = st.text_input("設定新密碼", type="password", key="reg_pwd")
        reg_pwd_confirm = st.text_input("確認新密碼", type="password", key="reg_pwd_confirm")
        
        if st.button("建立帳號並開啟自訂存錢挑戰", use_container_width=True):
            if reg_user and reg_pwd and reg_pwd_confirm:
                if reg_pwd != reg_pwd_confirm: st.error("❌ 兩次輸入的密碼不一致")
                else:
                    try:
                        check_exist = supabase.table("users").select("username").execute()
                        if any(x["username"] == reg_user for x in check_exist.data): 
                            st.error("❌ 該帳號已被佔用！")
                        else:
                            # 預設幫使用者寫入初始挑戰欄位資訊
                            supabase.table("users").insert({
                                "username": reg_user, 
                                "password": hash_password(reg_pwd),
                                "challenge_title": "大二前的存錢大作戰",
                                "challenge_target": 1000000.0,
                                "challenge_start": str(date.today()),
                                "challenge_end": str(date.today() + timedelta(days=365))
                            }).execute()
                            st.success("🎉 註冊成功！快切換至「會員登入」頁籤吧！")
                    except Exception as ex: st.error(f"註冊失敗: {ex}")
            else: st.warning("⚠️ 請填寫所有註冊欄位。")

# ==========================================
# 📊 4. 主程式控制核心 (會員登入後)
# ==========================================
else:
    current_user = st.session_state.username
    usd_twd_rate = get_usd_to_twd_rate()
    
    # ---------------------------------------------------------
    # 🦉 獲取使用者雲端資料與自訂挑戰設定
    # ---------------------------------------------------------
    try:
        user_res = supabase.table("users").select("*").eq("username", current_user).execute()
        assets_res = supabase.table("own_assets").select("*").eq("username", current_user).execute()
        tx_res = supabase.table("transactions").select("*").eq("username", current_user).execute()
        pf_res = supabase.table("portfolio").select("*").eq("username", current_user).execute()
    except Exception as api_err:
        st.error(f"📡 資料庫連線出錯: {api_err}")
        st.stop()

    user_info = user_res.data[0] if user_res.data else {}
    
    # 解析或初始化挑戰資料（防止舊帳號無欄位問題）
    c_title = user_info.get("challenge_title", "我的自訂理財大挑戰")
    try:
        c_target = float(user_info.get("challenge_target", 500000))
    except:
        c_target = 500000.0
        
    try:
        c_start = datetime.strptime(user_info.get("challenge_start", str(date.today())), "%Y-%m-%d").date()
        c_end = datetime.strptime(user_info.get("challenge_end", str(date.today() + timedelta(days=365))), "%Y-%m-%d").date()
    except:
        c_start = date.today()
        c_end = date.today() + timedelta(days=365)

    raw_assets = assets_res.data if assets_res.data else []
    asset_list = [x["asset_name"] for x in raw_assets]
    df_tx_all = pd.DataFrame(tx_res.data) if tx_res.data else pd.DataFrame(columns=["date", "type", "asset_name", "category", "amount", "note"])
    df_pf = pd.DataFrame(pf_res.data) if pf_res.data else pd.DataFrame()
    
    # 計算記帳連擊 (Streak)
    has_logged_today = False
    streak_count = 0
    if not df_tx_all.empty:
        df_tx_all["date"] = pd.to_datetime(df_tx_all["date"]).dt.date
        unique_dates = sorted(df_tx_all["date"].unique(), reverse=True)
        today = date.today()
        
        if today in unique_dates:
            has_logged_today = True
            
        check_date = today if today in unique_dates else today - timedelta(days=1)
        for d in unique_dates:
            if d == check_date:
                streak_count += 1
                check_date -= timedelta(days=1)
            elif d > check_date:
                continue
            else:
                break

    # 計算當前總淨資產 (台幣計價大加總)
    cash_sum = sum(float(x["amount"]) for x in raw_assets)
    invest_sum_twd = 0.0
    if not df_pf.empty:
        df_unreal = df_pf[df_pf["status"] == "未實現"].copy()
        if not df_unreal.empty:
            for idx, row in df_unreal.iterrows():
                stock_id = row["asset_name"].strip()
                current_mkt_price = get_current_price(stock_id)
                buy_price = float(row["cost"])
                inserted_cash = float(row["actual_cash"])
                is_us_stock = not stock_id.isdigit()
                multiplier = usd_twd_rate if is_us_stock else 1.0
                
                if current_mkt_price is not None and buy_price > 0:
                    shares = inserted_cash / buy_price
                    invest_sum_twd += (shares * current_mkt_price * multiplier)
                else:
                    invest_sum_twd += (inserted_cash * multiplier)
    net_worth = cash_sum + invest_sum_twd

    # ---------------------------------------------------------
    # 🦉 側邊欄 DuDu 吉祥物狀態反饋
    # ---------------------------------------------------------
    st.sidebar.title(f"👤 冒險者：{current_user}")
    
    streak_fire = "🔥" if has_logged_today else "💤"
    st.sidebar.subheader(f"{streak_fire} 記帳連擊：{streak_count} 天")
    st.sidebar.divider()
    
    if not has_logged_today:
        st.sidebar.error(f"**DuDu 的嚴厲督促 (😡)：**\n今天你還沒記帳喔！想假裝沒花錢是不是？快點進「日常記帳」！")
    else:
        st.sidebar.success(f"**DuDu 的溫柔誇獎 (🥰)：**\n今天有乖乖記帳，表現得很好！繼續保持，早日達成你的自訂挑戰！")
        
    st.sidebar.divider()
    st.sidebar.metric("💵 即時美金匯率", f"{usd_twd_rate:.2f} TWD")
    
    module = st.sidebar.radio(
        "🗂️ 核心功能選單",
        ["🏠 總資產智慧管理大盤", "🏆 設定我的專屬存錢挑戰", "1. 📝 日常記帳 (觸發連擊)", "2. 🏦 資產帳戶維護", "3. 📈 投資組合 (台美股連動)"]
    )
    st.sidebar.divider()
    if st.sidebar.button("登出系統", type="secondary", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # 解析資產類別標籤
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
        parsed_assets.append({"id_key": name, "資產類別": a_type, "帳戶名稱": display_name, "餘額 (元)": float(a["amount"])})
    df_assets_parsed = pd.DataFrame(parsed_assets) if parsed_assets else pd.DataFrame(columns=["id_key", "資產類別", "帳戶名稱", "餘額 (元)"])

    if not df_tx_all.empty:
        df_tx = df_tx_all[~df_tx_all["category"].isin(["證券買入", "證券賣出", "餘額微調", "帳戶劃轉-轉出", "帳戶劃轉-轉入", "歷史庫存導入"])].copy()
    else:
        df_tx = df_tx_all.copy()

    # ---------------------------------------------------------
    # 模組 0：🏠 總資產智慧管理大盤
    # ---------------------------------------------------------
    if module == "🏠 總資產智慧管理大盤":
        st.title("💰 總資產智慧管理大盤")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("💵 帳戶總餘額", f"{cash_sum:,.0f} 元")
        m2.metric("📊 投資總市值 (台美股折算)", f"{invest_sum_twd:,.0f} 元")
        m3.metric("🔥 記帳連擊", f"{streak_count} 天")
        m4.metric("👑 個人淨資產", f"{net_worth:,.0f} 元")
        
        # 🎯 核心：展示目前進行中的自訂存錢挑戰
        st.divider()
        st.subheader(f"🏆 當前挑戰賽事：{c_title}")
        
        progress_pct = min(max(net_worth / c_target, 0.0), 1.0) if c_target > 0 else 0.0
        days_left = (c_end - date.today()).days
        
        col_p1, col_p2 = st.columns([3, 1])
        with col_p1:
            st.progress(progress_pct)
            st.write(f"📈 當前資產：**{net_worth:,.0f}** 元 / 目標 **{c_target:,.0f}** 元 (**{progress_pct*100:.2f}%**)")
            
            if days_left > 0:
                st.info(f"⏳ 距離挑戰截止日還有 **{days_left}** 天！")
                needed_amount = c_target - net_worth
                if needed_amount > 0:
                    daily_needed = needed_amount / days_left
                    st.caption(f"💡 溫馨精算：若要在期限內達標，平均每天資產需淨增長 **{daily_needed:,.1f}** 元。")
                else:
                    st.balloons()
                    st.success("🎉 太神啦！你的總資產已經提前超越挑戰目標囉！")
            elif days_left == 0:
                st.warning("🚨 今天就是挑戰的最後大限截止日！衝啊！")
            else:
                st.error(f"❌ 挑戰賽已於 {-days_left} 天前截止。快去建立下一場全新挑戰吧！")
                
        with col_p2:
            # 根據進度條顯示吉祥物不同狀態
            if progress_pct < 0.2:
                st.warning("🦉 DuDu：挑戰剛起跑！你現在的資產進度還很渺小，少喝一杯星巴克，多累積點連擊！")
            elif progress_pct < 0.6:
                st.info("🦉 DuDu：哎喲不錯嘛，進度正在穩健攀升！繼續保持記帳自律，我看好你。")
            elif progress_pct < 1.0:
                st.success("🦉 DuDu：哇！離你的夢想目標越來越近了！快點加速衝刺終點線！")
            else:
                st.balloons()
                st.success("👑 DuDu：頂禮膜拜！你完美征服了這場財務挑戰，真是不折不扣的理財大師！")
                
        st.divider()
        st.subheader("📊 多元資產類別分佈比例")
        if not df_assets_parsed.empty:
            df_summary = df_assets_parsed.groupby("資產類別")["餘額 (元)"].sum().reset_index()
            if invest_sum_twd > 0:
                df_summary = pd.concat([df_summary, pd.DataFrame([{"資產類別": "證券投資 (台美股加總)", "餘額 (元)": invest_sum_twd}])], ignore_index=True)
            df_summary["所佔比例"] = df_summary["餘額 (元)"].apply(lambda x: f"{(x / net_worth * 100):.1f} %" if net_worth > 0 else "0%")
            st.table(df_summary.rename(columns={"餘額 (元)": "總金額 (元)"}))
        else:
            st.info("歡迎加入！請先前往「2. 🏦 資產帳戶維護」建立你的第一個錢包。")

    # ---------------------------------------------------------
    # 模組：🏆 設定我的專屬存錢挑戰 (新功能！)
    # ---------------------------------------------------------
    elif module == "🏆 設定我的專屬存錢挑戰":
        st.title("🏆 自訂我的專屬存錢理財挑戰賽")
        st.write("不論是「大二前存到100萬」、「暑假出國基金3萬」，還是「買新機車存5萬」，你可以在此自由規劃專屬賽道與時間軸！")
        
        st.divider()
        with st.form("custom_challenge_form"):
            new_title = st.text_input("🎯 挑戰賽名稱（例如：大二前存到百萬、買MacBook計畫）", value=c_title)
            new_target = st.number_input("💰 挑戰目標金額（新台幣）", min_value=1000.0, value=c_target, step=10000.0)
            
            c1, c2 = st.columns(2)
            new_start = c1.date_input("📅 挑戰開始日期", value=c_start)
            new_end = c2.date_input("📅 預計達成日期", value=c_end)
            
            if st.form_submit_button("💾 儲存並開啟全新賽道", type="primary", use_container_width=True):
                if new_end <= new_start:
                    st.error("❌ 錯誤：達成日期必須大於開始日期！請重新選擇區間。")
                else:
                    try:
                        # 將自訂挑戰同步寫入雲端資料庫保存
                        supabase.table("users").update({
                            "challenge_title": new_title.strip(),
                            "challenge_target": new_target,
                            "challenge_start": str(new_start),
                            "challenge_end": str(new_end)
                        }).eq("username", current_user).execute()
                        
                        st.balloons()
                        st.success(f"🎉 成功開啟全新挑戰：【{new_title}】！目標金額：NT$ {new_target:,.0f} 元。DuDu 已經準備好嚴格監督你囉！")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"挑戰設定儲存失敗: {ex}")
                        
        st.write("### 💡 目前的挑戰快照：")
        st.json({
            "挑戰項目": c_title,
            "目標金額": f"{c_target:,.0f} 元",
            "起點日期": str(c_start),
            "終點日期": str(c_end),
            "當前淨資產水位": f"{net_worth:,.0f} 元"
        })

    # ---------------------------------------------------------
    # 模組 1：📝 日常記帳
    # ---------------------------------------------------------
    elif module == "1. 📝 日常記帳 (觸發連擊)":
        st.title("📝 隨手日常記帳中心")
        
        if not asset_list:
            st.warning("⚠️ 您目前沒有任何資產帳戶，請先去建立帳戶！")
        else:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("📥 新增日常收支")
                with st.form("tx_form", clear_on_submit=True):
                    tx_date = st.date_input("記帳日期", value=date.today())
                    tx_type = st.selectbox("交易類型", ["支出", "收入"])
                    
                    asset_labels = {x: x.replace("[", "").replace("]", " -> ") for x in asset_list}
                    tx_asset = st.selectbox("使用帳戶(資產)", options=list(asset_labels.keys()), format_func=lambda x: asset_labels[x])
                    
                    tx_cate = st.text_input("分類 (如: 晚餐、飲料、薪水)")
                    tx_amt = st.number_input("金額 (元)", min_value=1, value=100)
                    tx_note = st.text_input("備註")
                    
                    if st.form_submit_button("🔥 確認記帳並蓄力連擊"):
                        supabase.table("transactions").insert({
                            "username": current_user, "date": str(tx_date), "type": tx_type,
                            "asset_name": tx_asset, "category": tx_cate, "amount": tx_amt, "note": tx_note
                        }).execute()
                        
                        current_asset_amt = next(x["amount"] for x in raw_assets if x["asset_name"] == tx_asset)
                        new_amt = current_asset_amt + tx_amt if tx_type == "收入" else current_asset_amt - tx_amt
                        supabase.table("own_assets").update({"amount": new_amt}).eq("username", current_user).eq("asset_name", tx_asset).execute()
                        
                        st.balloons()
                        st.success(f"🎉 記帳成功！連擊加能量！DuDu 對你露出了讚許的微笑。")
                        st.rerun()
            with c2:
                st.subheader("📋 本日最新日常記帳明細")
                today_tx = df_tx[df_tx["date"] == date.today()] if not df_tx.empty else pd.DataFrame()
                if not today_tx.empty:
                    st.dataframe(today_tx[["date", "type", "asset_name", "category", "amount", "note"]], use_container_width=True)
                else:
                    st.info("💡 今天還空空如也喔！快記一筆別讓 DuDu 生氣！")

    # ---------------------------------------------------------
    # 模組 2：🏦 資產帳戶維護
    # ---------------------------------------------------------
    elif module == "2. 🏦 資產帳戶維護":
        st.title("🏦 資產帳戶維護與多維度報表")
        tab_asset1, tab_asset2 = st.tabs(["➕ 建立新帳戶", "🔄 帳戶資金劃轉"])
        
        with tab_asset1:
            st.subheader("建立新資產帳戶")
            with st.form("new_asset_categorical", clear_on_submit=True):
                col_a, col_b, col_c = st.columns(3)
                asset_class = col_a.selectbox("選擇資產類別", ["現金口袋", "活期存款", "數位帳戶", "定期存款", "外幣資產", "虛擬貨幣", "實體資產(機車/汽車)", "其他資產"])
                custom_name = col_b.text_input("輸入名稱 (如: 數位高利活存、Richart)")
                init_balance = col_c.number_input("初始餘額 / 價值 (元)", min_value=0, value=0)
                
                if st.form_submit_button("💾 立即新增此資產帳戶", use_container_width=True, type="primary"):
                    if custom_name.strip():
                        combined_name = f"[{asset_class}]{custom_name.strip()}"
                        if combined_name in asset_list: st.error("❌ 該資產名稱已存在！")
                        else:
                            try:
                                supabase.table("own_assets").insert({"username": current_user, "asset_name": combined_name, "amount": init_balance}).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "收入", "asset_name": combined_name, "category": "帳戶初始化", "amount": init_balance, "note": f"開戶全新資產：{asset_class}"}).execute()
                                st.success(f"🎉 成功解鎖新資產版圖： [{asset_class}] {custom_name} ！")
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
                    transfer_note = st.text_input("劃轉備註", value="內部帳戶劃轉")
                    
                    if st.form_submit_button("🚀 確認執行劃轉"):
                        if from_asset == to_asset: st.error("❌ 來源與目的地不能相同！")
                        else:
                            try:
                                amt_from = next(x["amount"] for x in raw_assets if x["asset_name"] == from_asset)
                                amt_to = next(x["amount"] for x in raw_assets if x["asset_name"] == to_asset)
                                supabase.table("own_assets").update({"amount": amt_from - transfer_amt}).eq("username", current_user).eq("asset_name", from_asset).execute()
                                supabase.table("own_assets").update({"amount": amt_to + transfer_amt}).eq("username", current_user).eq("asset_name", to_asset).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "支出", "asset_name": from_asset, "category": "帳戶劃轉-轉出", "amount": transfer_amt, "note": f"{transfer_note} (流向: {to_asset})"}).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "收入", "asset_name": to_asset, "category": "帳戶劃轉-轉入", "amount": transfer_amt, "note": f"{transfer_note} (來源: {from_asset})"}).execute()
                                st.success(f"🚀 安全劃轉 {transfer_amt:,.0f} 元！")
                                st.rerun()
                            except Exception as ex: st.error(f"劃轉失敗: {ex}")

        st.divider()
        st.subheader("💳 我的帳戶資產分佈明細")
        if not df_assets_parsed.empty:
            st.dataframe(df_assets_parsed[["資產類別", "帳戶名稱", "餘額 (元)"]], use_container_width=True)
            
            st.write("🔧 **帳戶進階管理 (修正與刪除)**")
            target_asset = st.selectbox("選擇要處理的帳戶", options=df_assets_parsed["id_key"].tolist(), format_func=lambda x: x.replace("[", "").replace("]", " -> "))
            current_row = df_assets_parsed[df_assets_parsed["id_key"] == target_asset].iloc[0]
            
            edit_col1, edit_col2 = st.columns(2)
            new_name = edit_col1.text_input("重命名名稱", value=current_row["帳戶名稱"])
            new_balance = edit_col2.number_input("微調新餘額 (元)", min_value=0.0, value=float(current_row["餘額 (元)"]))
            
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("💾 儲存變更設定", use_container_width=True, type="primary"):
                old_balance = float(current_row["餘額 (元)"])
                fixed_combined_name = f"[{current_row['資產類別']}]{new_name}"
                if new_balance != old_balance:
                    diff = new_balance - old_balance
                    supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "資產調整", "asset_name": fixed_combined_name, "category": "餘額微調", "amount": abs(diff), "note": f"校正數據，差額: {diff}"}).execute()
                supabase.table("own_assets").update({"asset_name": fixed_combined_name, "amount": new_balance}).eq("username", current_user).eq("asset_name", target_asset).execute()
                st.success("⚙️ 帳戶校正完畢！")
                st.rerun()
                
            if btn_col2.button("🗑️ 徹底刪除此資產帳戶", use_container_width=True, type="secondary"):
                supabase.table("own_assets").delete().eq("username", current_user).eq("asset_name", target_asset).execute()
                st.success(f"💥 帳戶已移除！")
                st.rerun()

    # ---------------------------------------------------------
    # 模組 3：📈 投資組合 (台美股連動換算)
    # ---------------------------------------------------------
    elif module == "3. 📈 投資組合 (台美股連動)":
        st.title("📈 交易所即時連動投資組合")
        st.info(f"💡 當前聯網即時美金匯率為： **{usd_twd_rate:.2f}** TWD。")
        
        tab_inv1, tab_inv2 = st.tabs(["🛒 常規日常交易下單", "📥 導入系統前舊投資持股"])
        
        with tab_inv1:
            st.subheader("金融資產交易下單（原幣計價）")
            with st.form("invest_form", clear_on_submit=True):
                col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns(5)
                inv_date = col_i1.date_input("交易日期", value=date.today())
                inv_type = col_i2.selectbox("交易方向", ["買入", "賣出"])
                inv_name = col_i3.text_input("股票代號 (如: 0050 / NVDA)", key="stock_code_regular")
                inv_price = col_i4.number_input("交易單價 (原幣價)", min_value=0.1, value=100.0)
                inv_qty = col_i5.number_input("交易股數", min_value=1, value=1000)
                inv_asset_link = st.selectbox("連動扣款/入款資產帳戶", asset_list, format_func=lambda x: x.replace("[", "").replace("]", " -> "))
                
                if st.form_submit_button("送出交易紀錄"):
                    if inv_name and inv_asset_link:
                        total_cash_flow = inv_price * inv_qty
                        curr_asset_amt = next(x["amount"] for x in raw_assets if x["asset_name"] == inv_asset_link)
                        
                        if inv_type == "買入":
                            supabase.table("own_assets").update({"amount": curr_asset_amt - total_cash_flow}).eq("username", current_user).eq("asset_name", inv_asset_link).execute()
                            supabase.table("portfolio").insert({"username": current_user, "date": str(inv_date), "asset_name": inv_name.strip().upper(), "type": "買入", "cost": inv_price, "actual_cash": total_cash_flow, "status": "未實現"}).execute()
                            supabase.table("transactions").insert({"username": current_user, "date": str(inv_date), "type": "投資轉換", "asset_name": inv_asset_link, "category": "證券買入", "amount": total_cash_flow, "note": f"購入 {inv_name.upper()}"}).execute()
                            st.success(f"🎉 交易下單成功！")
                        elif inv_type == "賣出":
                            unrealized_res = supabase.table("portfolio").select("*").eq("username", current_user).eq("asset_name", inv_name.strip().upper()).eq("status", "未實現").execute()
                            if unrealized_res.data:
                                target_stock = unrealized_res.data[0]
                                supabase.table("own_assets").update({"amount": curr_asset_amt + total_cash_flow}).eq("username", current_user).eq("asset_name", inv_asset_link).execute()
                                supabase.table("portfolio").update({"type": "賣出", "cost": inv_price, "actual_cash": total_cash_flow, "status": "已實現"}).eq("id", target_stock["id"]).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(inv_date), "type": "投資結算", "asset_name": inv_asset_link, "category": "證券賣出", "amount": total_cash_flow, "note": f"平倉 {inv_name.upper()}"}).execute()
                                st.success(f"🎉 平倉獲利入帳！")
                            else: st.error(f"❌ 錯誤：你根本沒有該持股！別想騙 DuDu！")
                        st.rerun()
                        
        with tab_inv2:
            st.subheader("📥 導入歷史舊庫存 (不扣現金)")
            with st.form("history_invest_form", clear_on_submit=True):
                col_h1, col_h2, col_h3, col_h4 = st.columns(4)
                hist_date = col_h1.date_input("購入日期", value=date.today())
                hist_name = col_h2.text_input("股票代號 (如: 2330 / AAPL)", key="stock_code_history")
                hist_price = col_h3.number_input("購入單價 (原幣)", min_value=0.1, value=100.0)
                hist_qty = col_h4.number_input("持有股數", min_value=1, value=1000)
                
                if st.form_submit_button("📥 立即補入庫存"):
                    if hist_name.strip():
                        total_hist_cost = hist_price * hist_qty
                        supabase.table("portfolio").insert({"username": current_user, "date": str(hist_date), "asset_name": hist_name.strip().upper(), "type": "買入", "cost": hist_price, "actual_cash": total_hist_cost, "status": "未實現"}).execute()
                        st.success(f"🎉 歷史資產導入成功！")
                        st.rerun()

        st.divider()
        st.subheader("💼 大盤即時未實現庫存明細 (每 30 秒自動聯網刷新)")
        
        df_unreal = df_pf[df_pf["status"] == "未實現"].copy() if not df_pf.empty else pd.DataFrame()
        if not df_unreal.empty:
            display_currency, live_prices_twd, live_market_values_twd, cost_sum_twd = [], [], [], []
            for index, row in df_unreal.iterrows():
                stock_id = row["asset_name"].strip()
                current_mkt_price = get_current_price(stock_id)
                buy_price = float(row["cost"])
                inserted_cash = float(row["actual_cash"])
                
                is_us_stock = not stock_id.isdigit()
                currency_tag = "USD" if is_us_stock else "TWD"
                multiplier = usd_twd_rate if is_us_stock else 1.0
                
                if current_mkt_price is not None and buy_price > 0:
                    shares = inserted_cash / buy_price
                    current_value = shares * current_mkt_price
                else:
                    current_mkt_price = buy_price
                    current_value = inserted_cash
                
                display_currency.append(currency_tag)
                live_prices_twd.append(f"{current_mkt_price * multiplier:,.2f} 元")
                live_market_values_twd.append(current_value * multiplier)
                cost_sum_twd.append(inserted_cash * multiplier)
                
            df_unreal["計價幣別"] = display_currency
            df_unreal["即時市價(台幣)"] = live_prices_twd
            df_unreal["最新市值(台幣)"] = live_market_values_twd
            df_unreal["投入本金(台幣)"] = cost_sum_twd
            df_unreal["即時損益(台幣)"] = df_unreal["最新市值(台幣)"] - df_unreal["投入本金(台幣)"]
            
            st.dataframe(
                df_unreal[["asset_name", "計價幣別", "date", "cost", "投入本金(台幣)", "即時市價(台幣)", "最新市值(台幣)", "即時損益(台幣)"]]
                .rename(columns={"asset_name": "股票代號", "date": "購入日期", "cost": "買入單價(原幣)"}),
                use_container_width=True
            )
            
            total_cost_all = sum(cost_sum_twd)
            total_market_all = sum(live_market_values_twd)
            total_profit_all = total_market_all - total_cost_all
            total_roi = (total_profit_all / total_cost_all * 100) if total_cost_all > 0 else 0
            
            st.metric("📊 台美全庫存即時總損益 (新台幣大加總)", f"{total_profit_all:,.0f} 元", f"綜合即時總報酬率：{total_roi:.2f} %")
        else:
            st.info("目前尚無未實現持股。")