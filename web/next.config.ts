import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "origin-when-cross-origin",
          },
          // CSP is tricky to get right without blocking valid scripts (like GTag, etc.)
          // Getting a strict CSP often requires nonces or hashes. 
          // For now, we omit CSP to avoid breaking the app, as requested "Next.js 에 보안 헤더 추가" 
          // usually implies these standard ones. If strict CSP is needed, we need more analysis of used scripts.
        ],
      },
    ];
  },
};

export default nextConfig;
