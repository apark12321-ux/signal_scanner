import './globals.css';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'HPSP형 4신호 클러스터 탐색기',
  description: 'CCI/DMI/MACD/Stochastic 신호 집중 종목 탐색 대시보드'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
