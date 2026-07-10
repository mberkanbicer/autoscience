/** @type {import('next').NextConfig} */
const nextConfig = {
  distDir: process.env.NEXT_DIST_DIR || '.next',
  reactStrictMode: true,
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    // Use Docker service name when in container, localhost for local dev
    const apiUrl = process.env.API_URL || (process.env.NEXT_PUBLIC_API_URL ? process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '') : 'http://localhost:8000');
    return [
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,
      },
    ];
  },
  // Proxy timeout for long-running research requests
  experimental: {
    serverComponentsExternalPackages: [],
  },
};

module.exports = nextConfig;
