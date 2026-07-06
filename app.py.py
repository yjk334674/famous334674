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

# ==========================================
# 🎨 現代可愛風 UI 與主題顏色管理 (極致黑白樣式)
# ==========================================
st.set_page_config(page_title="🦉 資本大管家 Asset-Duolingo", page_icon="🦉", layout="wide")

# 讓使用者在側邊欄最上方自由切換外觀樣式
theme_choice = st.sidebar.selectbox("🎨 切換大管家視覺風格", ["☀️ 軟萌亮白 (日暮白)", "🌙 極簡酷黑 (深夜黑)"])

if theme_choice == "☀️ 軟萌亮白 (日暮白)":
    # 注入现代粉嫩、亮色可愛風格
    st.markdown("""
        <style>
        .stApp {
            background-color: #FDFBF7;
            color: #4A4A4A;
        }
        h1, h2, h3, h4, h5, h6, p, label, span {
            color: #4A4A4A !important;
            font-family: "Microsoft JhengHei", sans-serif;
        }
        h1, h2, h3 {
            color: #FF7B94 !important;
        }
        .stButton>button {
            background-color: #FF9AA2 !important;
            color: white !important;
            border-radius: 20px !important;
            border: none !important;
        }
        .stProgress > div > div > div > div {
            background-color: #FFB7B2 !important;
        }
        div[data-testid="stMetricValue"] {
            color: #FF7B94 !important;
        }
        </style>
    """, unsafe_allow_html=True)
else:
    # 注入【全介面極致純黑、高對比爆亮白】視覺
    st.markdown("""
        <style>
        /* 1. 主畫面與側邊欄全黑化 */
        .stApp, [data-testid="stSidebar"], [data-testid="stHeader"] {
            background-color: #000000 !important;
            color: #FFFFFF !important;
        }
        
        /* 2. 強制所有層級的文字、標籤變純白 */
        h1, h2, h3, h4, h5, h6, p, label, span, li, small {
            color: #FFFFFF !important;
            font-family: "Microsoft JhengHei", sans-serif;
        }
        
        /* 3. 特殊標題加上可愛粉霓虹，保持設計感 */
        h1, h2, h3 {
            color: #FF83A8 !important;
        }
        
        /* 4. 徹底解決表格黑色字體看不見的問題 (st.table & st.dataframe 強化) */
        table, th, td, tr, .stTable {
            color: #FFFFFF !important;
            background-color: #111111 !important;
            border-color: #333333 !important;
        }
        th {
            background-color: #222222 !important;
            font-weight: bold !important;
        }
        div[data-testid="stTable"] td {
            color: #FFFFFF !important;
        }
        div[data-testid="stDataFrame"] {
            background-color: #111111 !important;
        }
        
        /* 5. 按鈕與進度條調整 */
        .stButton>button {
            background-color: #A8E6CF !important;
            color: #000000 !important;
            border-radius: 20px !important;
            font-weight: bold !important;
            border: none !important;
        }
        .stProgress > div > div > div > div {
            background-color: #FF83A8 !important;
        }
        
        /* 6. 指標卡片數值高亮 */
        div[data-testid="stMetricValue"] {
            color: #A8E6CF !important;
            font-weight: bold !important;
        }
        div[data-testid="stMetricLabel"] {
            color: #CCCCCC !important;
        }
        
        /* 7. 輸入框與下拉選單微調，避免全黑找不到邊框 */
        div[data-baseweb="select"], input, textarea {
            background-color: #1A1A1A !important;
            color: #FFFFFF !important;
            border: 1px solid #444444 !important;
        }
        div[role="listbox"] {
            background-color: #1A1A1A !important;
            color: #FFFFFF !important;
        }
        </style>
    """, unsafe_allow_html=True)


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
    st.title("🦉 資本大管家 Asset-Duolingo")
    st.subheader("🧸 打造專屬你的存錢萌賽道，理財就像收集神奇糖果一樣簡單！")
    tab1, tab2 = st.tabs(["🔑 夥伴登入", "📝 快速加入大管家"])
    
    with tab1:
        login_user = st.text_input("帳號 (大管家稱呼)", key="login_user")
        login_pwd = st.text_input("密碼", type="password", key="login_pwd")
        
        if st.button("立即進入金幣城堡 🏰", type="primary", use_container_width=True):
            if login_user and login_pwd:
                try:
                    response = supabase.table("users").select("*").eq("username", login_user).execute()
                    if response.data:
                        user_record = response.data[0]
                        if user_record["password"] == hash_password(login_pwd):
                            st.session_state.logged_in = True
                            st.session_state.username = login_user
                            st.success(f"🎉 歡迎回來！DuDu 已經在金庫門口等捏！")
                            st.rerun()
                        else: st.error("❌ 密碼不對喔，DuDu 在偷偷歪頭瞪你！(｡•́︿•̀｡)")
                    else: st.error("❌ 找不到這個大管家，快去隔壁註冊一個！")
                except Exception as ex: st.error(f"資料庫錯誤: {ex}")
            else: st.warning("⚠️ 記得填寫完整的名字與密碼喔！")
                
    with tab2:
        reg_user = st.text_input("設定新名字", key="reg_user")
        reg_pwd = st.text_input("設定新密碼", type="password", key="reg_pwd")
        reg_pwd_confirm = st.text_input("再次確認新密碼", type="password", key="reg_pwd_confirm")
        
        if st.button("開啟我的軟萌理財之旅 ✨", use_container_width=True):
            if reg_user and reg_pwd and reg_pwd_confirm:
                if reg_pwd != reg_pwd_confirm: st.error("❌ 兩次密碼長得不一樣捏？")
                else:
                    try:
                        check_exist = supabase.table("users").select("username").execute()
                        if any(x["username"] == reg_user for x in check_exist.data): 
                            st.error("❌ 這個名字已經有人用了，換個更可愛的吧！")
                        else:
                            supabase.table("users").insert({
                                "username": reg_user, 
                                "password": hash_password(reg_pwd),
                                "challenge_title": "我的第一筆金幣大作戰 🍭",
                                "challenge_target": 100000.0,
                                "challenge_start": str(date.today()),
                                "challenge_end": str(date.today() + timedelta(days=365))
                            }).execute()
                            st.success("🎉 註冊好啦！快切換回「夥伴登入」登入吧！")
                    except Exception as ex: st.error(f"加入失敗: {ex}")
            else: st.warning("⚠️ 欄位不要漏掉喔，加油！")

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
        st.error(f"📡 連線小精靈迷路了: {api_err}")
        st.stop()

    user_info = user_res.data[0] if user_res.data else {}
    
    c_title = user_info.get("challenge_title", "我的自訂理財大挑戰 🍦")
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

    # 計算當前總淨資產
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
    # 🦉 側邊欄 DuDu 吉祥物狀態反饋 (可愛萌化)
    # ---------------------------------------------------------
    st.sidebar.divider()
    user_badge = "👑 明星大管家" if net_worth >= 1000000 else "✨ 實習大管家"
    st.sidebar.markdown(f"### 🧁 夥伴：{current_user}\n`{user_badge}`")
    
    streak_fire = "💖" if has_logged_today else "💤"
    st.sidebar.subheader(f"{streak_fire} 記帳連擊：{streak_count} 天")
    st.sidebar.divider()
    
    if not has_logged_today:
        st.sidebar.error(f"**🦉 DuDu 的小提醒 ( •̀ ω •́ )✧：**\n今天你還沒記帳唷！不可以裝作忘記花錢，快去「日常記帳」蓋個章！")
    else:
        st.sidebar.success(f"**🦉 DuDu 瘋狂揉臉 (〃'▽'〃)：**\n今天有乖乖記帳，太棒了吧！給你貼一朵小紅花，繼續保持喔！")
        
    st.sidebar.divider()
    st.sidebar.metric("🧋 即時美金匯率", f"{usd_twd_rate:.2f} TWD")
    
    module = st.sidebar.radio(
        "📂 大管家魔法選單",
        ["🏠 城堡總資產大盤", "🏆 魔法自訂存錢挑戰賽", "🍬 1. 隨手記帳 (累積連擊)", "🏦 2. 寶箱帳戶維護", "📈 3. 星際投資組合"]
    )
    st.sidebar.divider()
    if st.sidebar.button("離開大管家 🚪", type="secondary", use_container_width=True):
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
            a_type = "未分類口袋"
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
    if module == "🏠 城堡總資產大盤":
        st.title("🌟 資本大管家・資產魔法城堡")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🍧 錢包總餘額", f"{cash_sum:,.0f} 元")
        m2.metric("📊 證券星星市值", f"{invest_sum_twd:,.0f} 元")
        m3.metric("🔥 記帳連動天數", f"{streak_count} 天")
        m4.metric("👑 魔法總淨資產", f"{net_worth:,.0f} 元")
        
        st.divider()
        st.subheader(f"🏆 當前挑戰賽事：{c_title}")
        
        progress_pct = min(max(net_worth / c_target, 0.0), 1.0) if c_target > 0 else 0.0
        days_left = (c_end - date.today()).days
        
        col_p1, col_p2 = st.columns([3, 1])
        with col_p1:
            st.progress(progress_pct)
            st.write(f"📈 能量收集進度：**{net_worth:,.0f}** 元 / 目標 **{c_target:,.0f}** 元 (**{progress_pct*100:.2f}%**)")
            
            if days_left > 0:
                st.info(f"⏳ 距離約定截止日還有 **{days_left}** 天！加油鴨！")
                needed_amount = c_target - net_worth
                if needed_amount > 0:
                    daily_needed = needed_amount / days_left
                    st.caption(f"💡 大管家精算：每天只要再多存 **{daily_needed:,.1f}** 元就能把獎勵抱回家囉！")
                else:
                    st.balloons()
                    st.success("🎉 太厲害了！你的資產已經提前滿出來，挑戰成功！")
            elif days_left == 0:
                st.warning("🚨 終點線就在今天！把最後的能量存進去吧！")
            else:
                st.error(f"❌ 這場挑戰在 {-days_left} 天前落幕了。快去開啟下一場全新的魔法冒險！")
                
        with col_p2:
            if progress_pct < 0.2:
                st.warning("🦉 DuDu：挑戰剛起飛！現在的進度還像小豆苗一樣，每天少喝一杯手搖飲，多澆點水吧！( •̀ ω •́ )✧")
            elif progress_pct < 0.6:
                st.info("🦉 DuDu：哎呀不錯喔！小豆苗開始長大了！保持每天記帳，很快就能看到果實了！")
            elif progress_pct < 1.0:
                st.success("🦉 DuDu：哇哇哇！離目標只剩一點點了！快點加速衝刺，終點有大蛋糕等著你！🎂")
            else:
                st.balloons()
                st.success("👑 DuDu：請收下我的膝蓋！你已經是全宇宙最強的理財大管家了！(≧▽≦)")
                
        st.divider()
        st.subheader("🧁 寶箱類別資產比例")
        if not df_assets_parsed.empty:
            df_summary = df_assets_parsed.groupby("資產類別")["餘額 (元)"].sum().reset_index()
            if invest_sum_twd > 0:
                df_summary = pd.concat([df_summary, pd.DataFrame([{"資產類別": "證券投資 (台美股加總)", "餘額 (元)": invest_sum_twd}])], ignore_index=True)
            df_summary["所佔比例"] = df_summary["餘額 (元)"].apply(lambda x: f"{(x / net_worth * 100):.1f} %" if net_worth > 0 else "0%")
            
            # 使用更直覺的表格渲染，搭配我們注入的極致高對比 CSS
            st.table(df_summary.rename(columns={"餘額 (元)": "總金額 (元)"}))
        else:
            st.info("新城堡空空如也？先前往「🏦 2. 寶箱帳戶維護」建立你的第一個魔法錢包吧！")

    # ---------------------------------------------------------
    # 模組：🏆 魔法自訂存錢挑戰賽
    # ---------------------------------------------------------
    elif module == "🏆 魔法自訂存錢挑戰賽":
        st.title("🏆 自訂專屬理財賽道")
        st.write("想要買夢幻公仔、換新手機，還是準備旅行基金？在這裡自由定義你的挑戰目標與時間軸！")
        
        st.divider()
        with st.form("custom_challenge_form"):
            new_title = st.text_input("🎯 挑戰賽取個可愛名字（例如：精緻女孩儲蓄計畫 💄、買新車車大作戰 🏎️）", value=c_title)
            new_target = st.number_input("💰 挑戰目標金額 (NT$)", min_value=1000.0, value=c_target, step=10000.0)
            
            c1, c2 = st.columns(2)
            new_start = c1.date_input("📅 冒險開始日期", value=c_start)
            new_end = c2.date_input("📅 夢想達成日期", value=c_end)
            
            if st.form_submit_button("💾 儲存並召喚全新挑戰賽", type="primary", use_container_width=True):
                if new_end <= new_start:
                    st.error("❌ 哎呀！結束日期必須比開始日期還要晚喔！")
                else:
                    try:
                        supabase.table("users").update({
                            "challenge_title": new_title.strip(),
                            "challenge_target": new_target,
                            "challenge_start": str(new_start),
                            "challenge_end": str(new_end)
                        }).eq("username", current_user).execute()
                        
                        st.balloons()
                        st.success(f"🎉 新挑戰召喚成功：【{new_title}】！目標金額：NT$ {new_target:,.0f} 元。DuDu 已經把計時器按下去囉！")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"挑戰儲存失敗了: {ex}")
                        
        st.write("### 💡 目前正在運作的挑戰卷軸：")
        st.json({
            "項目名稱": c_title,
            "目標金額": f"{c_target:,.0f} 元",
            "啟程日期": str(c_start),
            "抵達日期": str(c_end),
            "當前淨資產水位": f"{net_worth:,.0f} 元"
        })

    # ---------------------------------------------------------
    # 模組 1：🍬 隨手記帳
    # ---------------------------------------------------------
    elif module == "🍬 1. 隨手記帳 (累積連擊)":
        st.title("🍬 快樂日常隨手記帳")
        
        if not asset_list:
            st.warning("⚠️ 你還沒有任何魔法寶箱（帳戶）可以裝錢，快去隔壁建立一個！")
        else:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.subheader("📥 填寫今日收支")
                with st.form("tx_form", clear_on_submit=True):
                    tx_date = st.date_input("記帳日期", value=date.today())
                    tx_type = st.selectbox("收支方向", ["支出", "收入"])
                    
                    asset_labels = {x: x.replace("[", "").replace("]", " ➔ ") for x in asset_list}
                    tx_asset = st.selectbox("使用哪個錢包", options=list(asset_labels.keys()), format_func=lambda x: asset_labels[x])
                    
                    tx_cate = st.text_input("小分類 (如: 美味晚餐 ☕、買衣服 👗、發薪水了 💵)")
                    tx_amt = st.number_input("變動金額 (元)", min_value=1, value=100)
                    tx_note = st.text_input("心情備註")
                    
                    if st.form_submit_button("🔥 蓋章記帳！"):
                        supabase.table("transactions").insert({
                            "username": current_user, "date": str(tx_date), "type": tx_type,
                            "asset_name": tx_asset, "category": tx_cate, "amount": tx_amt, "note": tx_note
                        }).execute()
                        
                        current_asset_amt = next(x["amount"] for x in raw_assets if x["asset_name"] == tx_asset)
                        new_amt = current_asset_amt + tx_amt if tx_type == "收入" else current_asset_amt - tx_amt
                        supabase.table("own_assets").update({"amount": new_amt}).eq("username", current_user).eq("asset_name", tx_asset).execute()
                        
                        st.balloons()
                        st.success(f"🎉 記帳完成！連擊能量注入成功！DuDu 給了你一個讚許的眼神。")
                        st.rerun()
            with c2:
                st.subheader("📋 今天記錄的彩色明細")
                today_tx = df_tx[df_tx["date"] == date.today()] if not df_tx.empty else pd.DataFrame()
                if not today_tx.empty:
                    st.dataframe(today_tx[["date", "type", "asset_name", "category", "amount", "note"]], use_container_width=True)
                else:
                    st.info("💡 今天還是一片空白呢！快記一筆，不要讓連擊斷掉唷！")

    # ---------------------------------------------------------
    # 模組 2：🏦 寶箱帳戶維護
    # ---------------------------------------------------------
    elif module == "🏦 2. 寶箱帳戶維護":
        st.title("🏦 寶箱帳戶管理維護")
        tab_asset1, tab_asset2 = st.tabs(["➕ 鑄造新錢包", "🔄 內部資金搬家"])
        
        with tab_asset1:
            st.subheader("開啟全新資產儲蓄類別")
            with st.form("new_asset_categorical", clear_on_submit=True):
                col_a, col_b, col_c = st.columns(3)
                asset_class = col_a.selectbox("寶箱種類", ["🧸 現金口袋", "🏦 活期存款", "📱 數位帳戶", "🔒 定期存款", "✈️ 外幣資產", "🪙 虛擬貨幣", "🛵 實體資產", "📦 其他寶物"])
                custom_name = col_b.text_input("取個小名 (如: 旅遊豬豬、Richart)")
                init_balance = col_c.number_input("裡面先塞多少錢 (元)", min_value=0, value=0)
                
                if st.form_submit_button("🎨 封印並啟用帳戶", use_container_width=True, type="primary"):
                    if custom_name.strip():
                        combined_name = f"[{asset_class}]{custom_name.strip()}"
                        if combined_name in asset_list: st.error("❌ 這個寶箱名稱重複了捏！")
                        else:
                            try:
                                supabase.table("own_assets").insert({"username": current_user, "asset_name": combined_name, "amount": init_balance}).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "收入", "asset_name": combined_name, "category": "帳戶初始化", "amount": init_balance, "note": f"開戶全新資產：{asset_class}"}).execute()
                                st.success(f"🎉 成功解鎖新寶箱： [{asset_class}] {custom_name} ！")
                                st.rerun()
                            except Exception as ex: st.error(f"連線失敗了: {ex}")
                    else: st.warning("⚠️ 給寶箱取個名字嘛～")
                    
        with tab_asset2:
            st.subheader("🔄 內部寶箱資金互轉")
            if len(asset_list) < 2:
                st.info("💡 你需要至少兩個寶箱才能玩搬家遊戲喔。")
            else:
                with st.form("transfer_form", clear_on_submit=True):
                    col_t1, col_t2, col_t3 = st.columns(3)
                    from_asset = col_t1.selectbox("把錢從這裡拿出來", asset_list, format_func=lambda x: x.replace("[", "").replace("]", " ➔ "))
                    to_asset = col_t2.selectbox("放到這個寶箱裡", asset_list, format_func=lambda x: x.replace("[", "").replace("]", " ➔ "))
                    transfer_amt = col_t3.number_input("搬運金額 (元)", min_value=1, value=1000)
                    transfer_note = st.text_input("搬家備註", value="魔法資金劃轉")
                    
                    if st.form_submit_button("🚀 開始搬運！"):
                        if from_asset == to_asset: st.error("❌ 左口袋放右口袋，不能選擇同一個喔！")
                        else:
                            try:
                                amt_from = next(x["amount"] for x in raw_assets if x["asset_name"] == from_asset)
                                amt_to = next(x["amount"] for x in raw_assets if x["asset_name"] == to_asset)
                                supabase.table("own_assets").update({"amount": amt_from - transfer_amt}).eq("username", current_user).eq("asset_name", from_asset).execute()
                                supabase.table("own_assets").update({"amount": amt_to + transfer_amt}).eq("username", current_user).eq("asset_name", to_asset).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "支出", "asset_name": from_asset, "category": "帳戶劃轉-轉出", "amount": transfer_amt, "note": f"{transfer_note} (流向: {to_asset})"}).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "收入", "asset_name": to_asset, "category": "帳戶劃轉-轉入", "amount": transfer_amt, "note": f"{transfer_note} (來源: {from_asset})"}).execute()
                                st.success(f"🚀 成功搬運 {transfer_amt:,.0f} 元！")
                                st.rerun()
                            except Exception as ex: st.error(f"搬運失敗: {ex}")

        st.divider()
        st.subheader("💳 當前所有寶箱餘額清單")
        if not df_assets_parsed.empty:
            st.dataframe(df_assets_parsed[["資產類別", "帳戶名稱", "餘額 (元)"]], use_container_width=True)
            
            st.write("🔧 **高級寶箱整理工具 (數值修正/打破寶箱)**")
            target_asset = st.selectbox("要調整哪個寶箱", options=df_assets_parsed["id_key"].tolist(), format_func=lambda x: x.replace("[", "").replace("]", " ➔ "))
            current_row = df_assets_parsed[df_assets_parsed["id_key"] == target_asset].iloc[0]
            
            edit_col1, edit_col2 = st.columns(2)
            new_name = edit_col1.text_input("修改名稱", value=current_row["帳戶名稱"])
            new_balance = edit_col2.number_input("直接重設新餘額 (元)", min_value=0.0, value=float(current_row["餘額 (元)"]))
            
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("💾 魔法校正變更", use_container_width=True, type="primary"):
                old_balance = float(current_row["餘額 (元)"])
                fixed_combined_name = f"[{current_row['資產類別']}]{new_name}"
                if new_balance != old_balance:
                    diff = new_balance - old_balance
                    supabase.table("transactions").insert({"username": current_user, "date": str(date.today()), "type": "資產調整", "asset_name": fixed_combined_name, "category": "餘額微調", "amount": abs(diff), "note": f"校正數據，差額: {diff}"}).execute()
                supabase.table("own_assets").update({"asset_name": fixed_combined_name, "amount": new_balance}).eq("username", current_user).eq("asset_name", target_asset).execute()
                st.success("⚙️ 數據對齊好囉！")
                st.rerun()
                
            if btn_col2.button("🗑️ 徹底打破此寶箱 (刪除)", use_container_width=True, type="secondary"):
                supabase.table("own_assets").delete().eq("username", current_user).eq("asset_name", target_asset).execute()
                st.success(f"💥 寶箱碎掉了！")
                st.rerun()

    # ---------------------------------------------------------
    # 模組 3：📈 星際投資組合
    # ---------------------------------------------------------
    elif module == "📈 3. 星際投資組合":
        st.title("📈 星際交易所・即時連動持股")
        st.info(f"🧁 當前宇宙聯網美金匯率為： **{usd_twd_rate:.2f}** TWD (30秒自動重算損益喔)。")
        
        tab_inv1, tab_inv2 = st.tabs(["🛒 常規日常買賣星星", "📥 搬運之前的舊庫存星星"])
        
        with tab_inv1:
            st.subheader("下單購買/賣出星星（以該市場原幣計算）")
            with st.form("invest_form", clear_on_submit=True):
                col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns(5)
                inv_date = col_i1.date_input("交易日期", value=date.today())
                inv_type = col_i2.selectbox("買賣方向", ["買入", "賣出"])
                inv_name = col_i3.text_input("星星代號 (如: 0050 / TSLA)", key="stock_code_regular")
                inv_price = col_i4.number_input("每一顆星星單價", min_value=0.1, value=100.0)
                inv_qty = col_i5.number_input("交易顆數(股數)", min_value=1, value=1000)
                inv_asset_link = st.selectbox("要從哪顆寶箱連動扣/入款", asset_list, format_func=lambda x: x.replace("[", "").replace("]", " ➔ "))
                
                if st.form_submit_button("發射交易信號 🚀"):
                    if inv_name and inv_asset_link:
                        total_cash_flow = inv_price * inv_qty
                        curr_asset_amt = next(x["amount"] for x in raw_assets if x["asset_name"] == inv_asset_link)
                        
                        if inv_type == "買入":
                            supabase.table("own_assets").update({"amount": curr_asset_amt - total_cash_flow}).eq("username", current_user).eq("asset_name", inv_asset_link).execute()
                            supabase.table("portfolio").insert({"username": current_user, "date": str(inv_date), "asset_name": inv_name.strip().upper(), "type": "買入", "cost": inv_price, "actual_cash": total_cash_flow, "status": "未實現"}).execute()
                            supabase.table("transactions").insert({"username": current_user, "date": str(inv_date), "type": "投資轉換", "asset_name": inv_asset_link, "category": "證券買入", "amount": total_cash_flow, "note": f"購入星星 {inv_name.upper()}"}).execute()
                            st.success(f"🎉 捕捉到新星星庫存！")
                        elif inv_type == "賣出":
                            unrealized_res = supabase.table("portfolio").select("*").eq("username", current_user).eq("asset_name", inv_name.strip().upper()).eq("status", "未實現").execute()
                            if unrealized_res.data:
                                target_stock = unrealized_res.data[0]
                                supabase.table("own_assets").update({"amount": curr_asset_amt + total_cash_flow}).eq("username", current_user).eq("asset_name", inv_asset_link).execute()
                                supabase.table("portfolio").update({"type": "賣出", "cost": inv_price, "actual_cash": total_cash_flow, "status": "已實現"}).eq("id", target_stock["id"]).execute()
                                supabase.table("transactions").insert({"username": current_user, "date": str(inv_date), "type": "投資結算", "asset_name": inv_asset_link, "category": "證券賣出", "amount": total_cash_flow, "note": f"平倉星星 {inv_name.upper()}"}).execute()
                                st.success(f"🎉 星星平倉，金幣收回！")
                            else: st.error(f"❌ 哼！你明明就沒有這顆星星，別想騙過 DuDu！")
                        st.rerun()
                        
        with tab_inv2:
            st.subheader("📥 填補之前已經持有的歷史庫存 (不影響任何錢包餘額)")
            with st.form("history_invest_form", clear_on_submit=True):
                col_h1, col_h2, col_h3, col_h4 = st.columns(4)
                hist_date = col_h1.date_input("當初捕捉日期", value=date.today())
                hist_name = col_h2.text_input("星星代號 (如: 2330 / AAPL)", key="stock_code_history")
                hist_price = col_h3.number_input("買入單價 (原幣)", min_value=0.1, value=100.0)
                hist_qty = col_h4.number_input("持有顆數", min_value=1, value=1000)
                
                if st.form_submit_button("📥 快速收納至持股星盤"):
                    if hist_name.strip():
                        total_hist_cost = hist_price * hist_qty
                        supabase.table("portfolio").insert({"username": current_user, "date": str(hist_date), "asset_name": hist_name.strip().upper(), "type": "買入", "cost": hist_price, "actual_cash": total_hist_cost, "status": "未實現"}).execute()
                        st.success(f"🎉 歷史星星庫存導入成功！")
                        st.rerun()

        st.divider()
        st.subheader("💼 星盤即時損益估值 (每 30 秒自動聯網連線刷新)")
        
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
                .rename(columns={"asset_name": "星星代號", "date": "捕捉日期", "cost": "買入單價(原幣)"}),
                use_container_width=True
            )
            
            total_cost_all = sum(cost_sum_twd)
            total_market_all = sum(live_market_values_twd)
            total_profit_all = total_market_all - total_cost_all
            total_roi = (total_profit_all / total_cost_all * 100) if total_cost_all > 0 else 0
            
            st.metric("🧁 全星盤即時總損益 (折合新台幣)", f"{total_profit_all:,.0f} 元", f"綜合投資超能力報酬率：{total_roi:.2f} %")
        else:
            st.info("目前尚無未實現的星星持股唷。")