"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert, ShieldCheck } from "lucide-react";
import { api, ApiError } from "@/app/lib/api";
import { clearAdminSession, getAdminToken } from "@/app/lib/admin-auth";

interface RawSkillIssueItem {
    id: string;
    source_url: string | null;
    external_id: string | null;
    status: string;
    parse_error?: Record<string, unknown> | null;
}

interface RawSkillListResponse {
    items: RawSkillIssueItem[];
    total: number;
}

function getIssueMessage(parseError?: Record<string, unknown> | null): string {
    if (!parseError) return "Parsing failed";
    const message = parseError.message;
    if (typeof message === "string" && message.trim()) return message;
    const detail = parseError.detail;
    if (typeof detail === "string" && detail.trim()) return detail;
    return "Parsing failed";
}

export default function AdminQualityPage() {
    const router = useRouter();
    const [loading, setLoading] = useState(true);
    const [issues, setIssues] = useState<RawSkillIssueItem[]>([]);
    const [totalIssues, setTotalIssues] = useState(0);

    useEffect(() => {
        async function fetchQualityIssues() {
            try {
                const token = getAdminToken() || undefined;
                if (!token) {
                    clearAdminSession();
                    router.replace("/admin/login");
                    return;
                }
                const res = await api.get<RawSkillListResponse>(
                    "/admin/raw-skills?status=error&page=1&size=100",
                    token
                );
                setIssues(res.items || []);
                setTotalIssues(res.total || 0);
            } catch (error) {
                console.error("Failed to fetch quality issues", error);
                if (error instanceof ApiError && error.status === 401) {
                    clearAdminSession();
                    router.replace("/admin/login");
                    return;
                }
                setIssues([]);
                setTotalIssues(0);
            } finally {
                setLoading(false);
            }
        }

        fetchQualityIssues();
    }, [router]);

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900">Quality Control</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-green-50 text-green-600 rounded-lg">
                            <ShieldCheck className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-900">Quality Score</h3>
                            <p className="text-sm text-gray-500">Overall marketplace health</p>
                        </div>
                    </div>
                    <div className="text-4xl font-extrabold text-gray-900">92<span className="text-lg text-gray-400 font-normal">/100</span></div>
                </div>

                <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-red-50 text-red-600 rounded-lg">
                            <ShieldAlert className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-900">Critical Issues</h3>
                            <p className="text-sm text-gray-500">Requires immediate action</p>
                        </div>
                    </div>
                    <div className="text-4xl font-extrabold text-gray-900">{totalIssues}</div>
                </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="font-bold text-gray-900">Detected Issues</h3>
                </div>
                <ul className="divide-y divide-gray-200">
                    {loading ? (
                        <li className="px-6 py-8 text-sm text-center text-gray-500">Loading...</li>
                    ) : issues.length === 0 ? (
                        <li className="px-6 py-8 text-sm text-center text-gray-500">No critical issues detected.</li>
                    ) : (
                        issues.map((item) => (
                            <li key={item.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                                <div>
                                    <h4 className="font-semibold text-gray-900">{item.external_id || item.source_url || item.id}</h4>
                                    <p className="text-sm text-gray-500">{getIssueMessage(item.parse_error)}</p>
                                </div>
                                <span className="px-2 py-1 text-xs font-bold rounded-full uppercase bg-red-100 text-red-800">
                                    high
                                </span>
                            </li>
                        ))
                    )}
                </ul>
            </div>
        </div>
    );
}
