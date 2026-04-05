/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async rewrites() {
    return [
      // Health check endpoints (more specific, must come first)
      {
        source: '/api/mock/health',
        destination: 'http://localhost:8001/health',
      },
      {
        source: '/api/rules/health',
        destination: 'http://localhost:8002/health',
      },
      {
        source: '/api/insight/health',
        destination: 'http://localhost:8003/health',
      },
      {
        source: '/api/audit/health',
        destination: 'http://localhost:8004/health',
      },
      // Proxy to backend services - API endpoints (less specific, comes after)
      {
        source: '/api/mock/:path*',
        destination: 'http://localhost:8001/api/mock/:path*',
      },
      {
        source: '/api/rules/:path*',
        destination: 'http://localhost:8002/api/rules/:path*',
      },
      {
        source: '/api/insight/:path*',
        destination: 'http://localhost:8003/api/insight/:path*',
      },
      {
        source: '/api/audit/:path*',
        destination: 'http://localhost:8004/api/audit/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
