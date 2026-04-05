import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BrainDump",
  description: "External Memory for your thoughts",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}
