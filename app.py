# app.py
import streamlit as st
import pandas as pd
from analyzer import analyze_stock
from tickers import TICKERS

# 强制开启投行看板全宽扁平化布局
st.set_page_config(layout="wide", page_title="AI Trading System Pro")

st.title("🚀 AI Trading System Pro")
st.caption("核心日线扫描器：9 EMA + 24 SMA 动能交叉 | 布林斐波那契精准定位 | 强弱多空量化评分")

# 核心安全防护盾：10分钟（600秒）内直接秒读内存，防止云端IP遭遇频控封锁
@st.cache_data(ttl=600)
def run_scan():
    results = []
    for t in TICKERS:
        try:
            res = analyze_stock(t)
            if res:
                results.append(res)
        except:
            continue
    return pd.DataFrame(results)

# 渲染触发按钮
if st.button("开始扫描", type="primary"):
    with st.spinner("量化引擎正在本地解算盘面指标，请稍候..."):
        df = run_scan()

        if df.empty:
            st.error("❌ 抱歉，当前时段云端公有网络拥堵，未拉取到有效数据，请稍后1-2分钟再次尝试。")
        else:
            # 严格按照模板要求：依评分从高到低进行降序排列
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            st.subheader("📊 实时多维量化扫描看板")
            
            # 高级表格样式渲染：多头与突破亮绿，空头与破位亮红
            def style_rows(val):
                if "金叉" in str(val) or "突破" in str(val):
                    return 'background-color: #e6f4ea; color: #137333; font-weight: bold;'
                if "死叉" in str(val) or "跌破" in str(val):
                    return 'background-color: #fce8e6; color: #c5221f; font-weight: bold;'
                return ''
                
            styled_df = df.style.map(style_rows, subset=['Signal & Breakout'])
            
            # 渲染出与您图片完全一致的扁平化无缝全宽表格
            st.dataframe(styled_df, use_container_width=True, height=650)

            # 单独切出 TOP 5 高权值强动能标的
            st.subheader("🔥 今日 TOP 5 强动能核心资产")
            st.dataframe(df.head(5), use_container_width=True)