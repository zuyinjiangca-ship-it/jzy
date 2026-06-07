# app.py
import streamlit as st
import pandas as pd
from analyzer import analyze_stock, get_secure_session
from tickers import TICKERS

st.set_page_config(layout="wide", page_title="AI Trading System Pro")

st.title("🚀 AI Trading System Pro")
st.caption("日线核心雷达：9 EMA + 24 SMA 趋势交叉 | 布林斐波那契精准定位 | 10分钟防锁安全盾")

# 核心安全缓存拦截，保持您朋友能跑通的稳定结构
@st.cache_data(ttl=600)
def run_scan():
    results = []
    # 在最外层创建单次连接，共享给所有资产，最大化防封锁
    session = get_secure_session()
    for t in TICKERS:
        try:
            res = analyze_stock(t, session)
            if res:
                results.append(res)
        except:
            continue
    return pd.DataFrame(results)

if st.button("开始扫描", type="primary"):
    with st.spinner("多维量化引擎已就位，正在本地内存解算盘面形态..."):
        df = run_scan()

        if df.empty:
            st.error("❌ 系统初始化异常，请检查基础配置文件。")
        else:
            # 严格按照您模板要求的 Score 评分进行降序排列
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            st.subheader("📊 实时多维量化扫描看板")
            
            # 视觉渲染增强：突破/金叉高亮绿，跌破/死叉高亮红
            def style_rows(val):
                if "金叉" in str(val) or "突破" in str(val):
                    return 'background-color: #e6f4ea; color: #137333; font-weight: bold;'
                if "死叉" in str(val) or "跌破" in str(val):
                    return 'background-color: #fce8e6; color: #c5221f; font-weight: bold;'
                return ''
                
            styled_df = df.style.map(style_rows, subset=['Signal & Breakout'])
            
            # 输出全宽完美看板（完全匹配您最开始提供的图片格式）
            st.dataframe(styled_df, use_container_width=True, height=650)

            # 独立提取前5名高分动能资产
            st.subheader("🔥 今日 TOP 5 强动能核心资产")
            st.dataframe(df.head(5), use_container_width=True)
