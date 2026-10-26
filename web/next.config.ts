import type { NextConfig } from "next";
import path from "node:path";

const config: NextConfig = {
  outputFileTracingRoot: path.resolve(import.meta.dirname, ".."),
  poweredByHeader: false,
  async headers() {
    return [{ source: "/:path*", headers: [
      {key: "X-Content-Type-Options", value: "nosniff"},
      {key: "Referrer-Policy", value: "no-referrer"},
      {key: "X-Frame-Options", value: "DENY"},
      ...(process.env.NODE_ENV==='production'?[{key:'Content-Security-Policy',value:"default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"}]:[])
    ] }];
  }
};
export default config;
