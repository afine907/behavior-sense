/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    return [
      // Proxy to backend services
      {
        source: '/api/mock/:path*',
        destination: `${apiUrl.replace(':8000', ':8001')}/api/:path*`,
      },
      {
        source: '/api/rules/:path*',
        destination: `${apiUrl.replace(':8000', ':8002')}/api/:path*`,
      },
      {
        source: '/api/insight/:path*',
        destination: `${apiUrl.replace(':8000', ':8003')}/api/:path*`,
      },
      {
        source: '/api/audit/:path*',
        destination: `${apiUrl.replace(':8000', ':8004')}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
