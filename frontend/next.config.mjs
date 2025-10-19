/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: process.env.NETLIFY ? "export" : undefined
};

export default nextConfig;
