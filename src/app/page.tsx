import fs from 'fs';
import path from 'path';
import ResultTable from '../components/ResultTable';

async function getData() {
  const filePath = path.join(process.cwd(), 'public', 'data', 'latest.json');
  const raw = fs.readFileSync(filePath, 'utf-8');
  return JSON.parse(raw);
}

export default async function Home() {
  const data = await getData();
  const candidates = data.candidates || [];
  const fourSame = candidates.filter((c: any) => c.cluster_type === '4SAME').length;
  const threeOne = candidates.filter((c: any) => c.cluster_type === '3+1').length;
  const twoTwo = candidates.filter((c: any) => c.cluster_type === '2+2').length;

  return (
    <main className="container">
      <section className="header">
        <div>
          <div className="eyebrow">KIWOOM REST API × GitHub Actions × Vercel</div>
          <h1>HPSP형 4신호 클러스터 탐색기</h1>
          <p className="subtitle">
            최근 5영업일 안에 CCI, DMI, MACD, Stochastic 4개 신호가 4개 동시·3+1·2+2·누적4 형태로 몰린 종목을 자동 선별합니다.
          </p>
        </div>
        <div className="status-card">
          <b>최근 스캔</b>
          <span>{data.generated_at || '-'}</span>
          <p>대상 {data.scanned_count || 0}개 / 후보 {candidates.length}개</p>
        </div>
      </section>

      <section className="grid">
        <div className="metric"><div className="label">전체 후보</div><div className="value">{candidates.length}</div></div>
        <div className="metric"><div className="label">4개 동시</div><div className="value">{fourSame}</div></div>
        <div className="metric"><div className="label">3+1</div><div className="value">{threeOne}</div></div>
        <div className="metric"><div className="label">2+2</div><div className="value">{twoTwo}</div></div>
      </section>

      <ResultTable candidates={candidates} />

      <p className="footer-note">
        이 대시보드는 자동주문을 수행하지 않습니다. 거래대금, 투자주의/경고, 관리종목, 투자주의환기, DART/KIND 공시 리스크를 추가 확인한 뒤 판단해야 합니다.
      </p>
    </main>
  );
}
