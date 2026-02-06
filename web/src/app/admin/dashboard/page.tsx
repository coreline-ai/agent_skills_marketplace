"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/app/lib/api";
import Link from "next/link";
import { ArrowUpRight, CheckCircle, Clock, AlertCircle, RefreshCw, ExternalLink } from "lucide-react";
import { clearAdminSession, getAdminToken } from "@/app/lib/admin-auth";

interface RawSkillListItem {
    id: string;
    source_url: string | null;
    external_id?: string | null;
    status: string;
    parse_error?: Record<string, unknown> | null;
    created_at?: string;
}

interface RawSkillListResponse {
    items: RawSkillListItem[];
    total: number;
}

interface CrawlSourceItem {
    id: string;
    repo_full_name: string;
    url: string;
}

export default function AdminDashboardPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [isSyncing, setIsSyncing] = useState(false);
    const [recentActivity, setRecentActivity] = useState<RawSkillListItem[]>([]);
    const [totalSkills, setTotalSkills] = useState(0);
    const [pendingCount, setPendingCount] = useState(0);
    const [flaggedCount, setFlaggedCount] = useState(0);
    const [crawlSources, setCrawlSources] = useState<CrawlSourceItem[]>([]);
    const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);

    const fetchDashboardData = useCallback(async (showInitialLoading: boolean = false) => {
        if (showInitialLoading) {
            setLoading(true);
        }
        try {
            const token = getAdminToken() || undefined;
            if (!token) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            const [skillsRes, pendingRes, errorRes, sourceRes] = await Promise.all([
                api.get<{ total: number }>("/skills?page=1&size=1"),
                api.get<RawSkillListResponse>("/admin/raw-skills?status=pending&page=1&size=5", token),
                api.get<RawSkillListResponse>("/admin/raw-skills?status=error&page=1&size=1", token),
                api.get<CrawlSourceItem[]>("/admin/crawl-sources", token),
            ]);

            setTotalSkills(skillsRes.total ?? 0);
            setRecentActivity(pendingRes.items || []);
            setPendingCount(pendingRes.total ?? 0);
            setFlaggedCount(errorRes.total ?? 0);
            setCrawlSources(sourceRes || []);
            setLastUpdatedAt(new Date());
        } catch (error) {
            console.error("Failed to fetch dashboard data", error);
            if (error instanceof ApiError && error.status === 401) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            if (showInitialLoading) {
                setRecentActivity([]);
                setTotalSkills(0);
                setPendingCount(0);
                setFlaggedCount(0);
                setCrawlSources([]);
            }
        } finally {
            if (showInitialLoading) {
                setLoading(false);
            }
        }
    }, [router]);

    useEffect(() => {
        fetchDashboardData(true);

        const intervalId = window.setInterval(() => {
            fetchDashboardData(false);
        }, 10000);

        const onVisibilityChange = () => {
            if (document.visibilityState === "visible") {
                fetchDashboardData(false);
            }
        };
        document.addEventListener("visibilitychange", onVisibilityChange);

        return () => {
            window.clearInterval(intervalId);
            document.removeEventListener("visibilitychange", onVisibilityChange);
        };
    }, [fetchDashboardData]);

    const handleSync = async () => {
        setIsSyncing(true);
        try {
            const token = getAdminToken() || undefined;
            if (!token) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            await api.post("/admin/ingest", {}, token);
            alert("Ingestion started in background.");
            // Refresh summary numbers right after sync trigger.
            await fetchDashboardData(false);
        } catch (error) {
            console.error("Failed to trigger sync", error);
            if (error instanceof ApiError && error.status === 401) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            alert("Failed to start ingestion.");
        } finally {
            setIsSyncing(false);
        }
    };

    return (
        <div className="space-y-8">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
                <div className="flex items-center gap-3">
                    {lastUpdatedAt && (
                        <span className="text-xs text-gray-500">
                            Updated: {lastUpdatedAt.toLocaleTimeString()}
                        </span>
                    )}
                    <button
                        onClick={handleSync}
                        disabled={isSyncing}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`} />
                        {isSyncing ? "Syncing..." : "Sync Sources"}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 font-medium">Total Skills</h3>
                        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                            <CheckCircle className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">{totalSkills}</p>
                    <p className="text-sm text-green-600 mt-2 flex items-center gap-1">
                        <ArrowUpRight className="w-4 h-4" /> Synced from catalog
                    </p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 font-medium">Pending Review</h3>
                        <div className="p-2 bg-yellow-50 text-yellow-600 rounded-lg">
                            <Clock className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">{pendingCount}</p>
                    <p className="text-sm text-gray-500 mt-2">
                        Needs attention
                    </p>
                    <div className="mt-4">
                        <Link href="/admin/skills?status=pending" className="text-sm text-blue-600 hover:underline">
                            View all pending
                        </Link>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 font-medium">Flagged Issues</h3>
                        <div className="p-2 bg-red-50 text-red-600 rounded-lg">
                            <AlertCircle className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">{flaggedCount}</p>
                    <p className="text-sm text-gray-500 mt-2">
                        Quality alerts
                    </p>
                    <div className="mt-4">
                        <Link href="/admin/quality" className="text-sm text-blue-600 hover:underline">
                            Review issues
                        </Link>
                    </div>
                </div>
            </div>

            {/* Recent Activity Section */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="font-bold text-gray-900">Recent Raw Skills Ingested</h3>
                </div>
                <div className="p-0">
                    {loading ? (
                        <div className="p-6 text-center text-gray-500">Loading recent activity...</div>
                    ) : recentActivity.length > 0 ? (
                        <ul className="divide-y divide-gray-100">
                            {recentActivity.map((item) => (
                                <li key={item.id} className="px-6 py-4 hover:bg-gray-50 flex justify-between items-center">
                                    <div>
                                        <p className="text-sm font-medium text-gray-900 truncate max-w-lg">{item.source_url}</p>
                                        <p className="text-xs text-gray-500 mt-1 capitalize">{item.status}</p>
                                    </div>
                                    <Link href={`/admin/skills?focus=${item.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-500">
                                        Review
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <div className="p-6 text-center text-gray-500">No recent activity.</div>
                    )}
                </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                    <h3 className="font-bold text-gray-900">GitHub Crawl Sources</h3>
                    <span className="text-xs text-gray-500">{crawlSources.length} repos</span>
                </div>
                <div className="p-0">
                    {loading ? (
                        <div className="p-6 text-center text-gray-500">Loading sources...</div>
                    ) : crawlSources.length > 0 ? (
                        <ul className="divide-y divide-gray-100">
                            {crawlSources.map((source) => (
                                <li key={source.id} className="px-6 py-4 hover:bg-gray-50">
                                    <div className="flex items-center justify-between gap-4">
                                        <div className="min-w-0 flex items-center gap-2">
                                            <span className="inline-flex items-center px-2.5 py-1 rounded-md bg-gray-100 text-gray-700 text-xs font-mono">
                                                {source.repo_full_name}
                                            </span>
                                            <span className="text-[11px] text-gray-400 whitespace-nowrap">SKILL.md source</span>
                                        </div>
                                        <a
                                            href={source.url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            title={source.url}
                                            className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:underline whitespace-nowrap"
                                        >
                                            {`github.com/${source.repo_full_name}`}
                                            <ExternalLink className="w-4 h-4" />
                                        </a>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <div className="p-6 text-center text-gray-500">No crawl sources configured.</div>
                    )}
                </div>
            </div>
        </div>
    );
}
