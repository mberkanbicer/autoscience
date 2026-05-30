/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/api/:path*',
      },
    ];
  },
  // Increase timeout for long-running research requests
  experimental: {
    serverComponentsExternalPackages: [],
  },
  // Proxy timeout (default is 30s, we need more for research)
  httpTimeout: 300000, // 5 minutes
};

module.exports = nextConfig;
