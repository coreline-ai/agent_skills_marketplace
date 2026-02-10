"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, List, ShieldCheck, LogOut, Globe } from "lucide-react";
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
            <div className="min-h-screen flex items-center justify-center bg-gray-100 text-gray-600 text-sm">
                Verifying admin session...
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
        <div className="min-h-screen bg-white flex justify-center py-8 font-sans text-gray-900">
            {/* Centered Admin Container */}
            <div className="w-full max-w-[1440px] bg-white rounded-3xl shadow-2xl flex overflow-hidden ring-1 ring-gray-900/5 min-h-[calc(100vh-4rem)] mx-4">

                {/* Admin Sidebar */}
                <aside className="w-[220px] bg-white border-r border-gray-100 flex flex-col flex-shrink-0">
                    <div className="p-6 border-b border-gray-100">
                        <Link href="/" className="font-bold text-lg text-gray-900 flex items-center gap-1.5 hover:opacity-80 transition-opacity">
                            <div className="w-6 h-6 rounded bg-gray-900 flex items-center justify-center text-white">
                                <ShieldCheck className="w-3.5 h-3.5" />
                            </div>
                            <span>Admin</span>
                        </Link>
                    </div>

                    <nav className="flex-1 px-3 py-6 space-y-1 overflow-y-auto">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = pathname.startsWith(item.href);
                            return (
                                <Link
                                    key={item.href}
                                    href={item.href}
                                    className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${isActive
                                        ? "bg-white text-gray-900 shadow-sm ring-1 ring-gray-200"
                                        : "text-gray-500 hover:bg-white/60 hover:text-gray-900"
                                        }`}
                                >
                                    <Icon className={`w-4 h-4 ${isActive ? "text-gray-900" : "text-gray-400 group-hover:text-gray-600"}`} />
                                    {item.label}
                                </Link>
                            );
                        })}
                    </nav>

                    <div className="p-4 border-t border-gray-100 mt-auto">
                        <button
                            type="button"
                            onClick={handleSignOut}
                            className="flex items-center gap-3 px-3 py-2.5 w-full text-left text-xs font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                        >
                            <LogOut className="w-4 h-4" />
                            Sign Out
                        </button>
                    </div>
                </aside>

                {/* Main Content Area */}
                <main className="flex-1 overflow-y-auto bg-white relative">
                    <div className="h-full">
                        <div className="sticky top-0 z-10 bg-white/80 backdrop-blur-md border-b border-gray-50 px-8 py-4 flex justify-between items-center">
                            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider">
                                {navItems.find(i => pathname.startsWith(i.href))?.label || "Console"}
                            </h2>
                            <div className="flex items-center gap-2">
                                <Link href="/" className="text-xs font-medium text-gray-400 hover:text-gray-900 hover:underline transition-colors flex items-center gap-1">
                                    Return to Market <ArrowUpRight className="w-3 h-3" />
                                </Link>
                            </div>
                        </div>
                        <div className="p-8 max-w-6xl mx-auto">
                            {children}
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}

// Add missing icon import
import { ArrowUpRight } from "lucide-react";
