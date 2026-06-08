import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api-flask/:path*',
        destination: `${process.env.FLASK_API_URL || 'http://localhost:5000'}/:path*`,
      },
    ]
  },
}

export default nextConfig
