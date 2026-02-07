import type { Metadata } from "next";
import { Plus_Jakarta_Sans, Noto_Sans_KR } from "next/font/google";
import "./globals.css";
import Link from "next/link";

import { ThemeProvider } from "@/components/ThemeProvider";
import { ThemeToggle } from "@/components/ThemeToggle";

const jakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-jakarta",
  display: "swap",
});

const notoSansKR = Noto_Sans_KR({
  subsets: ["latin"],
  variable: "--font-noto",
  weight: ["100", "300", "400", "500", "700", "900"],
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
        className={`${jakarta.variable} ${notoSansKR.variable} font-sans antialiased bg-white dark:bg-black text-black dark:text-white min-h-screen flex flex-col`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <header className="bg-white dark:bg-black border-b-2 border-black sticky top-0 z-50 dark:border-white">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 flex items-center justify-between py-4">
              <Link href="/" className="font-extrabold text-2xl tracking-tight flex items-center gap-2 border-2 border-black bg-accent px-3 py-1 dark:shadow-none dark:hover:translate-x-0 dark:hover:translate-y-0 dark:hover:shadow-none transition-all text-black">
                Agent Skills
              </Link>
              <nav className="flex items-center gap-4 sm:gap-8">
                <Link href="/skills" className="font-bold text-lg hover:underline decoration-2 underline-offset-4 decoration-accent text-black dark:text-white">
                  Skills
                </Link>
                <Link href="/guide" className="font-bold text-lg hover:underline decoration-2 underline-offset-4 decoration-accent text-black dark:text-white">
                  Guide
                </Link>
                <Link href="/rankings" className="font-bold text-lg hover:underline decoration-2 underline-offset-4 decoration-accent text-black dark:text-white">
                  Rankings
                </Link>
                <Link href="/admin/login" className="hidden sm:block font-bold text-sm border-2 border-black px-4 py-2 bg-white dark:bg-black text-black dark:text-white hover:bg-black hover:text-white dark:hover:bg-white dark:hover:text-black transition-colors dark:shadow-none dark:active:translate-x-0 dark:active:translate-y-0">
                  Admin
                </Link>
                <ThemeToggle />
              </nav>
            </div>
          </header>
          <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-12">
            {children}
          </main>
          <footer className="bg-white dark:bg-black border-t-2 border-black dark:border-white py-8 mt-auto">
            <div className="max-w-7xl mx-auto px-4 text-center font-bold text-black dark:text-white">
              &copy; {new Date().getFullYear()} AI Agent Skills Marketplace. Built with <span className="bg-accent px-1 text-black font-black">Coreline</span>.
            </div>
          </footer>
        </ThemeProvider>
      </body>
    </html>
  );
}
