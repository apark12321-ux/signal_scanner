import fs from 'fs';
import path from 'path';

type Candidate = {
  rank?: number;
  code?: string;
  name?: string;
  close?: number;
  change_pct?: number;
  volume_ratio?: number;
  pattern?: string;
  signals?: string[];
  signal_dates?: Record<string, string>;
  score?: number;
};

type LatestData = {
  generated_at?: string;
  market_date?: string;
  count?: number;
  candidates?: Candidate[];
};

async function loadLatest(): Promise<LatestData> {
  const file = path.join(process.cwd(), 'public', 'data', 'latest.json');
  try {
    const raw = fs.readFileSync(file, 'utf-8');
    return JSON.parse(raw) as LatestData;
  } catch {
    return {
      generated_at: new Date().toISOString(),
      market_date: '-',
      count: 0,
      candidates: [],
    };
  }
}

function fmtNumber(value?: number) {
  if (value === undefined || value === null || Number.isNaN(value)) return '-';
  return new Intl.NumberFormat('ko-KR').format(value);
}

function fmtPct(value?: number) {
  if (value === undefined || value === null || Number.isNaN(value)) return '-';
  return `${value.toFixed(2)}%`;
}

export default async function Page() {
  const data = await loadLatest();
  const candidates = data.candidates ?? [];

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="mx-auto max-w-7xl px-6 py-10">
        <div className="mb-8 rounded-3xl border border-slate-800 bg-slate-900/70 p-8 shadow-2xl">
          <p className="mb-3 text-sm font-semibold tracking-[0.25em] text-cyan-300">HPSP SIGNAL SCANNER</p>
          <h1 className="text-3xl font-bold md:text-5xl">4신호 클러스터 종목 탐색기</h1>
          <p className="mt-4 max-w-3xl text-slate-300">
            최근 5영업일 안에 CCI, DMI, MACD, Stochastic 신호가 4개동시·3+1·2+2·연속·누적 형태로 몰려 나온 종목을 추립니다.
          </p>
          <div className="mt-6 grid gap-3 text-sm text-slate-300 md:grid-cols-3">
            <div className="rounded-2xl bg-slate-800/80 p-4">
              <div className="text-slate-400">생성 시각</div>
              <div className="mt-1 font-semibold text-white">{data.generated_at ?? '-'}</div>
            </div>
            <div className="rounded-2xl bg-slate-800/80 p-4">
              <div className="text-slate-400">기준일</div>
              <div className="mt-1 font-semibold text-white">{data.market_date ?? '-'}</div>
            </div>
            <div className="rounded-2xl bg-slate-800/80 p-4">
              <div className="text-slate-400">후보 수</div>
              <div className="mt-1 font-semibold text-white">{fmtNumber(data.count ?? candidates.length)}</div>
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-3xl border border-slate-800 bg-slate-900/70">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[980px] border-collapse text-sm">
              <thead className="bg-slate-800 text-left text-slate-300">
                <tr>
                  <th className="px-4 py-3">순위</th>
                  <th className="px-4 py-3">종목</th>
                  <th className="px-4 py-3">코드</th>
                  <th className="px-4 py-3 text-right">종가</th>
                  <th className="px-4 py-3 text-right">등락률</th>
                  <th className="px-4 py-3 text-right">거래량배수</th>
                  <th className="px-4 py-3">패턴</th>
                  <th className="px-4 py-3">신호</th>
                  <th className="px-4 py-3 text-right">점수</th>
                </tr>
              </thead>
              <tbody>
                {candidates.length === 0 ? (
                  <tr>
                    <td className="px-4 py-10 text-center text-slate-400" colSpan={9}>
                      아직 후보 데이터가 없습니다. GitHub Actions의 scan-and-publish를 실행하면 public/data/latest.json이 갱신됩니다.
                    </td>
                  </tr>
                ) : (
                  candidates.map((item, idx) => (
                    <tr key={`${item.code}-${idx}`} className="border-t border-slate-800 hover:bg-slate-800/50">
                      <td className="px-4 py-3 text-slate-300">{item.rank ?? idx + 1}</td>
                      <td className="px-4 py-3 font-semibold text-white">{item.name ?? '-'}</td>
                      <td className="px-4 py-3 text-slate-300">{item.code ?? '-'}</td>
                      <td className="px-4 py-3 text-right">{fmtNumber(item.close)}</td>
                      <td className="px-4 py-3 text-right text-rose-300">{fmtPct(item.change_pct)}</td>
                      <td className="px-4 py-3 text-right">{item.volume_ratio ? `${item.volume_ratio.toFixed(2)}x` : '-'}</td>
                      <td className="px-4 py-3">
                        <span className="rounded-full bg-cyan-400/10 px-3 py-1 text-xs font-semibold text-cyan-200">{item.pattern ?? '-'}</span>
                      </td>
                      <td className="px-4 py-3 text-slate-300">{(item.signals ?? []).join(', ') || '-'}</td>
                      <td className="px-4 py-3 text-right font-semibold">{item.score ?? '-'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <p className="mt-6 text-xs leading-6 text-slate-500">
          본 화면은 자동매매가 아닌 후보 탐색용입니다. 실제 매수 전에는 호가, 거래대금, 투자주의/환기/관리종목, DART/KIND 공시 리스크를 반드시 확인해야 합니다.
        </p>
      </section>
    </main>
  );
}
