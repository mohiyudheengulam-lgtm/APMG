import type { NextConfig } from "next";

const API = process.env.AOD_API_URL ?? "http://127.0.0.1:8000";

// AOD_EXPORT=1: static build served by the Python API (single process, `agent-on-duty`); same origin, so no proxy.
// Otherwise (development): Next.js dev server proxies /api to the local API.
const nextConfig: NextConfig = process.env.AOD_EXPORT
  ? { output: "export", trailingSlash: true, images: { unoptimized: true }, devIndicators: false }
  : {
      devIndicators: { position: "bottom-right" },
      async rewrites() {
        return [{ source: "/api/:path*", destination: `${API}/api/:path*` }];
      },
    };

export default nextConfig;
