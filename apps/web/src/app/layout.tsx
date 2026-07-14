import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "세종 민원 AI 길잡이",
  description:
    "승인된 공식 행정 지식에 근거하는 세종 시민 민원 안내 서비스를 준비하는 화면",
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
