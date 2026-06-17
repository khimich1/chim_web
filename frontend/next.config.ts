import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Required for frontend/Dockerfile (standalone server.js).
  output: "standalone",
};

export default nextConfig;
