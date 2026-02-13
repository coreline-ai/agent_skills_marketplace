import { api } from "@/lib/api";
import { buildSkillsHref, type SearchMode } from "@/lib/skills-search";
import { SkillCard } from "@/components/SkillCard";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";

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
    github_stars?: number | null;
    github_updated_at?: string | null;
    match_reason?: string | null;
    trust_score?: number | null;
    trust_level?: string | null;
    trust_flags?: string[] | null;
}

interface SkillListResponse {
    items: SkillListItem[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

interface CategoryItem {
    id: string;
    name: string;
    slug: string;
    skill_count: number;
}

// Ensure dynamic rendering for search params
export const dynamic = 'force-dynamic';

async function getSkills(searchParams: { q?: string; category?: string; page?: number; mode?: SearchMode }) {
    // Construct query string
    const params = new URLSearchParams();
    if (searchParams.q) params.set("q", searchParams.q);
    if (searchParams.category) params.set("category", searchParams.category);
    if (searchParams.page) params.set("page", searchParams.page.toString());
    if (searchParams.mode) params.set("mode", searchParams.mode);

    // In real app use full URL
    return await api.get<SkillListResponse>(`/skills?${params.toString()}`, undefined, { revalidateSeconds: 20 });
}

async function getCategories() {
    return await api.get<CategoryItem[]>("/categories", undefined, { revalidateSeconds: 600 });
}

export default async function SkillsPage(props: {
    // Next.js 15+ provides searchParams as a Promise in Server Components.
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
    const searchParams = await props.searchParams;
    const q = typeof searchParams.q === 'string' ? searchParams.q : undefined;
    const category = typeof searchParams.category === 'string' ? searchParams.category : undefined;
    const modeValue = typeof searchParams.mode === "string" ? searchParams.mode : undefined;
    const mode: SearchMode =
        modeValue === "keyword" || modeValue === "vector" || modeValue === "hybrid"
            ? modeValue
            : "hybrid";
    const page = typeof searchParams.page === 'string' ? Number.parseInt(searchParams.page, 10) : 1;
    const safePage = Number.isFinite(page) && page > 0 ? page : 1;

    const [data, categories] = await Promise.all([
        getSkills({ q, category, page: safePage, mode }),
        getCategories(),
    ]);

    // If the user lands on an out-of-range page (e.g. after filtering), redirect to the last valid page.
    if (data.pages > 0 && safePage > data.pages) {
        redirect(buildSkillsHref({ q, category, page: data.pages, mode }));
    }
    const totalCategoryCount = categories.reduce((sum, item) => sum + (item.skill_count || 0), 0);
    const modeLabel = mode === "keyword" ? "Keyword" : mode === "vector" ? "Vector" : "Hybrid";

    return (
        <div className="space-y-10">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight mb-2">Skills</h1>
                    <div className="text-sm font-bold text-gray-500 dark:text-zinc-500">
                        Showing {data.items.length} of {data.total} skills
                    </div>
                </div>

                <form className="relative w-full md:w-80">
                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-zinc-500" />
                        <input
                            type="text"
                            name="q"
                            placeholder={mode === "vector" ? "Find semantically similar skills..." : mode === "hybrid" ? "Search with keyword + semantic ranking..." : "Search by exact keywords..."}
                            className={`w-full bg-[#F3F4F6] dark:bg-zinc-900 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 border border-transparent dark:border-white/10 focus:bg-white dark:focus:bg-black focus:border-accent dark:focus:border-accent focus:ring-0 rounded-full pl-11 pr-44 py-2.5 transition-all shadow-sm ${mode !== "keyword" ? "ring-2 ring-accent/30 border-accent/50" : ""}`}
                            defaultValue={q}
                        />
                        <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                            {[
                                { key: "keyword" as const, label: "정확도" },
                                { key: "vector" as const, label: "유사도" },
                                { key: "hybrid" as const, label: "하이브리드" },
                            ].map((item) => (
                                <Link
                                    key={item.key}
                                    href={buildSkillsHref({ q, category, mode: item.key })}
                                    className={`px-2 py-1 rounded-md text-[10px] font-bold tracking-tighter transition-all ${mode === item.key
                                        ? "bg-accent text-white shadow-sm"
                                        : "bg-gray-200 dark:bg-white/5 text-gray-500 dark:text-zinc-500 hover:text-black dark:hover:text-white"
                                        }`}
                                >
                                    {item.label}
                                </Link>
                            ))}
                        </div>
                    </div>
                    {category && <input type="hidden" name="category" value={category} />}
                    <input type="hidden" name="mode" value={mode} />
                </form>
            </div>

            <div className="text-xs text-gray-500 dark:text-zinc-500 -mt-4">
                Search mode: <span className="font-semibold text-gray-900 dark:text-white">{modeLabel}</span>
            </div>

            <div className="space-y-4">
                <p className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-zinc-500">Categories</p>
                <div className="flex flex-wrap gap-2">
                    <Link
                        href={buildSkillsHref({ q, mode })}
                        className={`px-4 py-1.5 rounded-full border text-xs font-bold transition-all ${!category
                            ? 'bg-gray-900 dark:bg-white text-white dark:text-black border-gray-900 dark:border-white shadow-md'
                            : 'bg-white dark:bg-zinc-900/40 text-gray-600 dark:text-zinc-400 border-gray-200 dark:border-zinc-800 hover:border-gray-300 dark:hover:border-zinc-700 hover:bg-gray-200 dark:hover:bg-zinc-800'}`}
                    >
                        All ({totalCategoryCount})
                    </Link>
                    {categories.map((item) => (
                        <Link
                            key={item.id}
                            href={buildSkillsHref({ q, category: item.slug, mode })}
                            className={`px-4 py-1.5 rounded-full border text-xs font-bold transition-all ${category === item.slug
                                ? 'bg-gray-900 dark:bg-white text-white dark:text-black border-gray-900 dark:border-white shadow-md'
                                : 'bg-white dark:bg-zinc-900/40 text-gray-600 dark:text-zinc-400 border-gray-200 dark:border-zinc-800 hover:border-gray-300 dark:hover:border-zinc-700 hover:bg-gray-200 dark:hover:bg-zinc-800'}`}
                        >
                            <span className="inline-flex items-center gap-2">
                                <span>{item.name}</span>
                                <span className={`text-[10px] ${category === item.slug ? 'text-gray-300 dark:text-zinc-500' : 'text-gray-400 dark:text-zinc-600'}`}>{item.skill_count || 0}</span>
                            </span>
                        </Link>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.items.length > 0 ? (
                    data.items.map((skill) => (
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
                            githubStars={skill.github_stars}
                            githubUpdatedAt={skill.github_updated_at}
                            matchReason={skill.match_reason ?? null}
                            trustScore={skill.trust_score ?? null}
                            trustLevel={skill.trust_level ?? null}
                            trustFlags={skill.trust_flags ?? null}
                        />
                    ))
                ) : (
                    <div className="col-span-full text-center py-20 border-2 border-dashed border-gray-200 dark:border-zinc-800 rounded-xl bg-gray-50 dark:bg-zinc-900/40">
                        <p className="text-lg font-medium text-gray-500 dark:text-zinc-500">No skills found matching your criteria.</p>
                        {mode === "vector" && (
                            <p className="mt-2 text-sm text-gray-400 dark:text-zinc-600">
                                Try <Link className="underline" href={buildSkillsHref({ q, category, mode: "hybrid" })}>Hybrid</Link> or <Link className="underline" href={buildSkillsHref({ q, category, mode: "keyword" })}>Keyword</Link> mode.
                            </p>
                        )}
                        {mode === "hybrid" && (
                            <p className="mt-2 text-sm text-gray-400 dark:text-zinc-600">
                                If embeddings are unavailable, search automatically falls back to keyword ranking.
                            </p>
                        )}
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
                        href={buildSkillsHref({ q, category, page: safePage - 1, mode })}
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
                        href={buildSkillsHref({ q, category, page: safePage + 1, mode })}
                        className="flex items-center gap-1 px-5 py-2 border border-gray-200 dark:border-zinc-800 rounded-full text-xs font-bold text-gray-600 dark:text-zinc-400 hover:bg-white dark:hover:bg-zinc-800 hover:text-gray-900 dark:hover:text-white hover:shadow-sm transition-all bg-white dark:bg-zinc-900"
                    >
                        Next <ChevronRight className="w-3 h-3" />
                    </Link>
                )}
            </div>
        </div >
    );
}
