import streamlit as st

# 設定網頁標題與圖示
st.set_page_config(page_title="定期定額試算 App", page_icon="💰", layout="centered")

st.title("💰 定期定額本利和試算 App")
st.write("輸入你的投資參數，即時計算未來的複利成長！")

st.divider()  # 畫一條分隔線

# ====== 後台與前端輸入欄位 ======
# 使用 Streamlit 的側邊欄 (Sidebar) 或主畫面作為輸入
col1, col2 = st.columns(2)

with col1:
    monthly_deposit = st.number_input(
        "每月固定投入金額 (元)", min_value=100, value=5000, step=500
    )
    total_months = st.number_input(
        "預計投資月數 (月)", min_value=1, value=12, step=1
    )

with col2:
    annual_rate = (
        st.number_input(
            "固定年利率 (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.1
        )
        / 100
    )

# ====== 計算邏輯 (核心後台) ======
total_principal = 0
future_value = 0
monthly_rate = annual_rate / 12

for month in range(1, total_months + 1):
    total_principal += monthly_deposit
    future_value = (future_value + monthly_deposit) * (1 + monthly_rate)

total_interest = round(future_value) - total_principal
roi = ((future_value - total_principal) / total_principal) * 100 if total_principal > 0 else 0

st.divider()

# ====== 前端結果美化輸出 ======
st.subheader("📊 試算結果總覽")

# 使用美觀的數據卡片 (Metrics) 顯示
m1, m2, m3 = st.columns(3)
m1.metric("預計投資期間", f"{total_months} 個月", f"約 {total_months/12:.1f} 年", delta_color="off")
m2.metric("總共投入本金", f"{total_principal:,} 元")
m3.metric("最終本利和", f"{round(future_value):,} 元")

st.write("")  # 空一行

m4, m5 = st.columns(2)
m4.metric("賺取總利息", f"{total_interest:,} 元")
m5.metric("整體投報率", f"{roi:.2f} %")

# 頁尾提示
st.caption("※ 本程式計算採月複利滾存成長。")