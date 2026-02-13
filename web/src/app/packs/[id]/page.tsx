import { api } from "@/lib/api";
import { SkillCard } from "@/components/SkillCard";
import Link from "next/link";
import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import { redirect } from "next/navigation";

interface PackDetail {
    id: string;
    repo_full_name: string;
    repo_url: string;
    skill_count: number;
    updated_at: string;
    dotclaude_skill_count: number;
    skills_dir_skill_count: number;
    description?: string | null;
}

interface SkillListItem {
    id: string;
    name: string;
    slug: string;
    description?: string;
    summary?: string | null;
    views: number;
    stars: number;
    score: number;
    category?: { name?: string } | null;
}

interface SkillListResponse {
    items: SkillListItem[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export const dynamic = "force-dynamic";

async function getPack(id: string) {
    return await api.get<PackDetail>(`/packs/${id}`, undefined, { revalidateSeconds: 120 });
}

async function getPackSkills(id: string, page: number) {
    return await api.get<SkillListResponse>(`/packs/${id}/skills?page=${page}&size=24`, undefined, { revalidateSeconds: 60 });
}

export default async function PackDetailPage(props: {
    params: Promise<{ id: string }>;
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
    const params = await props.params;
    const searchParams = await props.searchParams;
    const id = params.id;
    const page = typeof searchParams.page === "string" ? Number.parseInt(searchParams.page, 10) : 1;
    const safePage = Number.isFinite(page) && page > 0 ? page : 1;

    const [pack, data] = await Promise.all([getPack(id), getPackSkills(id, safePage)]);

    if (data.pages > 0 && safePage > data.pages) {
        redirect(`/packs/${id}?page=${data.pages}`);
    }

    return (
        <div className="space-y-10">
            <div className="flex items-center justify-between gap-4 flex-wrap">
                <div className="flex items-center gap-3">
                    <Link
                        href="/packs"
                        className="inline-flex items-center gap-1 px-4 py-2 rounded-full border border-gray-200 dark:border-zinc-800 text-xs font-bold text-gray-600 dark:text-zinc-400 hover:bg-white dark:hover:bg-zinc-800 bg-white dark:bg-zinc-900 transition-all"
                    >
                        <ChevronLeft className="w-3 h-3" />
                        Packs
                    </Link>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">
                            {pack.repo_full_name}
                        </h1>
                        <div className="mt-1 text-sm font-bold text-gray-500 dark:text-zinc-500">
                            {data.total} skills in this pack
                        </div>
                    </div>
                </div>

                <a
                    href={pack.repo_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-gray-200 dark:border-zinc-800 text-xs font-bold text-gray-600 dark:text-zinc-400 hover:bg-white dark:hover:bg-zinc-800 bg-white dark:bg-zinc-900 transition-all"
                >
                    Repo <ExternalLink className="w-3 h-3" />
                </a>
            </div>

            {pack.description && (
                <div className="bg-gray-50 dark:bg-zinc-900/40 border border-gray-200 dark:border-zinc-800 rounded-2xl p-6 text-gray-700 dark:text-zinc-300">
                    {pack.description}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.items.map((skill) => (
                    <SkillCard
                        key={skill.id}
                        id={skill.id}
                        name={skill.name}
                        slug={skill.slug}
                        description={skill.description || "No description provided."}
                        summary={skill.summary ?? null}
                        views={skill.views}
                        stars={skill.stars}
                        score={skill.score}
                        category={skill.category?.name || "Uncategorized"}
                    />
                ))}
            </div>

            <div className="flex justify-center items-center gap-4 pt-8 border-t border-gray-100 dark:border-white/5">
                {safePage <= 1 ? (
                    <span className="flex items-center gap-1 px-5 py-2 border border-gray-100 dark:border-white/5 rounded-full text-xs font-bold text-gray-300 dark:text-zinc-700 cursor-not-allowed bg-gray-50 dark:bg-zinc-900/40">
                        <ChevronLeft className="w-3 h-3" /> Previous
                    </span>
                ) : (
                    <Link
                        href={`/packs/${id}?page=${safePage - 1}`}
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
                        href={`/packs/${id}?page=${safePage + 1}`}
                        className="flex items-center gap-1 px-5 py-2 border border-gray-200 dark:border-zinc-800 rounded-full text-xs font-bold text-gray-600 dark:text-zinc-400 hover:bg-white dark:hover:bg-zinc-800 hover:text-gray-900 dark:hover:text-white hover:shadow-sm transition-all bg-white dark:bg-zinc-900"
                    >
                        Next <ChevronRight className="w-3 h-3" />
                    </Link>
                )}
            </div>
        </div>
    );
}
