"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/app/lib/api";
import { clearAdminSession, getAdminToken } from "@/app/lib/admin-auth";
import { RefreshCw } from "lucide-react";

const PLUGIN_SOURCE_IDS = [
    "claude-code-marketplace-directory",
    "bkit-ai-directory",
    "awesome-claude-plugins-awesomejun",
    "awesome-claude-skills-composiohq",
    "awesome-claude-skills-voltagent",
    "awesome-claude-skills-behisecc",
    "awesome-claude-skills-travisvn",
    "anthropic-official-skills",
    "claude-code-skills-marketplace-daymade",
    "claude-code-skills-levnikolaevich",
];

export function PluginsCrawlTrigger() {
    const router = useRouter();
    const [hasAdminSession, setHasAdminSession] = useState(false);
    const [isTriggering, setIsTriggering] = useState(false);

    useEffect(() => {
        setHasAdminSession(Boolean(getAdminToken()));
    }, []);

    const helperText = useMemo(() => {
        if (!hasAdminSession) {
            return (
                <>
                    관리자 로그인(토큰)이 없어서 여기서 크롤링을 트리거할 수 없습니다.{" "}
                    <a href="/admin/login" className="underline font-medium">
                        /admin/login
                    </a>
                    에서 로그인 후 다시 시도하세요.
                </>
            );
        }
        return <>Claude Code Marketplace 소스에서 최신 SKILL.md들을 ingest/parse 합니다.</>;
    }, [hasAdminSession]);

    const trigger = async () => {
        setIsTriggering(true);
        try {
            const token = getAdminToken() || undefined;
            if (!token) {
                setHasAdminSession(false);
                router.push("/admin/login");
                return;
            }
            const qs = PLUGIN_SOURCE_IDS.map((id) => `source_ids=${encodeURIComponent(id)}`).join("&");
            await api.post(`/admin/ingest?${qs}`, {}, token);
            alert(`크롤링 시작: ${PLUGIN_SOURCE_IDS.length} sources`);
            router.refresh();
        } catch (error) {
            console.error("Failed to trigger ingest", error);
            if (error instanceof ApiError && error.status === 401) {
                clearAdminSession();
                setHasAdminSession(false);
                router.push("/admin/login");
                return;
            }
            alert("크롤링 시작 실패");
        } finally {
            setIsTriggering(false);
        }
    };

    return (
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h2 className="text-gray-900 font-bold">마켓플레이스 크롤링</h2>
                    <p className="text-sm text-gray-500 mt-1">{helperText}</p>
                </div>

                <button
                    type="button"
                    onClick={trigger}
                    disabled={!hasAdminSession || isTriggering}
                    className="inline-flex items-center justify-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 transition-colors text-sm font-medium"
                >
                    <RefreshCw className={`w-4 h-4 ${isTriggering ? "animate-spin" : ""}`} />
                    {isTriggering ? "마켓플레이스 크롤링 시작 중..." : "마켓플레이스 크롤링 시작"}
                </button>
            </div>
        </div>
    );
}
