import { api } from "@/lib/api";
import { SkillCard } from "@/components/SkillCard";
import { Search, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";
import { redirect } from "next/navigation";

interface PluginListItem {
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

interface PluginListResponse {
    items: PluginListItem[];
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

export const dynamic = "force-dynamic";

async function getPlugins(searchParams: { q?: string; category?: string; page?: number }) {
    const params = new URLSearchParams();
    if (searchParams.q) params.set("q", searchParams.q);
    if (searchParams.category) params.set("category", searchParams.category);
    if (searchParams.page) params.set("page", searchParams.page.toString());
    return await api.get<PluginListResponse>(`/plugins?${params.toString()}`);
}

async function getCategories() {
    // Reuse global taxonomy categories for filtering.
    return await api.get<CategoryItem[]>("/categories");
}

function buildPluginsHref(params: { q?: string; category?: string; page?: number }) {
    const query = new URLSearchParams();
    if (params.q) query.set("q", params.q);
    if (params.category) query.set("category", params.category);
    if (params.page && params.page > 1) query.set("page", params.page.toString());
    const queryString = query.toString();
    return queryString ? `/plugins?${queryString}` : "/plugins";
}

export default async function PluginsPage(props: {
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
    const searchParams = await props.searchParams;
    const q = typeof searchParams.q === "string" ? searchParams.q : undefined;
    const category = typeof searchParams.category === "string" ? searchParams.category : undefined;
    const page = typeof searchParams.page === "string" ? Number.parseInt(searchParams.page, 10) : 1;
    const safePage = Number.isFinite(page) && page > 0 ? page : 1;

    const [data, categories] = await Promise.all([
        getPlugins({ q, category, page: safePage }),
        getCategories(),
    ]);

    if (data.pages > 0 && safePage > data.pages) {
        redirect(buildPluginsHref({ q, category, page: data.pages }));
    }

    return (
        <div className="space-y-10">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight mb-2">Plugins</h1>
                    <div className="text-sm font-bold text-gray-500 dark:text-zinc-500">
                        Showing {data.items.length} of {data.total} marketplace items
                    </div>
                </div>

                <form className="relative w-full md:w-80">
                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-zinc-500" />
                        <input
                            type="text"
                            name="q"
                            placeholder="Search marketplace items..."
                            className="w-full bg-[#F3F4F6] dark:bg-zinc-900 text-sm text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-zinc-500 border border-transparent dark:border-white/10 focus:bg-white dark:focus:bg-black focus:border-accent dark:focus:border-accent focus:ring-0 rounded-full pl-11 pr-4 py-2.5 transition-all shadow-sm"
                            defaultValue={q}
                        />
                    </div>
                    {category && <input type="hidden" name="category" value={category} />}
                </form>
            </div>

            <div className="space-y-4">
                <p className="text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-zinc-500">
                    Categories (filter)
                </p>
                <div className="flex flex-wrap gap-2">
                    <Link
                        href={buildPluginsHref({ q })}
                        className={`px-4 py-1.5 rounded-full border text-xs font-bold transition-all ${!category
                            ? "bg-gray-900 dark:bg-white text-white dark:text-black border-gray-900 dark:border-white shadow-md"
                            : "bg-white dark:bg-zinc-900/40 text-gray-600 dark:text-zinc-400 border-gray-200 dark:border-zinc-800 hover:border-gray-300 dark:hover:border-zinc-700 hover:bg-gray-200 dark:hover:bg-zinc-800"
                            }`}
                    >
                        All
                    </Link>
                    {categories.map((item) => (
                        <Link
                            key={item.id}
                            href={buildPluginsHref({ q, category: item.slug })}
                            className={`px-4 py-1.5 rounded-full border text-xs font-bold transition-all ${category === item.slug
                                ? "bg-gray-900 dark:bg-white text-white dark:text-black border-gray-900 dark:border-white shadow-md"
                                : "bg-white dark:bg-zinc-900/40 text-gray-600 dark:text-zinc-400 border-gray-200 dark:border-zinc-800 hover:border-gray-300 dark:hover:border-zinc-700 hover:bg-gray-200 dark:hover:bg-zinc-800"
                                }`}
                        >
                            {item.name}
                        </Link>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.items.length > 0 ? (
                    data.items.map((item) => (
                        <SkillCard
                            key={item.id}
                            id={item.id}
                            name={item.name}
                            slug={item.slug}
                            description={item.description || "No description provided."}
                            summary={item.summary ?? null}
                            views={item.views}
                            stars={item.stars}
                            score={item.score}
                            category={item.category?.name || "Uncategorized"}
                        />
                    ))
                ) : (
                    <div className="col-span-full text-center py-20 border-2 border-dashed border-gray-200 dark:border-zinc-800 rounded-xl bg-gray-50 dark:bg-zinc-900/40">
                        <p className="text-lg font-medium text-gray-500 dark:text-zinc-500">
                            No marketplace items yet. Run crawling above (admin) and refresh.
                        </p>
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
                        href={buildPluginsHref({ q, category, page: safePage - 1 })}
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
                        href={buildPluginsHref({ q, category, page: safePage + 1 })}
                        className="flex items-center gap-1 px-5 py-2 border border-gray-200 dark:border-zinc-800 rounded-full text-xs font-bold text-gray-600 dark:text-zinc-400 hover:bg-white dark:hover:bg-zinc-800 hover:text-gray-900 dark:hover:text-white hover:shadow-sm transition-all bg-white dark:bg-zinc-900"
                    >
                        Next <ChevronRight className="w-3 h-3" />
                    </Link>
                )}
            </div>
        </div>
    );
}
