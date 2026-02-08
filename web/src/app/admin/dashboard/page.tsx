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

interface SkillValidationSettings {
    profile: "lax" | "strict";
    enforce: boolean;
}

interface DashboardStats {
    skills_total: number;
    skills_public_total: number;
    skills_non_public_total: number;
    skills_url_null_total: number;
    skills_blob_any_depth_total: number;
    skills_nested_noncanonical_total: number;
    skills_repo_root_total: number;
    skills_other_total: number;
    raw_total: number;
    raw_pending: number;
    raw_processed: number;
    raw_error: number;
    raw_error_claude_spec: number;
    raw_error_quality: number;
    raw_processed_skill_md: number;
    raw_processed_skill_md_missing_spec: number;
}

interface WorkerStatus {
    phase: string;
    heartbeat_at?: string | null;
    loop_started_at?: string | null;
    loop_finished_at?: string | null;
    next_run_at?: string | null;
    auto_ingest_enabled?: boolean | null;
    interval_seconds?: number | null;
    last_ingested_raw_items?: number | null;
    last_pending_before?: number | null;
    last_pending_after?: number | null;
    last_processed_in_loop?: number | null;
    last_error_count_in_loop?: number | null;
    last_drained_in_loop?: number | null;
    last_error?: string | null;

    ingest_source_id?: string | null;
    ingest_source_type?: string | null;
    ingest_source_index?: number | null;
    ingest_source_total?: number | null;
    ingest_url?: string | null;
    ingest_directory_url?: string | null;
    ingest_repo_full_name?: string | null;
    ingest_discovered_repo_index?: number | null;
    ingest_discovered_repo_total?: number | null;
    ingest_discovered_repos?: number | null;
    ingest_last_source_error?: string | null;
    ingested_so_far?: number | null;
    ingest_results?: number | null;
    recent_events?: Array<Record<string, unknown>> | null;
}

export default function AdminDashboardPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [isSyncing, setIsSyncing] = useState(false);
    const [isSavingWorkerSettings, setIsSavingWorkerSettings] = useState(false);
    const [isReparsing, setIsReparsing] = useState(false);
    const [isReparsingAllMissingSpec, setIsReparsingAllMissingSpec] = useState(false);
    const [recentActivity, setRecentActivity] = useState<RawSkillListItem[]>([]);
    const [totalSkills, setTotalSkills] = useState(0);
    const [pendingCount, setPendingCount] = useState(0);
    const [flaggedCount, setFlaggedCount] = useState(0);
    const [crawlSources, setCrawlSources] = useState<CrawlSourceItem[]>([]);
    const [workerSettings, setWorkerSettings] = useState<WorkerSettings | null>(null);
    const [intervalDraft, setIntervalDraft] = useState("");
    const [skillValidationSettings, setSkillValidationSettings] = useState<SkillValidationSettings | null>(null);
    const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
    const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null);
    const [workerStatus, setWorkerStatus] = useState<WorkerStatus | null>(null);

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
            const workerResPromise: Promise<WorkerSettings | null> = api
                .get<WorkerSettings>("/admin/worker-settings", token)
                .catch((error) => {
                    // Backward compatible: older API builds won't have this endpoint yet.
                    if (error instanceof ApiError && error.status === 404) {
                        return null;
                    }
                    throw error;
                });

            const skillValidationPromise: Promise<SkillValidationSettings | null> = api
                .get<SkillValidationSettings>("/admin/skill-validation-settings", token)
                .catch((error) => {
                    if (error instanceof ApiError && error.status === 404) {
                        return null;
                    }
                    throw error;
                });

            const [skillsRes, pendingRes, recentRes, errorRes, sourceRes, workerRes, validationRes] = await Promise.all([
                api.get<{ total: number }>("/skills?page=1&size=1"),
                api.get<RawSkillListResponse>("/admin/raw-skills?status=pending&page=1&size=5", token),
                // status="" intentionally means "no filter" in the API (empty string is falsy server-side).
                api.get<RawSkillListResponse>("/admin/raw-skills?status=&page=1&size=5", token),
                api.get<RawSkillListResponse>("/admin/raw-skills?status=error&page=1&size=1", token),
                api.get<CrawlSourceItem[]>("/admin/crawl-sources", token),
                workerResPromise,
                skillValidationPromise,
            ]);

            const statsRes: DashboardStats | null = await api
                .get<DashboardStats>("/admin/dashboard-stats", token)
                .catch((error) => {
                    // Backward compatible: older API builds won't have this endpoint yet.
                    if (error instanceof ApiError && error.status === 404) {
                        return null;
                    }
                    throw error;
                });
            const workerStatusRes: WorkerStatus | null = await api
                .get<WorkerStatus>("/admin/worker-status", token)
                .catch((error) => {
                    if (error instanceof ApiError && error.status === 404) {
                        return null;
                    }
                    throw error;
                });

            if (statsRes) {
                setDashboardStats(statsRes);
                setTotalSkills(statsRes.skills_public_total ?? 0);
                setPendingCount(statsRes.raw_pending ?? (pendingRes.total ?? 0));
                setFlaggedCount(statsRes.raw_error ?? (errorRes.total ?? 0));
            } else {
                setDashboardStats(null);
                setTotalSkills(skillsRes.total ?? 0);
                setPendingCount(pendingRes.total ?? 0);
                setFlaggedCount(errorRes.total ?? 0);
            }
            setRecentActivity(recentRes.items || []);
            setCrawlSources(sourceRes || []);
            setWorkerSettings(workerRes || null);
            setWorkerStatus(workerStatusRes || null);
            if (showInitialLoading && workerRes) {
                setIntervalDraft(String(workerRes.auto_ingest_interval_seconds ?? 60));
            }
            setSkillValidationSettings(validationRes || null);
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
                setSkillValidationSettings(null);
                setDashboardStats(null);
                setWorkerStatus(null);
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

    const patchSkillValidationSettings = async (patch: Partial<SkillValidationSettings>) => {
        setIsSavingWorkerSettings(true);
        try {
            const token = getAdminToken() || undefined;
            if (!token) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            const updated = await api.patch<SkillValidationSettings>(
                "/admin/skill-validation-settings",
                patch,
                token,
            );
            setSkillValidationSettings(updated);
        } catch (error) {
            console.error("Failed to update skill validation settings", error);
            if (error instanceof ApiError && error.status === 401) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            alert("Failed to update skill validation settings.");
        } finally {
            setIsSavingWorkerSettings(false);
        }
    };

    const handleReparseRecent = async () => {
        setIsReparsing(true);
        try {
            const token = getAdminToken() || undefined;
            if (!token) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            const res = await api.post<{ updated: number }>("/admin/raw-skills/reparse?limit=100", {}, token);
            alert(`Queued ${res.updated} raw skills for re-parse. The worker will pick them up shortly.`);
            await fetchDashboardData(false);
        } catch (error) {
            console.error("Failed to queue reparse", error);
            if (error instanceof ApiError && error.status === 401) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            alert("Failed to queue reparse.");
        } finally {
            setIsReparsing(false);
        }
    };

    const handleReparseAllMissingSpec = async () => {
        setIsReparsingAllMissingSpec(true);
        try {
            const token = getAdminToken() || undefined;
            if (!token) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            const res = await api.post<{ updated: number }>(
                "/admin/raw-skills/reparse?limit=5000&only_skill_md=true&only_missing_claude_spec=true",
                {},
                token,
            );
            alert(`Queued ${res.updated} raw skills (missing claude_spec) for re-parse. The worker will pick them up shortly.`);
            await fetchDashboardData(false);
        } catch (error) {
            console.error("Failed to queue reparse (missing spec)", error);
            if (error instanceof ApiError && error.status === 401) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            alert("Failed to queue reparse.");
        } finally {
            setIsReparsingAllMissingSpec(false);
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
                        <h3 className="text-gray-500 font-medium">공개 스킬</h3>
                        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                            <CheckCircle className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">{totalSkills}</p>
                    {dashboardStats ? (
                        <p className="text-sm text-gray-500 mt-2">
                            DB 전체: <span className="font-mono">{dashboardStats.skills_total}</span>
                            {" "}/ 비공개(정책 제외): <span className="font-mono">{dashboardStats.skills_non_public_total}</span>
                        </p>
                    ) : (
                        <p className="text-sm text-green-600 mt-2 flex items-center gap-1">
                            <ArrowUpRight className="w-4 h-4" /> 카탈로그 동기화됨
                        </p>
                    )}
                    {dashboardStats && (
                        <p className="text-xs text-gray-500 mt-2">
                            제외 사유 예시: url 없음 <span className="font-mono">{dashboardStats.skills_url_null_total}</span>, repo root{" "}
                            <span className="font-mono">{dashboardStats.skills_repo_root_total}</span>, nested/non-canonical{" "}
                            <span className="font-mono">{dashboardStats.skills_nested_noncanonical_total}</span>, 기타{" "}
                            <span className="font-mono">{dashboardStats.skills_other_total}</span>
                        </p>
                    )}
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 font-medium">파싱 대기</h3>
                        <div className="p-2 bg-yellow-50 text-yellow-600 rounded-lg">
                            <Clock className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">{pendingCount}</p>
                    <p className="text-sm text-gray-500 mt-2">
                        워커가 아직 처리하지 않은 raw SKILL.md (큐)
                    </p>
                    <div className="mt-4">
                        <Link href="/admin/skills?status=pending" className="block w-full text-center px-4 py-2 bg-gray-50 text-gray-900 rounded-lg hover:bg-gray-100 transition-colors text-sm font-medium">
                            파싱 대기 목록 보기
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
                    {dashboardStats ? (
                        <p className="text-sm text-gray-500 mt-2">
                            claude_spec: <span className="font-mono">{dashboardStats.raw_error_claude_spec}</span>{" "}
                            / quality: <span className="font-mono">{dashboardStats.raw_error_quality}</span>
                        </p>
                    ) : (
                        <p className="text-sm text-gray-500 mt-2">품질 알림</p>
                    )}
                    <div className="mt-4">
                        <Link href="/admin/quality" className="block w-full text-center px-4 py-2 bg-gray-50 text-gray-900 rounded-lg hover:bg-gray-100 transition-colors text-sm font-medium">
                            문제 검토
                        </Link>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm md:col-span-3">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        <div>
                            <h3 className="text-gray-900 font-bold">워커 상태</h3>
                            <p className="text-sm text-gray-500 mt-1">
                                워커가 매 루프마다 DB에 기록하는 heartbeat로, 현재 무엇을 하고 있는지 확인할 수 있습니다.
                            </p>
                        </div>

                        {workerStatus ? (
                            <div className="flex items-center gap-3 flex-wrap text-sm">
                                <span className="text-gray-500">
                                    phase: <span className="font-mono text-gray-900">{workerStatus.phase ?? "unknown"}</span>
                                </span>
                                {typeof workerStatus.ingest_source_index === "number" &&
                                    typeof workerStatus.ingest_source_total === "number" &&
                                    workerStatus.ingest_source_id && (
                                        <span className="text-gray-500">
                                            source:{" "}
                                            <span className="font-mono text-gray-900">
                                                {workerStatus.ingest_source_index}/{workerStatus.ingest_source_total}
                                            </span>{" "}
                                            <span className="font-mono text-gray-900">{workerStatus.ingest_source_id}</span>
                                        </span>
                                    )}
                                {workerStatus.ingest_repo_full_name && (
                                    <span className="text-gray-500">
                                        repo: <span className="font-mono text-gray-900">{workerStatus.ingest_repo_full_name}</span>
                                    </span>
                                )}
                                {typeof workerStatus.interval_seconds === "number" && (
                                    <span className="text-gray-500">
                                        interval: <span className="font-mono text-gray-900">{workerStatus.interval_seconds}s</span>
                                    </span>
                                )}
                                {(workerStatus.ingest_last_source_error || workerStatus.last_error) && (
                                    <span className="text-red-700">
                                        last_error:{" "}
                                        <span className="font-mono">
                                            {workerStatus.ingest_last_source_error ?? workerStatus.last_error}
                                        </span>
                                    </span>
                                )}
                            </div>
                        ) : (
                            <div className="text-sm text-gray-500">
                                이 API 빌드에는 <span className="font-mono">/admin/worker-status</span> 엔드포인트가 없어
                                상태를 표시할 수 없습니다. (API 컨테이너/서버를 최신 코드로 재시작하세요.)
                            </div>
                        )}
                    </div>

                    {workerStatus && (
                        <div className="mt-4 text-sm text-gray-600 flex flex-wrap gap-x-6 gap-y-2">
                            {workerStatus.heartbeat_at && (
                                <span>
                                    heartbeat: <span className="font-mono">{workerStatus.heartbeat_at}</span>
                                </span>
                            )}
                            {workerStatus.loop_started_at && (
                                <span>
                                    loop_start: <span className="font-mono">{workerStatus.loop_started_at}</span>
                                </span>
                            )}
                            {workerStatus.next_run_at && (
                                <span>
                                    next_run: <span className="font-mono">{workerStatus.next_run_at}</span>
                                </span>
                            )}
                            {typeof workerStatus.last_ingested_raw_items === "number" && (
                                <span>
                                    last_ingested: <span className="font-mono">{workerStatus.last_ingested_raw_items}</span>
                                </span>
                            )}
                            {typeof workerStatus.last_pending_before === "number" &&
                                typeof workerStatus.last_pending_after === "number" && (
                                    <span>
                                        pending: <span className="font-mono">{workerStatus.last_pending_before}</span> →{" "}
                                        <span className="font-mono">{workerStatus.last_pending_after}</span>
                                    </span>
                                )}
                            {typeof workerStatus.last_drained_in_loop === "number" && (
                                <span>
                                    drained_in_loop: <span className="font-mono">{workerStatus.last_drained_in_loop}</span>
                                </span>
                            )}
                            {typeof workerStatus.last_processed_in_loop === "number" && (
                                <span>
                                    processed_in_loop: <span className="font-mono">{workerStatus.last_processed_in_loop}</span>
                                </span>
                            )}
                            {typeof workerStatus.last_error_count_in_loop === "number" && (
                                <span>
                                    errors_in_loop: <span className="font-mono">{workerStatus.last_error_count_in_loop}</span>
                                </span>
                            )}
                        </div>
                    )}

                    {workerStatus?.recent_events && workerStatus.recent_events.length > 0 && (
                        <div className="mt-4">
                            <div className="text-sm font-medium text-gray-700 mb-2">최근 이벤트</div>
                            <ul className="divide-y divide-gray-100 border border-gray-100 rounded-lg overflow-hidden">
                                {workerStatus.recent_events
                                    .slice(-8)
                                    .reverse()
                                    .map((ev, idx) => {
                                        const at = typeof ev.at === "string" ? ev.at : "";
                                        const phase = typeof ev.phase === "string" ? ev.phase : "unknown";
                                        const sourceId = typeof ev.ingest_source_id === "string" ? ev.ingest_source_id : "";
                                        const repo = typeof ev.ingest_repo_full_name === "string" ? ev.ingest_repo_full_name : "";
                                        const err = typeof ev.ingest_last_source_error === "string" ? ev.ingest_last_source_error : (typeof ev.last_error === "string" ? ev.last_error : "");
                                        return (
                                            <li key={`${idx}-${at}-${phase}`} className="px-3 py-2 text-xs text-gray-600">
                                                <span className="font-mono text-gray-500">{at}</span>{" "}
                                                <span className="font-mono text-gray-900">{phase}</span>
                                                {sourceId && (
                                                    <>
                                                        {" "}
                                                        <span className="text-gray-400">|</span>{" "}
                                                        <span className="font-mono">{sourceId}</span>
                                                    </>
                                                )}
                                                {repo && (
                                                    <>
                                                        {" "}
                                                        <span className="text-gray-400">|</span>{" "}
                                                        <span className="font-mono">{repo}</span>
                                                    </>
                                                )}
                                                {err && (
                                                    <>
                                                        {" "}
                                                        <span className="text-gray-400">|</span>{" "}
                                                        <span className="text-red-700 font-mono">{err}</span>
                                                    </>
                                                )}
                                            </li>
                                        );
                                    })}
                            </ul>
                        </div>
                    )}
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm md:col-span-3">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        <div>
                            <h3 className="text-gray-900 font-bold">워커 자동 크롤링</h3>
                            <p className="text-sm text-gray-500 mt-1">
                                워커 컨테이너는 계속 실행되지만, 여기서 수집(ingest)을 끌 수 있습니다. 변경은 다음 루프부터 반영됩니다.
                            </p>
                        </div>

                        {workerSettings ? (
                            <div className="flex items-center gap-3">
                                <span className="text-sm text-gray-500">
                                    상태:{" "}
                                    <span
                                        className={`font-bold ${workerSettings.auto_ingest_enabled ? "text-emerald-600" : "text-gray-700"}`}
                                    >
                                        {workerSettings.auto_ingest_enabled ? "ON" : "OFF"}
                                    </span>
                                </span>
                                <button
                                    onClick={() =>
                                        patchWorkerSettings({
                                            auto_ingest_enabled: !workerSettings.auto_ingest_enabled,
                                        })
                                    }
                                    disabled={isSavingWorkerSettings}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors disabled:opacity-50 ${
                                        workerSettings.auto_ingest_enabled
                                            ? "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100"
                                            : "bg-gray-50 text-gray-800 border-gray-200 hover:bg-gray-100"
                                    }`}
                                >
                                    {isSavingWorkerSettings ? "저장 중..." : workerSettings.auto_ingest_enabled ? "끄기" : "켜기"}
                                </button>
                            </div>
                        ) : (
                            <div className="text-sm text-gray-500">
                                이 API 빌드에는 <span className="font-mono">/admin/worker-settings</span> 엔드포인트가 없어
                                토글을 표시할 수 없습니다. (API 컨테이너/서버를 최신 코드로 재시작하세요.)
                            </div>
                        )}
                    </div>

                    {workerSettings && (
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
                    )}
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm md:col-span-3">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                        <div>
                            <h3 className="text-gray-900 font-bold">SKILL.md 스펙 검증</h3>
                            <p className="text-sm text-gray-500 mt-1">
                                <span className="font-mono">lax</span>는 관측 위주, <span className="font-mono">strict</span>는 더 엄격합니다.
                                <span className="font-mono">enforce</span>를 켜면 실패한 스킬은 ingest에서 <span className="font-mono">error</span>로 떨어집니다.
                            </p>
                        </div>

                        {skillValidationSettings ? (
                            <div className="flex items-center gap-3 flex-wrap">
                                <span className="text-sm text-gray-500">
                                    profile: <span className="font-bold text-gray-900">{skillValidationSettings.profile}</span>
                                </span>
                                <select
                                    value={skillValidationSettings.profile}
                                    onChange={(e) => {
                                        const v = e.target.value === "strict" ? "strict" : "lax";
                                        patchSkillValidationSettings({ profile: v });
                                    }}
                                    disabled={isSavingWorkerSettings}
                                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white"
                                >
                                    <option value="lax">lax</option>
                                    <option value="strict">strict</option>
                                </select>
                                <button
                                    onClick={() =>
                                        patchSkillValidationSettings({ enforce: !skillValidationSettings.enforce })
                                    }
                                    disabled={isSavingWorkerSettings}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium border transition-colors disabled:opacity-50 ${
                                        skillValidationSettings.enforce
                                            ? "bg-red-50 text-red-700 border-red-200 hover:bg-red-100"
                                            : "bg-gray-50 text-gray-800 border-gray-200 hover:bg-gray-100"
                                    }`}
                                >
                                    enforce: {skillValidationSettings.enforce ? "ON" : "OFF"}
                                </button>
                                <button
                                    onClick={handleReparseRecent}
                                    disabled={isReparsing || isSavingWorkerSettings}
                                    className="px-4 py-2 rounded-lg text-sm font-medium border border-gray-200 bg-white hover:bg-gray-50 disabled:opacity-50 transition-colors"
                                    title="Older RawSkills may not be re-validated unless content changed. This queues a bounded re-parse."
                                >
                                    {isReparsing ? "재파싱 큐잉..." : "최근 100개 재파싱"}
                                </button>
                                {dashboardStats && (
                                    <button
                                        onClick={handleReparseAllMissingSpec}
                                        disabled={isReparsingAllMissingSpec || isSavingWorkerSettings}
                                        className="px-4 py-2 rounded-lg text-sm font-medium border border-gray-200 bg-white hover:bg-gray-50 disabled:opacity-50 transition-colors"
                                        title="Queue a re-parse for processed SKILL.md rows that don't have claude_spec yet."
                                    >
                                        {isReparsingAllMissingSpec
                                            ? "누락 재파싱..."
                                            : `누락 ${dashboardStats.raw_processed_skill_md_missing_spec}개 재파싱`}
                                    </button>
                                )}
                            </div>
                        ) : (
                            <div className="text-sm text-gray-500">
                                이 API 빌드에는 <span className="font-mono">/admin/skill-validation-settings</span> 엔드포인트가 없어
                                설정을 표시할 수 없습니다.
                            </div>
                        )}
                    </div>

                    {dashboardStats && (
                        <div className="mt-4 text-sm text-gray-600 flex flex-wrap gap-x-6 gap-y-2">
                            <span>
                                SKILL.md 처리됨: <span className="font-mono">{dashboardStats.raw_processed_skill_md}</span>
                            </span>
                            <span>
                                spec 누락: <span className="font-mono">{dashboardStats.raw_processed_skill_md_missing_spec}</span>
                            </span>
                            <span>
                                Raw 전체: <span className="font-mono">{dashboardStats.raw_total}</span>
                            </span>
                            <span>
                                pending: <span className="font-mono">{dashboardStats.raw_pending}</span>
                            </span>
                        </div>
                    )}
                </div>
            </div>

            {/* Recent Activity Section */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="font-bold text-gray-900">최근 Raw Skills</h3>
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
                                    <Link
                                        href={`/admin/skills?status=${encodeURIComponent(item.status)}&focus=${encodeURIComponent(item.id)}`}
                                        className="text-sm font-medium text-blue-600 hover:text-blue-500"
                                    >
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
