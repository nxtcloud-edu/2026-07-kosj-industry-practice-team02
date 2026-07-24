import type { NextConfig } from "next";

const localApiBaseUrl = process.env.API_INTERNAL_BASE_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // Next 15.2+/16 dev 서버는 dev 리소스(/_next/webpack-hmr, Fast Refresh, RSC)에
  // 대한 cross-origin 요청을 기본 차단한다. 이 앱은 README·런북 기준 접속 호스트가
  // 127.0.0.1(예: http://127.0.0.1:3000)이지만 dev 서버 정규 origin은 localhost라,
  // 127.0.0.1 접속 시 dev 리소스가 차단되어 클라이언트 hydration이 완료되지 못한다
  // (프로덕션 next start에는 이 검사가 없어 재현되지 않음). loopback 호스트를 허용한다.
  allowedDevOrigins: ["127.0.0.1"],
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${localApiBaseUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
