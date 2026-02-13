"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, List, ShieldCheck, LogOut, Globe, ArrowUpRight } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { clearAdminSession, getAdminToken } from "@/lib/admin-auth";

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();
    const router = useRouter();
    const isLoginPage = pathname === "/admin/login";
    const [authReady, setAuthReady] = useState(false);
    useEffect(() => {
        let mounted = true;

        if (isLoginPage) {
            return () => {
                mounted = false;
            };
        }

        const token = getAdminToken();
        if (!token) {
            router.replace("/admin/login");
            return () => {
                mounted = false;
            };
        }

        api.get<{ username: string }>("/admin/me", token)
            .then(() => {
                if (mounted) setAuthReady(true);
            })
            .catch((error) => {
                if (error instanceof ApiError && error.status === 401) {
                    clearAdminSession();
                    router.replace("/admin/login");
                    return;
                }
                // Keep session on transient errors (network/server). Avoid forced relogin loops.
                if (mounted) setAuthReady(true);
            });

        return () => {
            mounted = false;
        };
    }, [isLoginPage, router]);

    // Login page uses the main layout (with sidebar) - pass through completely
    if (isLoginPage) {
        return <>{children}</>;
    }

    if (!authReady) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-black text-white font-sans">
                <div className="relative mb-8">
                    <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center animate-pulse">
                        <ShieldCheck className="w-8 h-8 text-white" />
                    </div>
                </div>
                <div className="flex flex-col items-center gap-2">
                    <p className="text-sm font-semibold tracking-widest uppercase text-zinc-500">Security Check</p>
                    <h1 className="text-lg font-medium text-white/90">관리자 세션을 확인 중입니다...</h1>
                </div>
            </div>
        );
    }

    const navItems = [
        { href: "/admin/dashboard", label: "대시보드", icon: LayoutDashboard },
        { href: "/admin/crawling", label: "플러그인 관리", icon: Globe },
        { href: "/admin/skills", label: "스킬 관리", icon: List },
        { href: "/admin/quality", label: "품질 관리", icon: ShieldCheck },
    ];

    const handleSignOut = () => {
        clearAdminSession();
        router.replace("/admin/login");
    };

    return (
        <div className="min-h-screen bg-black flex justify-center py-0 sm:py-8 font-sans text-white selection:bg-white/20">
            {/* Centered Admin Container */}
            <div className="w-full max-w-[1440px] bg-black sm:rounded-[32px] flex overflow-hidden ring-1 ring-white/10 min-h-screen sm:min-h-[calc(100vh-4rem)] sm:mx-4 relative shadow-[0_0_50px_-12px_rgba(255,255,255,0.05)]">

                {/* Admin Sidebar */}
                <aside className="w-[240px] bg-zinc-950 border-r border-white/5 flex flex-col flex-shrink-0">
                    <div className="p-8 border-b border-white/5">
                        <Link href="/" className="font-bold text-lg text-white flex items-center gap-2 hover:opacity-80 transition-opacity group">
                            <div className="w-8 h-8 rounded-xl bg-white flex items-center justify-center text-black shadow-lg group-hover:scale-105 transition-transform">
                                <ShieldCheck className="w-4.5 h-4.5" />
                            </div>
                            <span className="tracking-tight">Admin Console</span>
                        </Link>
                    </div>

                    <nav className="flex-1 px-4 py-8 space-y-1 overflow-y-auto custom-scrollbar">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = pathname.startsWith(item.href);
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`flex items-center gap-3 px-4 py-3 rounded-2xl text-sm font-medium transition-all duration-300 group ${isActive
                                        ? "bg-white text-black shadow-[0_4px_12px_rgba(255,255,255,0.1)]"
                                        : "text-zinc-500 hover:bg-white/5 hover:text-white"
                                        }`}
                                >
                                    <Icon className={`w-4.5 h-4.5 ${isActive ? "text-black" : "text-zinc-600 group-hover:text-zinc-300"}`} />
                                    {item.label}
                                </Link>
                            );
                        })}
                    </nav>

                    <div className="p-6 border-t border-white/5 mt-auto">
                        <button
                            type="button"
                            onClick={handleSignOut}
                            className="flex items-center gap-3 px-4 py-3 w-full text-left text-xs font-semibold text-zinc-500 hover:text-red-400 hover:bg-red-400/10 rounded-2xl transition-all group"
                        >
                            <LogOut className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                            Sign Out
                        </button>
                    </div>
                </aside>

                {/* Main Content Area */}
                <main className="flex-1 overflow-y-auto bg-black relative custom-scrollbar">
                    <div className="h-full flex flex-col">
                        <header className="sticky top-0 z-20 bg-black/80 backdrop-blur-xl border-b border-white/5 px-8 h-20 flex justify-between items-center">
                            <div>
                                <h2 className="text-xs font-bold text-zinc-500 uppercase tracking-[0.2em]">
                                    {navItems.find(i => pathname.startsWith(i.href))?.label || "Console"}
                                </h2>
                            </div>
                            <div className="flex items-center gap-6">
                                <Link href="/" className="text-xs font-bold text-zinc-400 hover:text-white transition-colors flex items-center gap-1.5 group">
                                    Return to Market
                                    <ArrowUpRight className="w-3.5 h-3.5 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 transition-transform" />
                                </Link>
                                <div className="h-4 w-px bg-white/10" />
                                <div className="flex items-center gap-2">
                                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-wider">System Live</span>
                                </div>
                            </div>
                        </header>

                        <div className="flex-1 p-8 sm:p-12 w-full max-w-7xl mx-auto">
                            {children}
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}

