# analyzer.py
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

def get_secure_session():
    """建立虚拟安全通道，进一步降低公有云被频控的风险"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

def get_data(ticker, session, retries=3):
    for _ in range(retries):
        try:
            # 继承朋友的 valid 1y 周期参数，彻底规避 6m 导致的线上空数据死锁
            df = yf.download(ticker, period="1y", progress=False, session=session)
            if not df.empty:
                # 核心防错：拍扁 yfinance 最新的双层 MultiIndex 表头
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
        except:
            time.sleep(0.5)
    return None

def analyze_stock(ticker):
    session = get_secure_session()
    df = get_data(ticker, session)

    if df is None or df.empty:
        return None

    # 清洗无效交易日数据
    df = df.dropna(subset=['Close'])

    if len(df) < 60:
        return None

    # 强转数据类型，防止类型冲突
    close = df['Close'].astype(float)
    volume = df['Volume'].astype(float)
    high_series = df['High'].astype(float)
    low_series = df['Low'].astype(float)

    latest_close = float(close.iloc[-1])
    latest_vol = float(volume.iloc[-1])

    # 1. 9 EMA 与 24 SMA 动态动能交叉
    df['EMA_9'] = close.ewm(span=9, adjust=False).mean()
    df['SMA_24'] = close.rolling(window=24).mean()
    
    ema_9_now = float(df['EMA_9'].iloc[-1])
    sma_24_now = float(df['SMA_24'].iloc[-1])
    ema_9_prev = float(df['EMA_9'].iloc[-2])
    sma_24_prev = float(df['SMA_24'].iloc[-2])

    if ema_9_prev < sma_24_prev and ema_9_now >= sma_24_now:
        trend_signal = "🎯 金叉启动"
    elif ema_9_prev > sma_24_prev and ema_9_now <= sma_24_now:
        trend_signal = "🚨 死叉确立"
    elif ema_9_now > sma_24_now:
        trend_signal = "📈 多头趋势"
    else:
        trend_signal = "📉 空头动能"

    # 2. RSI (14) 强弱动能指标
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    latest_rsi = float(rsi.iloc[-1])

    # 3. 布林带 (20, 2) 波动率边界
    df['BB_mid'] = close.rolling(window=20).mean()
    df['BB_std'] = close.rolling(window=20).std()
    df['BB_lower'] = df['BB_mid'] - (2 * df['BB_std'])
    bb_lower_now = float(df['BB_lower'].iloc[-1])

    # 4. 斐波那契回撤（近60个交易日黄金分割防御线）
    recent_df = df.tail(60)
    high_p = float(recent_df['High'].max())
    low_p = float(recent_df['Low'].min())
    diff = high_p - low_p
    fib_382 = high_p - 0.382 * diff
    fib_618 = high_p - 0.618 * diff

    # 5. 综合计算精确定位：Support（地板）与 Resistance（天花板）
    support = max(bb_lower_now, fib_618)
    resistance = fib_382

    if latest_close > resistance:
        breakout_status = " 🚀 突破阻力"
    elif latest_close < support:
        breakout_status = " ⚠️ 跌破支撑"
    else:
        breakout_status = ""
        
    final_signal = trend_signal + breakout_status

    # 6. 量价追踪改良版：依照操盘逻辑精准区分放量上涨（抢筹）与放量下跌（出货）
    df['Vol_SMA20'] = volume.rolling(window=20).mean()
    avg_vol = float(df['Vol_SMA20'].iloc[-1])
    price_change = latest_close - float(close.iloc[-2])

    if latest_vol > avg_vol * 1.5:
        vol_status = "🔥 放量上涨" if price_change > 0 else "💥 放量下跌"
    elif latest_vol < avg_vol * 0.7:
        vol_status = "💤 缩量"
    else:
        vol_status = "正常"

    # 7. 顶级投行综合评分多空模型 (Score)
    score = 50
    if trend_signal == "🎯 金叉启动": score += 25
    elif trend_signal == "📈 多头趋势": score += 15
    elif trend_signal == "🚨 死叉确立": score -= 25
    elif trend_signal == "📉 空头动能": score -= 15
    if "🚀 突破阻力" in final_signal: score += 15
    if "🔥 放量上涨" in vol_status: score += 10
    elif "💥 放量下跌" in vol_status: score -= 10
    score = max(10, min(95, score))

    return {
        "Ticker": ticker,
        "Price": round(latest_close, 2),
        "Score": int(score),
        "9 EMA": round(ema_9_now, 2),
        "24 SMA": round(sma_24_now, 2),
        "Support": round(support, 2),
        "Resistance": round(resistance, 2),
        "RSI": round(latest_rsi, 1),
        "Volume Status": vol_status,
        "Signal & Breakout": final_signal
    }
