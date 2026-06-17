from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=window).mean()


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False, min_periods=span).mean()


def cross_up(a: pd.Series, b: pd.Series | float | int) -> pd.Series:
    if isinstance(b, (float, int)):
        b = pd.Series([b] * len(a), index=a.index)
    return (a.shift(1) <= b.shift(1)) & (a > b)


def cci(df: pd.DataFrame, window: int = 20) -> pd.Series:
    tp = (df['high'] + df['low'] + df['close']) / 3
    ma = tp.rolling(window=window, min_periods=window).mean()
    md = tp.rolling(window=window, min_periods=window).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    return (tp - ma) / (0.015 * md)


def dmi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    high, low, close = df['high'], df['low'], df['close']
    up = high.diff()
    down = -low.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)
    tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(window=window, min_periods=window).sum()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(window=window, min_periods=window).sum() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(window=window, min_periods=window).sum() / atr
    adx = (((plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)) * 100).rolling(window=window, min_periods=window).mean()
    return pd.DataFrame({'plus_di': plus_di, 'minus_di': minus_di, 'adx': adx})


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return pd.DataFrame({'macd': line, 'macd_signal': sig, 'macd_hist': line - sig})


def stochastic(df: pd.DataFrame, k_window: int = 12, k_smooth: int = 5, d_window: int = 5) -> pd.DataFrame:
    lo = df['low'].rolling(window=k_window, min_periods=k_window).min()
    hi = df['high'].rolling(window=k_window, min_periods=k_window).max()
    raw_k = (df['close'] - lo) / (hi - lo).replace(0, np.nan) * 100
    k = raw_k.rolling(window=k_smooth, min_periods=k_smooth).mean()
    d = k.rolling(window=d_window, min_periods=d_window).mean()
    return pd.DataFrame({'stoch_k': k, 'stoch_d': d})


def enrich_indicators(df: pd.DataFrame, params: dict) -> pd.DataFrame:
    out = df.copy()
    for w in [5, 10, 20, 60, 120]:
        out[f'ma{w}'] = sma(out['close'], w)
    out['cci'] = cci(out, params.get('cci_window', 20))
    out = pd.concat([
        out,
        dmi(out, params.get('dmi_window', 14)),
        macd(out['close'], params.get('macd_fast', 12), params.get('macd_slow', 26), params.get('macd_signal', 9)),
        stochastic(out, params.get('stoch_k', 12), params.get('stoch_smooth', 5), params.get('stoch_d', 5)),
    ], axis=1)
    out['sig_cci'] = cross_up(out['cci'], params.get('cci_baseline', 0))
    out['sig_dmi'] = cross_up(out['plus_di'], out['minus_di'])
    out['sig_macd'] = cross_up(out['macd'], out['macd_signal'])
    out['sig_stoch'] = cross_up(out['stoch_k'], out['stoch_d'])
    return out
