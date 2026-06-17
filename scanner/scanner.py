from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import pandas as pd

from .indicators import enrich_indicators
from .kiwoom import KiwoomClient, normalize_daily_rows

SIGNAL_MAP = {
    'CCI': 'sig_cci',
    'DMI': 'sig_dmi',
    'MACD': 'sig_macd',
    'STOCH': 'sig_stoch',
}


def classify_cluster(recent: pd.DataFrame) -> str:
    per_day_counts = [sum(bool(row[col]) for col in SIGNAL_MAP.values()) for _, row in recent.iterrows()]
    if any(c >= 4 for c in per_day_counts):
        return '4SAME'
    counts = sorted([c for c in per_day_counts if c > 0], reverse=True)
    if len(counts) >= 2 and counts[0] >= 3 and counts[1] >= 1:
        return '3+1'
    if len(counts) >= 2 and counts[0] >= 2 and counts[1] >= 2:
        return '2+2'
    if sum(1 for c in per_day_counts if c > 0) >= 4:
        return 'SEQ4'
    return 'ACCUM4'


def analyze_one(code: str, name: str, market: str, df: pd.DataFrame, params: Dict) -> Optional[Dict]:
    if len(df) < 130:
        return None

    enriched = enrich_indicators(df, params)
    recent_bars = int(params.get('recent_bars', 5))
    recent = enriched.tail(recent_bars).copy()

    signals_recent: Dict[str, List[str]] = defaultdict(list)
    for _, row in recent.iterrows():
        for key, col in SIGNAL_MAP.items():
            if bool(row[col]):
                signals_recent[key].append(str(row['date']))

    signal_count = sum(1 for key in SIGNAL_MAP if signals_recent.get(key))
    if signal_count < int(params.get('min_signal_count', 4)):
        return None

    last = enriched.iloc[-1]
    prev = enriched.iloc[-2]
    ma_windows = [5, 10, 20, 60, 120]
    ma_ok = all(pd.notna(last[f'ma{w}']) and last['close'] > last[f'ma{w}'] for w in ma_windows)
    if params.get('require_ma_all', True) and not ma_ok:
        return None

    vol_ma20 = enriched['volume'].rolling(20).mean().iloc[-1]
    volume_ratio = float(last['volume'] / vol_ma20) if vol_ma20 and pd.notna(vol_ma20) else 0.0
    if volume_ratio < float(params.get('min_volume_ratio', 2.0)):
        return None

    change_pct = ((float(last['close']) - float(prev['close'])) / float(prev['close']) * 100) if prev['close'] else 0.0
    if change_pct < float(params.get('min_price_change_pct', 0.0)):
        return None

    cluster_type = classify_cluster(recent)
    cluster_bonus = {'4SAME': 40, '3+1': 28, '2+2': 24, 'SEQ4': 18, 'ACCUM4': 16}.get(cluster_type, 0)
    score = cluster_bonus + signal_count * 10 + min(volume_ratio, 8) * 3 + max(change_pct, 0) * 0.7
    last_signal_dates = [d for dates in signals_recent.values() for d in dates]

    return {
        'code': code,
        'name': name,
        'market': market,
        'close': int(round(float(last['close']))),
        'change_pct': round(float(change_pct), 2),
        'volume': int(round(float(last['volume']))),
        'volume_ratio': round(volume_ratio, 2),
        'signal_count': signal_count,
        'cluster_type': cluster_type,
        'score': round(score, 2),
        'ma_status': 'MA5/10/20/60/120 상방' if ma_ok else 'MA 일부 미충족',
        'last_signal_date': max(last_signal_dates) if last_signal_dates else '',
        'signals_recent': dict(signals_recent),
    }


def sample_rows() -> List[Dict]:
    return [
        {
            'code': '403870', 'name': 'HPSP', 'market': 'KOSDAQ', 'close': 83500,
            'change_pct': 16.78, 'volume': 33421000, 'volume_ratio': 4.2,
            'signal_count': 4, 'cluster_type': '4SAME', 'score': 98.5,
            'ma_status': 'MA5/10/20/60/120 상방', 'last_signal_date': '20260615',
            'signals_recent': {'CCI': ['20260615'], 'DMI': ['20260615'], 'MACD': ['20260615'], 'STOCH': ['20260615']},
        },
        {
            'code': '000660', 'name': '샘플반도체', 'market': 'KOSPI', 'close': 185000,
            'change_pct': 6.2, 'volume': 9200000, 'volume_ratio': 2.8,
            'signal_count': 4, 'cluster_type': '3+1', 'score': 87.2,
            'ma_status': 'MA5/10/20/60/120 상방', 'last_signal_date': '20260617',
            'signals_recent': {'CCI': ['20260616'], 'DMI': ['20260617'], 'MACD': ['20260616'], 'STOCH': ['20260616']},
        },
    ]


def scan(client: KiwoomClient, stocks: List[Dict[str, str]], params: Dict) -> List[Dict]:
    results = []
    limit = int(params.get('limit', 0) or 0)
    if limit:
        stocks = stocks[:limit]

    for stock in stocks:
        try:
            rows = client.daily_chart(stock['code'])
            df = normalize_daily_rows(rows)
            candidate = analyze_one(stock['code'], stock.get('name', ''), stock.get('market', ''), df, params)
            if candidate:
                results.append(candidate)
        except Exception as exc:
            print(f"[WARN] {stock.get('code')} {stock.get('name')}: {exc}")

    results.sort(key=lambda x: x['score'], reverse=True)
    for rank, row in enumerate(results, start=1):
        row['rank'] = rank
    return results


def make_payload(candidates: List[Dict], scanned_count: int) -> Dict:
    kst = timezone(timedelta(hours=9))
    return {
        'generated_at': datetime.now(kst).strftime('%Y-%m-%d %H:%M:%S KST'),
        'scanned_count': scanned_count,
        'candidates': candidates,
    }
