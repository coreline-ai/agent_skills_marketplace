"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Compass, BarChart2, FolderKanban, ShieldCheck, Settings, ChevronDown, BookOpen } from "lucide-react";
import { ThemeToggle } from "@/components/ThemeToggle";

export function Sidebar() {
    const pathname = usePathname();

    // Hide sidebar on admin pages (admin has its own layout)
    if (pathname?.startsWith("/admin")) return null;

    const navSections = [
        {
            title: "Platform",
            items: [
                { name: "Home", href: "/", icon: Home },
                { name: "Skills Library", href: "/skills", icon: Compass },
                { name: "Rankings", href: "/rankings", icon: BarChart2 },
                { name: "User Guide", href: "/guide", icon: BookOpen },
            ]
        },
        {
            title: "Management",
            items: [
                { name: "Admin", href: "/admin", icon: ShieldCheck },
                { name: "Settings", href: "/settings", icon: Settings },
            ]
        }
    ];

    return (
        <aside className="bg-sidebar border-r border-border min-h-full flex flex-col flex-shrink-0 w-[280px] hidden md:flex transition-all duration-300" data-purpose="sidebar">
            <div className="h-20 flex items-center px-6 border-b border-sidebar">
                <Link href="/" className="flex items-center gap-3">
                    <img
                        src="/coreline_logo.png"
                        alt="Coreline AI Logo"
                        className="w-8 h-8 rounded-xl shadow-sm"
                    />
                    <span className="text-xl font-bold tracking-tight text-gray-900">
                        CORELINE <span className="text-accent">AI</span>
                    </span>
                </Link>
            </div>

            <nav className="flex-1 px-4 py-6 overflow-y-auto space-y-8">
                {navSections.map((section) => (
                    <div key={section.title} data-purpose="nav-section">
                        <h3 className="px-2 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                            {section.title}
                        </h3>
                        <ul className="space-y-1">
                            {section.items.map((item) => {
                                const Icon = item.icon;
                                const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
                                return (
                                    <li key={item.name}>
                                        <Link
                                            href={item.href}
                                            className={`flex items-center gap-3 px-3 py-2.5 rounded-[8px] transition-all group ${isActive
                                                ? "bg-white text-gray-900 shadow-sm border border-gray-100"
                                                : "text-gray-600 hover:text-gray-900 hover:bg-white/60 hover:shadow-sm"
                                                }`}
                                        >
                                            <Icon className={`w-5 h-5 ${isActive ? "text-accent" : "text-gray-400 group-hover:text-accent"} transition-colors text-center`} />
                                            <span className="text-sm font-medium">{item.name}</span>
                                        </Link>
                                    </li>
                                );
                            })}
                        </ul>
                    </div>
                ))}
            </nav>

            <div className="p-4 pb-8 mt-auto space-y-4">
                {/* Separator */}
                <div className="h-px bg-gray-200 mx-2"></div>

                <div className="flex justify-between items-center px-2">
                    <span className="text-sm text-gray-500 font-medium">Dark Mode</span>
                    <div className="scale-90 origin-right">
                        <ThemeToggle />
                    </div>
                </div>

                <div className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-white/60 cursor-pointer transition-colors group">
                    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold shadow-sm">
                        CA
                    </div>
                    <div className="flex-1 min-w-0">
                        <p className="text-sm font-bold text-gray-900 truncate">Coreline AI</p>
                        <p className="text-xs text-gray-500 truncate font-medium">corelineailab@gmail.com</p>
                    </div>
                    <ChevronDown className="w-4 h-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
                </div>
            </div>
        </aside>
    );
}
