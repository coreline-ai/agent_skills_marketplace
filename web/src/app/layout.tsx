import type { Metadata } from "next";
import "./globals.css";

import { ThemeProvider } from "@/components/ThemeProvider";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Sidebar } from "@/components/Sidebar";
import { Inter } from "next/font/google";
import { Search, Bell } from "lucide-react";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Agent Skills Marketplace",
  description: "High-quality skills for autonomous agents.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${inter.variable} font-sans antialiased text-foreground min-h-screen selection:bg-accent selection:text-white flex flex-col items-center py-8`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {/* Centered App Container */}
          <div className="w-full max-w-[1440px] min-h-[calc(100vh-4rem)] bg-background dark:bg-black shadow-2xl rounded-2xl flex relative ring-1 ring-gray-900/5 dark:ring-white/10 overflow-hidden">
            <Sidebar />

            <main className="flex-1 relative bg-white/50 dark:bg-black/40" data-purpose="main-wrapper">
              <div className="p-8">
                {/* Header removed as requested */}

                {children}
              </div>
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
