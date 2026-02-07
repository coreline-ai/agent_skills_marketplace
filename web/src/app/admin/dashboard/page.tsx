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
    source_type: "github_repo" | "web_directory" | "github_search";
    repo_full_name: string | null;
    url: string;
    policy?: {
        min_repo_type?: string;
        max_repos?: number;
        max_sitemap_pages?: number;
        max_pages?: number;
        query_count?: number;
        search_mode?: string;
        require_token?: boolean;
        allowed_path_globs?: string[];
    };
}

interface WorkerSettings {
    auto_ingest_enabled: boolean;
    auto_ingest_interval_seconds: number;
}

export default function AdminDashboardPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [isSyncing, setIsSyncing] = useState(false);
    const [isSavingWorkerSettings, setIsSavingWorkerSettings] = useState(false);
    const [recentActivity, setRecentActivity] = useState<RawSkillListItem[]>([]);
    const [totalSkills, setTotalSkills] = useState(0);
    const [pendingCount, setPendingCount] = useState(0);
    const [flaggedCount, setFlaggedCount] = useState(0);
    const [crawlSources, setCrawlSources] = useState<CrawlSourceItem[]>([]);
    const [workerSettings, setWorkerSettings] = useState<WorkerSettings | null>(null);
    const [intervalDraft, setIntervalDraft] = useState("");
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
            const [skillsRes, pendingRes, errorRes, sourceRes, workerRes] = await Promise.all([
                api.get<{ total: number }>("/skills?page=1&size=1"),
                api.get<RawSkillListResponse>("/admin/raw-skills?status=pending&page=1&size=5", token),
                api.get<RawSkillListResponse>("/admin/raw-skills?status=error&page=1&size=1", token),
                api.get<CrawlSourceItem[]>("/admin/crawl-sources", token),
                api.get<WorkerSettings>("/admin/worker-settings", token),
            ]);

            setTotalSkills(skillsRes.total ?? 0);
            setRecentActivity(pendingRes.items || []);
            setPendingCount(pendingRes.total ?? 0);
            setFlaggedCount(errorRes.total ?? 0);
            setCrawlSources(sourceRes || []);
            setWorkerSettings(workerRes || null);
            if (showInitialLoading && workerRes) {
                setIntervalDraft(String(workerRes.auto_ingest_interval_seconds ?? 60));
            }
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
                setWorkerSettings(null);
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

    const patchWorkerSettings = async (patch: Partial<WorkerSettings>) => {
        setIsSavingWorkerSettings(true);
        try {
            const token = getAdminToken() || undefined;
            if (!token) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            const updated = await api.patch<WorkerSettings>("/admin/worker-settings", patch, token);
            setWorkerSettings(updated);
            if (typeof updated.auto_ingest_interval_seconds === "number") {
                setIntervalDraft(String(updated.auto_ingest_interval_seconds));
            }
        } catch (error) {
            console.error("Failed to update worker settings", error);
            if (error instanceof ApiError && error.status === 401) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            alert("Failed to update worker settings. (If this is a fresh DB, run alembic migrations.)");
        } finally {
            setIsSavingWorkerSettings(false);
        }
    };

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
                <h1 className="text-2xl font-bold text-gray-900">대시보드 개요</h1>
                <div className="flex items-center gap-3">
                    {lastUpdatedAt && (
                        <span className="text-xs text-gray-500">
                            업데이트: {lastUpdatedAt.toLocaleTimeString()}
                        </span>
                    )}
                    <button
                        onClick={handleSync}
                        disabled={isSyncing}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors text-sm font-medium"
                    >
                        <RefreshCw className={`w-4 h-4 ${isSyncing ? "animate-spin" : ""}`} />
                        {isSyncing ? "동기화 중..." : "소스 동기화"}
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 font-medium">전체 스킬</h3>
                        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                            <CheckCircle className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">{totalSkills}</p>
                    <p className="text-sm text-green-600 mt-2 flex items-center gap-1">
                        <ArrowUpRight className="w-4 h-4" /> 카탈로그 동기화됨
                    </p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 font-medium">검토 대기</h3>
                        <div className="p-2 bg-yellow-50 text-yellow-600 rounded-lg">
                            <Clock className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">{pendingCount}</p>
                    <p className="text-sm text-gray-500 mt-2">
                        검토 필요 항목
                    </p>
                    <div className="mt-4">
                        <Link href="/admin/skills?status=pending" className="block w-full text-center px-4 py-2 bg-gray-50 text-gray-900 rounded-lg hover:bg-gray-100 transition-colors text-sm font-medium">
                            대기 목록 보기
                        </Link>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 font-medium">문제 신고</h3>
                        <div className="p-2 bg-red-50 text-red-600 rounded-lg">
                            <AlertCircle className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">{flaggedCount}</p>
                    <p className="text-sm text-gray-500 mt-2">
                        품질 알림
                    </p>
                    <div className="mt-4">
                        <Link href="/admin/quality" className="block w-full text-center px-4 py-2 bg-gray-50 text-gray-900 rounded-lg hover:bg-gray-100 transition-colors text-sm font-medium">
                            문제 검토
                        </Link>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm md:col-span-3">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        <div>
                            <h3 className="text-gray-900 font-bold">워커 자동 크롤링</h3>
                            <p className="text-sm text-gray-500 mt-1">
                                워커 컨테이너는 계속 실행되지만, 여기서 수집(ingest)을 끌 수 있습니다. 변경은 다음 루프부터 반영됩니다.
                            </p>
                        </div>

                        <div className="flex items-center gap-3">
                            <span className="text-sm text-gray-500">
                                상태:{" "}
                                <span
                                    className={`font-bold ${workerSettings?.auto_ingest_enabled ? "text-emerald-600" : "text-gray-700"}`}
                                >
                                    {workerSettings?.auto_ingest_enabled ? "ON" : "OFF"}
                                </span>
                            </span>
                            <button
                                onClick={() =>
                                    patchWorkerSettings({
                                        auto_ingest_enabled: !(workerSettings?.auto_ingest_enabled ?? true),
                                    })
                                }
                                disabled={isSavingWorkerSettings}
                                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors disabled:opacity-50 ${
                                    workerSettings?.auto_ingest_enabled
                                        ? "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"
                                        : "bg-gray-50 text-gray-800 border-gray-200 hover:bg-gray-100"
                                }`}
                            >
                                {isSavingWorkerSettings ? "저장 중..." : workerSettings?.auto_ingest_enabled ? "끄기" : "켜기"}
                            </button>
                        </div>
                    </div>

                    <div className="mt-5 flex flex-col md:flex-row md:items-center gap-3">
                        <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                            루프 간격 (초)
                        </label>
                        <input
                            type="number"
                            min={10}
                            max={86400}
                            value={intervalDraft}
                            onChange={(e) => setIntervalDraft(e.target.value)}
                            className="w-full md:w-48 px-3 py-2 border border-gray-200 rounded-lg text-sm"
                            placeholder="60"
                        />
                        <button
                            onClick={() => {
                                const parsed = Number.parseInt(intervalDraft, 10);
                                if (!Number.isFinite(parsed) || parsed < 10 || parsed > 86400) {
                                    alert("Interval must be between 10 and 86400 seconds.");
                                    return;
                                }
                                patchWorkerSettings({ auto_ingest_interval_seconds: parsed });
                            }}
                            disabled={isSavingWorkerSettings}
                            className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors text-sm font-medium"
                        >
                            간격 저장
                        </button>
                    </div>
                </div>
            </div>

            {/* Recent Activity Section */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="font-bold text-gray-900">최근 수집된 Raw Skills</h3>
                </div>
                <div className="p-0">
                    {loading ? (
                        <div className="p-6 text-center text-gray-500">최근 활동 불러오는 중...</div>
                    ) : recentActivity.length > 0 ? (
                        <ul className="divide-y divide-gray-100">
                            {recentActivity.map((item) => (
                                <li key={item.id} className="px-6 py-4 hover:bg-gray-50 flex justify-between items-center">
                                    <div>
                                        <p className="text-sm font-medium text-gray-900 truncate max-w-lg">{item.source_url}</p>
                                        <p className="text-xs text-gray-500 mt-1 capitalize">{item.status}</p>
                                    </div>
                                    <Link href={`/admin/skills?focus=${item.id}`} className="text-sm font-medium text-blue-600 hover:text-blue-500">
                                        검토하기
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <div className="p-6 text-center text-gray-500">최근 활동이 없습니다.</div>
                    )}
                </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                    <h3 className="font-bold text-gray-900">크롤링 소스</h3>
                    <span className="text-xs text-gray-500">{crawlSources.length}개 소스</span>
                </div>
                <div className="p-0">
                    {loading ? (
                        <div className="p-6 text-center text-gray-500">소스 불러오는 중...</div>
                    ) : crawlSources.length > 0 ? (
                        <ul className="divide-y divide-gray-100">
                            {crawlSources.map((source) => (
                                <li key={source.id} className="px-6 py-4 hover:bg-gray-50">
                                    <div className="flex flex-col gap-2">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium text-gray-900 truncate">
                                                {source.repo_full_name ?? source.url.replace(/^https?:\/\//, "")}
                                            </span>
                                            <a
                                                href={source.url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                title={source.url}
                                                className="text-gray-400 hover:text-blue-600 transition-colors"
                                            >
                                                <ExternalLink className="w-4 h-4" />
                                            </a>
                                        </div>
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <span className="inline-flex items-center px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[11px] font-medium">
                                                {source.source_type}
                                            </span>
                                            <span className="text-[11px] text-gray-500 whitespace-nowrap">
                                                {`min:${source.policy?.min_repo_type ?? "-"}`}
                                            </span>
                                            {typeof source.policy?.query_count === "number" && (
                                                <span className="text-[11px] text-gray-500 whitespace-nowrap">
                                                    {`queries:${source.policy.query_count}`}
                                                </span>
                                            )}
                                            {typeof source.policy?.require_token === "boolean" && (
                                                <span className="text-[11px] text-gray-500 whitespace-nowrap">
                                                    {source.policy.require_token ? "token:required" : "token:optional"}
                                                </span>
                                            )}
                                        </div>
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
