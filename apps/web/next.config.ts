import type { NextConfig } from "next";

const localApiBaseUrl = process.env.API_INTERNAL_BASE_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
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
