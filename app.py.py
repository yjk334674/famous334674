import pandas as pd
import streamlit as st

# 設定網頁標題與圖示
st.set_page_config(page_title="定期定額資產組合試算 App", page_icon="💰", layout="centered")

st.title("💰 定期定額資產組合試算 App")
st.write("自訂你的資產配置比例與報酬率，即時計算綜合複利成長！")

st.divider()

# ====== 1. 左側欄/上方：基礎投資參數 ======
col1, col2 = st.columns(2)
with col1:
    monthly_deposit = st.number_input(
        "每月總投入金額 (元)", min_value=100, value=10000, step=1000
    )
with col2:
    total_months = st.number_input(
        "預計投資月數 (月)", min_value=1, value=36, step=1
    )

st.write("")
st.subheader("🛠️ 自訂資產組合配置")
st.write("你可以直接在下方表格內**修改名稱、調整比例與報酬率**，或是點擊表格下方新增項目：")

# ====== 2. 動態資產組合表格 (後台預設初始組合) ======
default_portfolio = pd.DataFrame(
    [
        {"資產名稱": "美股 ETF (如 VTI)", "配置比例 (%)": 60.0, "預期年化報酬率 (%)": 9.0},
        {"資產名稱": "高股息 ETF (如 0056)", "配置比例 (%)": 30.0, "預期年化報酬率 (%)": 6.0},
        {"資產名稱": "加密貨幣 / 現金", "配置比例 (%)": 10.0, "預期年化報酬率 (%)": 2.0},
    ]
)

# 讓使用者可以在前端像 Excel 一樣編輯表格
edited_df = st.data_editor(
    default_portfolio,
    num_rows="dynamic",  # 允許使用者動態新增或刪除一整列
    use_container_width=True,
)

# ====== 3. 後台核心計算邏輯 ======
# 計算目前配置總比例
total_allocation = edited_df["配置比例 (%)"].sum()

# 檢查防呆：如果比例不等於 100%，給予警告提示
if total_allocation != 100.0:
    st.warning(
        f"⚠️ 目前配置總比例為 **{total_allocation:.1f}%**。建議將調整至 **100%** 以符合真實分配（目前將依實際權重自動重算）。"
    )

# 計算加權綜合年化報酬率
# 公式: 總和(各資產比例 * 各資產報酬率) / 總比例
weighted_annual_rate = (
    (edited_df["配置比例 (%)"] * edited_df["預期年化報酬率 (%)"]).sum()
    / total_allocation
    / 100
    if total_allocation > 0
    else 0
)

# 逐月複利滾存計算
total_principal = 0
future_value = 0
monthly_rate = weighted_annual_rate / 12

for month in range(1, total_months + 1):
    total_principal += monthly_deposit
    future_value = (future_value + monthly_deposit) * (1 + monthly_rate)

total_interest = round(future_value) - total_principal
roi = (
    ((future_value - total_principal) / total_principal) * 100
    if total_principal > 0
    else 0
)

st.divider()

# ====== 4. 前端試算結果美化輸出 ======
st.subheader("📊 組合試算結果總覽")

# 顯示加權後的綜合報酬率
st.info(f"💡 依據你的資產配置，這套組合的**綜合加權年化報酬率**約為：**{weighted_annual_rate * 100:.2f} %**")

m1, m2, m3 = st.columns(3)
m1.metric(
    "預計投資期間",
    f"{total_months} 個月",
    f"約 {total_months/12:.1f} 年",
    delta_color="off",
)
m2.metric("總共投入本金", f"{total_principal:,} 元")
m3.metric("最終本利和", f"{round(future_value):,} 元")

st.write("")

m4, m5 = st.columns(2)
m4.metric("賺取總利息", f"{total_interest:,} 元")
m5.metric("整體投報率", f"{roi:.2f} %")

st.caption("※ 本程式依據資產組合之加權年化報酬率，採月複利滾存成長進行試算。")
