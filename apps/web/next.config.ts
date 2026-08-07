import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async redirects() {
    return [
      {
        source: '/settings',
        destination: '/dashboard/settings',
        permanent: true,
      },
    ];
  },
};

export default nextConfig;
