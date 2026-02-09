"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/app/lib/api";
import { clearAdminSession, getAdminToken } from "@/app/lib/admin-auth";
import { ExternalLink, RefreshCw } from "lucide-react";
import { PluginsCrawlTrigger } from "@/components/PluginsCrawlTrigger";

interface CrawlSourceItem {
    id: string;
    source_type: "github_repo" | "web_directory" | "github_search" | "markdown_list";
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
        repo_scan_enabled?: boolean;
    };
}

export default function AdminCrawlingPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [crawlSources, setCrawlSources] = useState<CrawlSourceItem[]>([]);
    const [isTriggering, setIsTriggering] = useState(false);
    const [selectedSourceId, setSelectedSourceId] = useState<string>("");

    const claudeCandidates = useMemo(() => {
        const items = crawlSources.filter((s) => {
            const id = (s.id || "").toLowerCase();
            const url = (s.url || "").toLowerCase();
            const repo = (s.repo_full_name || "").toLowerCase();
            return id.includes("claude") || url.includes("claude") || repo.includes("claude") || id.includes("anthropic");
        });
        return items;
    }, [crawlSources]);

    useEffect(() => {
        if (!selectedSourceId && claudeCandidates.length > 0) {
            const preferred =
                claudeCandidates.find((s) => s.id === "claude-code-marketplace-directory") ??
                claudeCandidates.find((s) => s.id.includes("claude-code") && s.id.includes("marketplace")) ??
                claudeCandidates[0];
            setSelectedSourceId(preferred.id);
        }
    }, [claudeCandidates, selectedSourceId]);

    const fetchSources = useCallback(async () => {
        setLoading(true);
        try {
            const token = getAdminToken() || undefined;
            if (!token) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            const items = await api.get<CrawlSourceItem[]>("/admin/crawl-sources", token);
            setCrawlSources(items || []);
        } catch (error) {
            console.error("Failed to fetch crawl sources", error);
            if (error instanceof ApiError && error.status === 401) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            setCrawlSources([]);
        } finally {
            setLoading(false);
        }
    }, [router]);

    useEffect(() => {
        fetchSources();
    }, [fetchSources]);

    const triggerIngest = async (sourceId?: string) => {
        setIsTriggering(true);
        try {
            const token = getAdminToken() || undefined;
            if (!token) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            const qs = sourceId ? `?source_id=${encodeURIComponent(sourceId)}` : "";
            await api.post(`/admin/ingest${qs}`, {}, token);
            alert(sourceId ? `크롤링 시작: ${sourceId}` : "크롤링 시작");
        } catch (error) {
            console.error("Failed to trigger ingest", error);
            if (error instanceof ApiError && error.status === 401) {
                clearAdminSession();
                router.replace("/admin/login");
                return;
            }
            alert("크롤링 시작 실패");
        } finally {
            setIsTriggering(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between gap-3">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">플러그인 관리</h1>
                    <p className="text-sm text-gray-500 mt-1">
                        구성된 크롤링 소스를 확인하고, 특정 소스만 선택해서 ingest를 트리거할 수 있습니다.
                    </p>
                </div>
                <button
                    type="button"
                    onClick={fetchSources}
                    disabled={loading}
                    className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors text-sm font-medium"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                    새로고침
                </button>
            </div>

            <PluginsCrawlTrigger />

            <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                        <h2 className="text-gray-900 font-bold">빠른 실행</h2>
                        <p className="text-sm text-gray-500 mt-1">
                            클로드 관련 소스 중 하나를 선택해서 해당 소스만 크롤링합니다.
                        </p>
                    </div>

                    <div className="flex items-center gap-3 flex-wrap">
                        <select
                            value={selectedSourceId}
                            onChange={(e) => setSelectedSourceId(e.target.value)}
                            disabled={loading || claudeCandidates.length === 0}
                            className="px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white min-w-[320px] max-w-full"
                        >
                            {claudeCandidates.length === 0 ? (
                                <option value="">claude 소스가 없습니다</option>
                            ) : (
                                claudeCandidates.map((s) => (
                                    <option key={s.id} value={s.id}>
                                        {s.id}
                                    </option>
                                ))
                            )}
                        </select>
                        <button
                            type="button"
                            onClick={() => triggerIngest(selectedSourceId || undefined)}
                            disabled={isTriggering || loading || (claudeCandidates.length > 0 && !selectedSourceId)}
                            className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors text-sm font-medium"
                        >
                            {isTriggering ? "시작 중..." : "이 소스 크롤링"}
                        </button>
                    </div>
                </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
                    <h2 className="font-bold text-gray-900">전체 크롤링 소스</h2>
                    <span className="text-xs text-gray-500">{crawlSources.length}개</span>
                </div>
                <div className="p-0">
                    {loading ? (
                        <div className="p-6 text-center text-gray-500">소스 불러오는 중...</div>
                    ) : crawlSources.length > 0 ? (
                        <ul className="divide-y divide-gray-100">
                            {crawlSources.map((source) => (
                                <li key={source.id} className="px-6 py-4 hover:bg-gray-50">
                                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                                        <div className="min-w-0">
                                            <div className="flex items-center gap-2">
                                                <span className="text-sm font-medium text-gray-900 truncate">
                                                    {source.repo_full_name ?? source.url.replace(/^https?:\/\//, "")}
                                                </span>
                                                <a
                                                    href={source.url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    title={source.url}
                                                    className="text-gray-400 hover:text-blue-600 transition-colors flex-shrink-0"
                                                >
                                                    <ExternalLink className="w-4 h-4" />
                                                </a>
                                            </div>
                                            <div className="flex items-center gap-2 flex-wrap mt-2">
                                                <span className="inline-flex items-center px-2 py-0.5 rounded bg-blue-50 text-blue-700 text-[11px] font-medium">
                                                    {source.source_type}
                                                </span>
                                                <span className="text-[11px] text-gray-500 whitespace-nowrap">
                                                    id: <span className="font-mono">{source.id}</span>
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

                                        <div className="flex items-center gap-2">
                                            <button
                                                type="button"
                                                onClick={() => triggerIngest(source.id)}
                                                disabled={isTriggering}
                                                className="px-3 py-2 border border-gray-200 bg-white rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50 transition-colors"
                                                title="이 소스만 ingest"
                                            >
                                                {isTriggering ? "실행 중..." : "이 소스만 크롤링"}
                                            </button>
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
