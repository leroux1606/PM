import type { NextConfig } from "next";

/** When using `next dev`, API calls must reach FastAPI; set if your backend is not on 8001. */
const backendProxy =
  process.env.BACKEND_PROXY_URL ?? "http://127.0.0.1:8001";

const nextConfig: NextConfig = {
  output: "export",
  images: {
    unoptimized: true,
  },
  async rewrites() {
    // Dev only: proxy /api/* to FastAPI. Static export + FastAPI in prod: same origin, no rewrite.
    if (process.env.NODE_ENV !== "development") {
      return [];
    }
    return [
      { source: "/api/:path*", destination: `${backendProxy}/api/:path*` },
    ];
  },
};

export default nextConfig;
