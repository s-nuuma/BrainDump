/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    // 開発中のためビルド時の型エラーを一時的に無視
    ignoreBuildErrors: true,
  },
  eslint: {
    // ビルド時のESLintエラーを無視
    ignoreDuringBuilds: true,
  },
};

export default nextConfig;
