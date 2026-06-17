# HPSP형 4신호 클러스터 탐색기

키움 REST API로 일봉 데이터를 가져와 최근 5영업일 안에 아래 4개 신호가 몰린 종목을 찾고, Vercel 대시보드로 보여주는 프로젝트입니다.

- CCI 기준선 상향돌파
- DMI +DI가 -DI 상향돌파
- MACD 골든크로스
- Stochastic 골든크로스

## 구조

```text
Kiwoom REST API
→ GitHub Actions 정기 실행
→ public/data/latest.json 생성/커밋
→ Vercel 자동 배포
→ 웹 대시보드 표시
```

## 로컬 실행

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/scan.py --sample
npm install
npm run dev
```

## 실제 키움 API 스캔

```bash
python scripts/scan.py --codes 403870,005930,000660 --output public/data/latest.json
```

전체 종목:

```bash
python scripts/scan.py --output public/data/latest.json
```

## GitHub 설정

Repository → Settings → Secrets and variables → Actions에 아래 값을 추가합니다.

- `KIWOOM_APP_KEY`
- `KIWOOM_SECRET_KEY`
- `KIWOOM_BASE_URL` = `https://api.kiwoom.com`

그 다음 Actions 탭에서 `scan-and-publish`를 수동 실행합니다.

## Vercel 설정

1. Vercel → Add New Project
2. GitHub 저장소 Import
3. Framework Preset: Next.js
4. Deploy

GitHub Actions가 `public/data/latest.json`을 갱신해 push하면 Vercel이 자동 배포합니다.

## 신호 분류

- `4SAME`: 같은 날 4개 신호 동시 발생
- `3+1`: 하루 3개 + 다른 하루 1개
- `2+2`: 하루 2개 + 다른 하루 2개
- `SEQ4`: 최근 5영업일 중 4일 이상에 신호 발생
- `ACCUM4`: 최근 5영업일 안에 4개 신호가 모두 1회 이상 발생

## 주의

이 프로젝트는 후보 탐색용입니다. 자동주문은 구현하지 않았습니다. 매수 판단 전 거래대금, VI, 투자주의/경고, 관리종목, 투자주의환기, DART/KIND 공시 리스크를 별도로 확인해야 합니다.

키움 API 응답 필드명은 계정/문서 개정에 따라 달라질 수 있어 `scanner/kiwoom.py`에서 다중 필드명을 허용하도록 작성했습니다.
