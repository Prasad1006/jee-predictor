import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  compress: true,
  // Code splitting: separate chunks for predictor and chat
  experimental: {
    optimizePackageImports: ["react", "react-dom"],
  },
  // Image optimization
  images: {
    unoptimized: true,
  },
  // Headers for caching static assets
  async headers() {
    return [
      {
        source: "/_next/static/:path*",
        headers: [
          {
            key: "Cache-Control",
            value: "public, max-age=31536000, immutable",
          },
        ],
      },
    ];
  },
  // Middleware for performance
  onDemandEntries: {
    maxInactiveAge: 60 * 1000,
    pagesBufferLength: 2,
  },
};

export default nextConfig;
