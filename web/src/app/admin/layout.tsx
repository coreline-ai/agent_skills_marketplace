"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, List, ShieldCheck, LogOut } from "lucide-react";
import { api, ApiError } from "@/app/lib/api";
import { clearAdminSession, getAdminToken } from "@/app/lib/admin-auth";

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
        { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
        { href: "/admin/skills", label: "Manage Skills", icon: List },
        { href: "/admin/quality", label: "Quality Control", icon: ShieldCheck },
    ];

    const handleSignOut = () => {
        clearAdminSession();
        router.replace("/admin/login");
    };

    return (
        <div className="min-h-screen bg-gray-100 flex">
            {/* Sidebar */}
            <aside className="w-64 bg-white border-r border-gray-200">
                <div className="p-6 border-b border-gray-200">
                    <Link href="/" className="font-bold text-xl text-blue-600">
                        Agent Skills
                    </Link>
                    <p className="text-xs text-gray-500 mt-1">Admin Console</p>
                </div>
                <nav className="p-4 space-y-2">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = pathname.startsWith(item.href);
                        return (
                            <Link
                                key={item.href}
                                href={item.href}
                                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${isActive
                                        ? "bg-blue-50 text-blue-700"
                                        : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                                    }`}
                            >
                                <Icon className="w-5 h-5" />
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>
                <div className="absolute bottom-0 w-64 p-4 border-t border-gray-200">
                    <button
                        type="button"
                        onClick={handleSignOut}
                        className="flex items-center gap-3 px-4 py-3 w-full text-left text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                        <LogOut className="w-5 h-5" />
                        Sign Out
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-y-auto">
                <div className="p-8">
                    {children}
                </div>
            </main>
        </div>
    );
}
