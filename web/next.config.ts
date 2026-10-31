import type { NextConfig } from "next";

// Site estático: tudo roda no navegador, sem servidor.
const nextConfig: NextConfig = {
  output: "export",
};

export default nextConfig;
