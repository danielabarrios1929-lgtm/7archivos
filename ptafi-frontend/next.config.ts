import type { NextConfig } from "next";

const isDevelopment = process.env.NODE_ENV !== 'production';

const nextConfig: NextConfig = {
  async rewrites() {
    if (isDevelopment) {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ];
    }
    return []; // En producción (Vercel) las rutas /api las maneja vercel.json
  },
};

export default nextConfig;
