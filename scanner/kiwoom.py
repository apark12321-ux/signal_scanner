from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


def clean_number(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().replace(',', '')
    if s in ('', '-', '+'):
        return 0.0
    return float(s.replace('+', ''))


@dataclass
class KiwoomClient:
    app_key: str
    secret_key: str
    base_url: str = 'https://api.kiwoom.com'
    request_sleep: float = 0.12
    access_token: Optional[str] = None

    @classmethod
    def from_env(cls) -> 'KiwoomClient':
        return cls(
            app_key=os.environ['KIWOOM_APP_KEY'],
            secret_key=os.environ['KIWOOM_SECRET_KEY'],
            base_url=os.environ.get('KIWOOM_BASE_URL', 'https://api.kiwoom.com'),
            request_sleep=float(os.environ.get('SCAN_REQUEST_SLEEP', '0.12')),
        )

    def issue_token(self) -> str:
        res = requests.post(
            f'{self.base_url}/oauth2/token',
            json={
                'grant_type': 'client_credentials',
                'appkey': self.app_key,
                'secretkey': self.secret_key,
            },
            timeout=20,
        )
        res.raise_for_status()
        data = res.json()
        token = data.get('token') or data.get('access_token')
        if not token:
            raise RuntimeError(f'Kiwoom token response has no token: {data}')
        self.access_token = token
        return token

    def request(self, api_id: str, url_path: str, body: Dict[str, Any], next_key: str = '') -> tuple[Dict[str, Any], Dict[str, str]]:
        if not self.access_token:
            self.issue_token()
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {self.access_token}',
            'api-id': api_id,
            'cont-yn': 'Y' if next_key else 'N',
            'next-key': next_key,
        }
        time.sleep(self.request_sleep)
        res = requests.post(f'{self.base_url}{url_path}', headers=headers, json=body, timeout=30)
        res.raise_for_status()
        return res.json(), {k.lower(): v for k, v in res.headers.items()}

    def stock_list(self, market_type: str = '0') -> List[Dict[str, str]]:
        data, _ = self.request('ka10099', '/api/dostk/stkinfo', {'mrkt_tp': market_type})
        rows = data.get('list') or data.get('stk_info') or data.get('stk_cd_list') or data.get('stk_list') or []
        stocks: List[Dict[str, str]] = []
        for row in rows:
            code = str(row.get('stk_cd') or row.get('code') or row.get('종목코드') or '').replace('A', '').strip()
            name = str(row.get('stk_nm') or row.get('name') or row.get('종목명') or '').strip()
            market = str(row.get('mrkt_cls') or row.get('market') or '')
            if code and name:
                stocks.append({'code': code, 'name': name, 'market': market})
        return stocks

    def daily_chart(self, code: str, base_date: str = '', adj: str = '1') -> List[Dict[str, Any]]:
        body = {'stk_cd': code, 'base_dt': base_date, 'upd_stkpc_tp': adj}
        all_rows: List[Dict[str, Any]] = []
        next_key = ''
        while True:
            data, headers = self.request('ka10081', '/api/dostk/chart', body, next_key=next_key)
            rows = data.get('stk_dt_pole_chart_qry') or data.get('stk_daily_chart_qry') or data.get('output') or data.get('list') or []
            all_rows.extend(rows)
            cont = headers.get('cont-yn') or headers.get('cont_yn') or 'N'
            next_key = headers.get('next-key') or headers.get('next_key') or ''
            if cont != 'Y' or not next_key or len(all_rows) >= 260:
                break
        return all_rows


def normalize_daily_rows(rows: List[Dict[str, Any]]):
    import pandas as pd

    normalized = []
    for r in rows:
        date = str(r.get('dt') or r.get('date') or r.get('일자') or r.get('trde_dt') or '').strip()
        if not date:
            continue
        normalized.append({
            'date': date,
            'open': abs(clean_number(r.get('open_pric') or r.get('open') or r.get('시가'))),
            'high': abs(clean_number(r.get('high_pric') or r.get('high') or r.get('고가'))),
            'low': abs(clean_number(r.get('low_pric') or r.get('low') or r.get('저가'))),
            'close': abs(clean_number(r.get('cur_prc') or r.get('close_pric') or r.get('close') or r.get('현재가') or r.get('종가'))),
            'volume': abs(clean_number(r.get('trde_qty') or r.get('volume') or r.get('거래량'))),
        })
    df = pd.DataFrame(normalized)
    if df.empty:
        return df
    return df.drop_duplicates('date').sort_values('date').reset_index(drop=True)
