import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "세종 민원 AI 길잡이",
  description:
    "승인된 공식 행정 지식을 근거로 출처와 다음 행동까지 안내하는 세종 시민 민원 서비스",
};

type RootLayoutProps = Readonly<{
  children: ReactNode;
}>;

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
