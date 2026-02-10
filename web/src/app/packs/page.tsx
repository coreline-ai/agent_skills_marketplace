import { api } from "@/lib/api";
import { PackCard } from "@/components/PackCard";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";

interface PackListItem {
    id: string;
    repo_full_name: string;
    repo_url: string;
    skill_count: number;
    updated_at: string;
    dotclaude_skill_count: number;
    skills_dir_skill_count: number;
    description?: string | null;
}

interface PackListResponse {
    items: PackListItem[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export const dynamic = "force-dynamic";

async function getPacks(searchParams: { q?: string; page?: number }) {
    const params = new URLSearchParams();
    if (searchParams.q) params.set("q", searchParams.q);
    if (searchParams.page) params.set("page", String(searchParams.page));
    return await api.get<PackListResponse>(`/packs?${params.toString()}`);
}

function buildPacksHref(params: { q?: string; page?: number }) {
    const query = new URLSearchParams();
    if (params.q) query.set("q", params.q);
    if (params.page && params.page > 1) query.set("page", params.page.toString());
    const queryString = query.toString();
    return queryString ? `/packs?${queryString}` : "/packs";
}

export default async function PacksPage(props: {
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
    const searchParams = await props.searchParams;
    const q = typeof searchParams.q === "string" ? searchParams.q : undefined;
    const page = typeof searchParams.page === "string" ? Number.parseInt(searchParams.page, 10) : 1;
    const safePage = Number.isFinite(page) && page > 0 ? page : 1;

    const data = await getPacks({ q, page: safePage });
    if (data.pages > 0 && safePage > data.pages) {
        redirect(buildPacksHref({ q, page: data.pages }));
    }

    return (
        <div className="space-y-10">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight mb-2">Skill Packs</h1>
                    <div className="text-sm font-bold text-gray-500 dark:text-zinc-500">
                        Showing {data.items.length} of {data.total} packs
                    </div>
                </div>

                <form className="relative w-full md:w-80">
                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-zinc-500" />
                        <input
                            type="text"
                            name="q"
                            placeholder="Search by repo (owner/repo)..."
                            className="w-full bg-[#F3F4F6] dark:bg-zinc-900 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 border border-transparent dark:border-white/10 focus:bg-white dark:focus:bg-black focus:border-accent dark:focus:border-accent focus:ring-0 rounded-full pl-11 pr-4 py-2.5 transition-all shadow-sm"
                            defaultValue={q}
                        />
                    </div>
                </form>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.items.length > 0 ? (
                    data.items.map((pack) => (
                        <PackCard
                            key={pack.id}
                            id={pack.id}
                            repo_full_name={pack.repo_full_name}
                            repo_url={pack.repo_url}
                            skill_count={pack.skill_count}
                            updated_at={pack.updated_at}
                            dotclaude_skill_count={pack.dotclaude_skill_count}
                            skills_dir_skill_count={pack.skills_dir_skill_count}
                            description={pack.description ?? null}
                        />
                    ))
                ) : (
                    <div className="col-span-full text-center py-20 border-2 border-dashed border-gray-200 dark:border-zinc-800 rounded-xl bg-gray-50 dark:bg-zinc-900/40">
                        <p className="text-lg font-medium text-gray-500 dark:text-zinc-500">No packs found.</p>
                    </div>
                )}
            </div>

            <div className="flex justify-center items-center gap-4 pt-8 border-t border-gray-100 dark:border-white/5">
                {safePage <= 1 ? (
                    <span className="flex items-center gap-1 px-5 py-2 border border-gray-100 dark:border-white/5 rounded-full text-xs font-bold text-gray-300 dark:text-zinc-700 cursor-not-allowed bg-gray-50 dark:bg-zinc-900/40">
                        <ChevronLeft className="w-3 h-3" /> Previous
                    </span>
                ) : (
                    <Link
                        href={buildPacksHref({ q, page: safePage - 1 })}
                        className="flex items-center gap-1 px-5 py-2 border border-gray-200 dark:border-zinc-800 rounded-full text-xs font-bold text-gray-600 dark:text-zinc-400 hover:bg-white dark:hover:bg-zinc-800 hover:text-gray-900 dark:hover:text-white hover:shadow-sm transition-all bg-white dark:bg-zinc-900"
                    >
                        <ChevronLeft className="w-3 h-3" /> Previous
                    </Link>
                )}

                <span className="text-xs font-bold text-gray-500 dark:text-zinc-500">
                    Page <span className="text-gray-900 dark:text-white">{data.page}</span> of {data.pages}
                </span>

                {safePage >= data.pages ? (
                    <span className="flex items-center gap-1 px-5 py-2 border border-gray-100 dark:border-white/5 rounded-full text-xs font-bold text-gray-300 dark:text-zinc-700 cursor-not-allowed bg-gray-50 dark:bg-zinc-900/40">
                        Next <ChevronRight className="w-3 h-3" />
                    </span>
                ) : (
                    <Link
                        href={buildPacksHref({ q, page: safePage + 1 })}
                        className="flex items-center gap-1 px-5 py-2 border border-gray-200 dark:border-zinc-800 rounded-full text-xs font-bold text-gray-600 dark:text-zinc-400 hover:bg-white dark:hover:bg-zinc-800 hover:text-gray-900 dark:hover:text-white hover:shadow-sm transition-all bg-white dark:bg-zinc-900"
                    >
                        Next <ChevronRight className="w-3 h-3" />
                    </Link>
                )}
            </div>
        </div>
    );
}

