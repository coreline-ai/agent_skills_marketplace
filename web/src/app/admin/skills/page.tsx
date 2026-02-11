"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useRouter } from "next/navigation";
import { Check, X } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { clearAdminSession, getAdminToken } from "@/lib/admin-auth";

interface RawSkillListItem {
    id: string;
    source_url: string | null;
    external_id: string | null;
    status: string;
    created_at?: string;
}

interface RawSkillListResponse {
    items: RawSkillListItem[];
    total: number;
}

export default function AdminSkillsPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const status = searchParams.get("status") || "pending";
    const focusId = searchParams.get("focus") || "";
    const [loading, setLoading] = useState(true);
    const [items, setItems] = useState<RawSkillListItem[]>([]);
    const [total, setTotal] = useState(0);
    const [counts, setCounts] = useState<{ pending: number; processed: number; error: number } | null>(null);

    useEffect(() => {
        async function fetchQueue() {
            try {
                const token = getAdminToken() || undefined;
                if (!token) {
                    clearAdminSession();
                    router.replace("/admin/login");
                    return;
                }
                const stats = await api.get<{
                    raw_pending: number;
                    raw_processed: number;
                    raw_error: number;
                }>("/admin/dashboard-stats", token);
                setCounts({
                    pending: stats.raw_pending ?? 0,
                    processed: stats.raw_processed ?? 0,
                    error: stats.raw_error ?? 0,
                });
                const res = await api.get<RawSkillListResponse>(
                    `/admin/raw-skills?status=${encodeURIComponent(status)}&page=1&size=100`,
                    token
                );
                setItems(res.items || []);
                setTotal(res.total || 0);
            } catch (error) {
                console.error("Failed to fetch admin raw skills", error);
                if (error instanceof ApiError && error.status === 401) {
                    clearAdminSession();
                    router.replace("/admin/login");
                    return;
                }
                setCounts(null);
                setItems([]);
                setTotal(0);
            } finally {
                setLoading(false);
            }
        }

        setLoading(true);
        fetchQueue();
    }, [router, status]);

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h1 className="text-2xl font-bold text-gray-900">Raw Skills Queue</h1>
                <div className="flex gap-2">
                    <button
                        onClick={() => router.push("/admin/skills?status=pending")}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${status === "pending" ? "bg-gray-900 text-white border-gray-900" : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
                            }`}
                    >
                        pending{counts ? ` (${counts.pending})` : ""}
                    </button>
                    <button
                        onClick={() => router.push("/admin/skills?status=processed")}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${status === "processed" ? "bg-gray-900 text-white border-gray-900" : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
                            }`}
                    >
                        processed{counts ? ` (${counts.processed})` : ""}
                    </button>
                    <button
                        onClick={() => router.push("/admin/skills?status=error")}
                        className={`px-3 py-1.5 rounded-lg text-xs font-bold border transition-colors ${status === "error" ? "bg-gray-900 text-white border-gray-900" : "bg-white text-gray-700 border-gray-200 hover:bg-gray-50"
                            }`}
                    >
                        error{counts ? ` (${counts.error})` : ""}
                    </button>
                </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                    <h2 className="font-semibold text-gray-900">Status: {status}</h2>
                    <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-1 rounded-full">
                        {total} Items
                    </span>
                </div>

                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Source
                                </th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    External ID
                                </th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Date
                                </th>
                                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Status
                                </th>
                                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {loading ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-10 text-center text-sm text-gray-500">
                                        Loading...
                                    </td>
                                </tr>
                            ) : items.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="px-6 py-10 text-center text-sm text-gray-500">
                                        {status === "pending"
                                            ? "No pending items. Queue is drained (normal). Turn ON auto ingest to collect more."
                                            : "No items found."}
                                    </td>
                                </tr>
                            ) : (
                                items.map((item) => (
                                    <tr
                                        key={item.id}
                                        className={`hover:bg-gray-50 ${focusId && item.id === focusId ? "bg-yellow-50" : ""}`}
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">
                                            {item.source_url || "-"}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {item.external_id || "-"}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {item.created_at ? new Date(item.created_at).toISOString().split('T')[0] : "-"}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                                                {item.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button disabled className="text-green-300 mx-2 cursor-not-allowed" title="Approve (coming soon)">
                                                <Check className="w-5 h-5" />
                                            </button>
                                            <button disabled className="text-red-300 mx-2 cursor-not-allowed" title="Reject (coming soon)">
                                                <X className="w-5 h-5" />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
