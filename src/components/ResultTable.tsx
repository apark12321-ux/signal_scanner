'use client';

import { useMemo, useState } from 'react';

type Candidate = {
  rank: number;
  code: string;
  name: string;
  market?: string;
  close: number;
  change_pct: number;
  volume: number;
  volume_ratio: number;
  signal_count: number;
  cluster_type: string;
  score: number;
  ma_status: string;
  last_signal_date: string;
  signals_recent: Record<string, string[]>;
};

function fmtNumber(n: number | undefined) {
  if (n === undefined || Number.isNaN(n)) return '-';
  return new Intl.NumberFormat('ko-KR').format(n);
}

function fmtPct(n: number | undefined) {
  if (n === undefined || Number.isNaN(n)) return '-';
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`;
}

function signalOn(candidate: Candidate, key: string) {
  return Boolean(candidate.signals_recent?.[key]?.length);
}

export default function ResultTable({ candidates }: { candidates: Candidate[] }) {
  const [query, setQuery] = useState('');
  const [cluster, setCluster] = useState('ALL');
  const [minSignals, setMinSignals] = useState('4');

  const filtered = useMemo(() => {
    return candidates.filter((c) => {
      const q = query.trim().toLowerCase();
      const matchesQuery = !q || c.name.toLowerCase().includes(q) || c.code.includes(q);
      const matchesCluster = cluster === 'ALL' || c.cluster_type === cluster;
      const matchesSignals = c.signal_count >= Number(minSignals);
      return matchesQuery && matchesCluster && matchesSignals;
    });
  }, [candidates, query, cluster, minSignals]);

  return (
    <>
      <div className="controls">
        <input placeholder="종목명/종목코드 검색" value={query} onChange={(e) => setQuery(e.target.value)} />
        <select value={cluster} onChange={(e) => setCluster(e.target.value)}>
          <option value="ALL">전체 유형</option>
          <option value="4SAME">4개 동시</option>
          <option value="3+1">3+1</option>
          <option value="2+2">2+2</option>
          <option value="ACCUM4">누적 4개</option>
          <option value="SEQ4">연속 4개</option>
        </select>
        <select value={minSignals} onChange={(e) => setMinSignals(e.target.value)}>
          <option value="4">4신호 이상</option>
          <option value="3">3신호 이상</option>
          <option value="2">2신호 이상</option>
        </select>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>순위</th>
              <th>종목</th>
              <th>시장</th>
              <th>유형</th>
              <th>점수</th>
              <th>4신호</th>
              <th>종가</th>
              <th>등락률</th>
              <th>거래량</th>
              <th>거래량배수</th>
              <th>이평상태</th>
              <th>최근 신호일</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr key={c.code}>
                <td>{c.rank}</td>
                <td><b>{c.name}</b><br /><span className="muted">{c.code}</span></td>
                <td>{c.market || '-'}</td>
                <td><span className={`badge ${c.cluster_type === '4SAME' ? 'hot' : c.cluster_type === '3+1' ? 'good' : 'warn'}`}>{c.cluster_type}</span></td>
                <td><b>{c.score.toFixed(1)}</b></td>
                <td>
                  <div className="signals">
                    <span className={`signal ${signalOn(c, 'CCI') ? 'on' : ''}`}>CCI</span>
                    <span className={`signal ${signalOn(c, 'DMI') ? 'on' : ''}`}>DMI</span>
                    <span className={`signal ${signalOn(c, 'MACD') ? 'on' : ''}`}>MACD</span>
                    <span className={`signal ${signalOn(c, 'STOCH') ? 'on' : ''}`}>STO</span>
                  </div>
                </td>
                <td>{fmtNumber(c.close)}</td>
                <td className={c.change_pct >= 0 ? 'up' : 'down'}>{fmtPct(c.change_pct)}</td>
                <td>{fmtNumber(c.volume)}</td>
                <td>{c.volume_ratio.toFixed(2)}x</td>
                <td>{c.ma_status}</td>
                <td>{c.last_signal_date || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
