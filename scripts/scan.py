#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

from scanner.kiwoom import KiwoomClient
from scanner.scanner import make_payload, sample_rows, scan


def get_params(args):
    return {
        'cci_window': int(os.environ.get('SCAN_CCI_WINDOW', '20')),
        'cci_baseline': float(os.environ.get('SCAN_CCI_BASELINE', '0')),
        'dmi_window': int(os.environ.get('SCAN_DMI_WINDOW', '14')),
        'macd_fast': int(os.environ.get('SCAN_MACD_FAST', '12')),
        'macd_slow': int(os.environ.get('SCAN_MACD_SLOW', '26')),
        'macd_signal': int(os.environ.get('SCAN_MACD_SIGNAL', '9')),
        'stoch_k': int(os.environ.get('SCAN_STOCH_K', '12')),
        'stoch_smooth': int(os.environ.get('SCAN_STOCH_SMOOTH', '5')),
        'stoch_d': int(os.environ.get('SCAN_STOCH_D', '5')),
        'recent_bars': int(os.environ.get('SCAN_RECENT_BARS', '5')),
        'min_signal_count': int(os.environ.get('SCAN_MIN_SIGNAL_COUNT', '4')),
        'min_volume_ratio': float(os.environ.get('SCAN_MIN_VOLUME_RATIO', '2.0')),
        'min_price_change_pct': float(os.environ.get('SCAN_MIN_PRICE_CHANGE_PCT', '0')),
        'require_ma_all': os.environ.get('SCAN_REQUIRE_MA_ALL', 'true').lower() == 'true',
        'limit': args.limit if args.limit is not None else int(os.environ.get('SCAN_LIMIT', '0')),
    }


def main():
    parser = argparse.ArgumentParser(description='HPSP-type 4-signal cluster scanner')
    parser.add_argument('--output', default='public/data/latest.json')
    parser.add_argument('--sample', action='store_true')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--codes', default='', help='Comma separated stock codes for smoke test')
    args = parser.parse_args()

    load_dotenv()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.sample:
        candidates = sample_rows()
        for rank, row in enumerate(candidates, start=1):
            row['rank'] = rank
        payload = make_payload(candidates, scanned_count=len(candidates))
    else:
        client = KiwoomClient.from_env()
        params = get_params(args)
        if args.codes:
            stocks = [{'code': code.strip(), 'name': code.strip(), 'market': 'MANUAL'} for code in args.codes.split(',') if code.strip()]
        else:
            stocks = client.stock_list(os.environ.get('KIWOOM_MARKET_TP', '0'))
        candidates = scan(client, stocks, params)
        payload = make_payload(candidates, scanned_count=len(stocks))

    tmp = output_path.with_suffix('.tmp')
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(output_path)
    print(f"saved: {output_path} candidates={len(payload['candidates'])}")


if __name__ == '__main__':
    main()
