import type { Metadata } from "next";

import { DecorativeBlobs } from "@/components/ui/DecorativeBlobs";
import "./globals.css";

export const metadata: Metadata = {
  title: "chim_web — химия",
  description: "Платформа для репетитора по химии и учеников",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className="h-full antialiased">
      <body className="chem-surface relative min-h-full flex flex-col">
        <DecorativeBlobs />
        {children}
      </body>
    </html>
  );
}
