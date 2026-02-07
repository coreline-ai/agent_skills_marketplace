import { api } from "@/app/lib/api";
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

async function getSkills(searchParams: { q?: string; category?: string; page?: number }) {
    // Construct query string
    const params = new URLSearchParams();
    if (searchParams.q) params.set("q", searchParams.q);
    if (searchParams.category) params.set("category", searchParams.category);
    if (searchParams.page) params.set("page", searchParams.page.toString());

    // In real app use full URL
    return await api.get<SkillListResponse>(`/skills?${params.toString()}`);
}

async function getCategories() {
    return await api.get<CategoryItem[]>("/categories");
}

function buildSkillsHref(params: { q?: string; category?: string; page?: number }) {
    const query = new URLSearchParams();
    if (params.q) query.set("q", params.q);
    if (params.category) query.set("category", params.category);
    if (params.page && params.page > 1) query.set("page", params.page.toString());
    const queryString = query.toString();
    return queryString ? `/skills?${queryString}` : "/skills";
}

export default async function SkillsPage(props: {
    // Next.js 15+ provides searchParams as a Promise in Server Components.
    searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
    const searchParams = await props.searchParams;
    const q = typeof searchParams.q === 'string' ? searchParams.q : undefined;
    const category = typeof searchParams.category === 'string' ? searchParams.category : undefined;
    const page = typeof searchParams.page === 'string' ? Number.parseInt(searchParams.page, 10) : 1;
    const safePage = Number.isFinite(page) && page > 0 ? page : 1;

    const [data, categories] = await Promise.all([
        getSkills({ q, category, page: safePage }),
        getCategories(),
    ]);

    // If the user lands on an out-of-range page (e.g. after filtering), redirect to the last valid page.
    if (data.pages > 0 && safePage > data.pages) {
        redirect(buildSkillsHref({ q, category, page: data.pages }));
    }
    const totalCategoryCount = categories.reduce((sum, item) => sum + (item.skill_count || 0), 0);

    return (
        <div className="space-y-10">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">Skills</h1>
                    <div className="text-sm font-bold text-gray-500">
                        Showing {data.items.length} of {data.total} skills
                    </div>
                </div>

                <form className="relative w-full md:w-80">
                    <div className="relative">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                        <input
                            type="text"
                            name="q"
                            placeholder="Search by keywords..."
                            className="w-full bg-[#F3F4F6] text-sm text-gray-900 placeholder-gray-400 border border-transparent focus:bg-white focus:border-accent focus:ring-0 rounded-full pl-11 pr-4 py-2.5 transition-all shadow-sm"
                            defaultValue={q}
                        />
                    </div>
                    {category && <input type="hidden" name="category" value={category} />}
                </form>
            </div>

            <div className="space-y-4">
                <p className="text-xs font-bold uppercase tracking-wider text-gray-400">Categories</p>
                <div className="flex flex-wrap gap-2">
                    <Link
                        href={buildSkillsHref({ q })}
                        className={`px-4 py-1.5 rounded-full border text-xs font-bold transition-all ${!category
                            ? 'bg-gray-900 text-white border-gray-900 shadow-md'
                            : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-200'}`}
                    >
                        All ({totalCategoryCount})
                    </Link>
                    {categories.map((item) => (
                        <Link
                            key={item.id}
                            href={buildSkillsHref({ q, category: item.slug })}
                            className={`px-4 py-1.5 rounded-full border text-xs font-bold transition-all ${category === item.slug
                                ? 'bg-gray-900 text-white border-gray-900 shadow-md'
                                : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-gray-200'}`}
                        >
                            <span className="inline-flex items-center gap-2">
                                <span>{item.name}</span>
                                <span className={`text-[10px] ${category === item.slug ? 'text-gray-300' : 'text-gray-400'}`}>{item.skill_count || 0}</span>
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
                        />
                    ))
                ) : (
                    <div className="col-span-full text-center py-20 border-2 border-dashed border-gray-200 rounded-xl bg-gray-50">
                        <p className="text-lg font-medium text-gray-500">No skills found matching your criteria.</p>
                    </div>
                )}
            </div>

            <div className="flex justify-center items-center gap-4 pt-8 border-t border-gray-100">
                {safePage <= 1 ? (
                    <span className="flex items-center gap-1 px-5 py-2 border border-gray-100 rounded-full text-xs font-bold text-gray-300 cursor-not-allowed bg-gray-50">
                        <ChevronLeft className="w-3 h-3" /> Previous
                    </span>
                ) : (
                    <Link
                        href={buildSkillsHref({ q, category, page: safePage - 1 })}
                        className="flex items-center gap-1 px-5 py-2 border border-gray-200 rounded-full text-xs font-bold text-gray-600 hover:bg-white hover:text-gray-900 hover:shadow-sm transition-all bg-white"
                    >
                        <ChevronLeft className="w-3 h-3" /> Previous
                    </Link>
                )}

                <span className="text-xs font-bold text-gray-500">
                    Page <span className="text-gray-900">{data.page}</span> of {data.pages}
                </span>

                {safePage >= data.pages ? (
                    <span className="flex items-center gap-1 px-5 py-2 border border-gray-100 rounded-full text-xs font-bold text-gray-300 cursor-not-allowed bg-gray-50">
                        Next <ChevronRight className="w-3 h-3" />
                    </span>
                ) : (
                    <Link
                        href={buildSkillsHref({ q, category, page: safePage + 1 })}
                        className="flex items-center gap-1 px-5 py-2 border border-gray-200 rounded-full text-xs font-bold text-gray-600 hover:bg-white hover:text-gray-900 hover:shadow-sm transition-all bg-white"
                    >
                        Next <ChevronRight className="w-3 h-3" />
                    </Link>
                )}
            </div>
        </div >
    );
}
