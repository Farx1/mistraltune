import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // Dockerfile.frontend copies .next/standalone
};

export default nextConfig;
