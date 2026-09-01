import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Providers } from "@/app/providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "WoonLens — Compare Dutch homes with official data",
  description:
    "Compare Dutch homes using live, source-backed public data without a hidden score.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
