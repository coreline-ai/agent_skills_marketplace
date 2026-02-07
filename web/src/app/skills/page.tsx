import { api } from "@/app/lib/api";
import { SkillCard } from "@/components/SkillCard";
import { Search } from "lucide-react";
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
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                    <h1 className="text-4xl font-black text-black dark:text-white tracking-tight mb-2">Explore Skills</h1>
                    <div className="text-sm font-bold text-gray-600 dark:text-gray-400">
                        Showing {data.items.length} of {data.total} skills
                    </div>
                </div>

                {/* Simple Search Form */}
                <form className="relative w-full md:w-96">
                    <div className="flex flex-col md:flex-row items-center gap-6 bg-white dark:bg-black border-2 border-black dark:border-white p-6 neo-shadow dark:shadow-none rounded-xl">
                        <div className="relative flex-1 w-full">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-6 h-6 text-black dark:text-white" />
                            <input
                                type="text"
                                name="q"
                                placeholder="Search skills (e.g., 'trading', 'writer')..."
                                className="w-full pl-12 pr-4 py-4 bg-white dark:bg-black border-2 border-black dark:border-white text-black dark:text-white font-bold text-lg placeholder:text-gray-400 focus:outline-none focus:ring-0 transition-all"
                                defaultValue={q}
                            />
                        </div>
                    </div>
                    {category && <input type="hidden" name="category" value={category} />}
                </form>
            </div>

            <div className="space-y-4">
                <p className="text-sm font-bold uppercase tracking-wider">Categories</p>
                <div className="flex flex-wrap gap-2 py-4">
                    <Link
                        href={buildSkillsHref({ q })}
                        className={`px-4 py-2 border-2 border-main font-bold text-sm transition-all ${!category ? 'bg-invert' : 'bg-background text-foreground hover:bg-accent hover:text-black'}`}
                    >
                        All ({totalCategoryCount})
                    </Link>
                    {categories.map((item) => (
                        <Link
                            key={item.id}
                            href={buildSkillsHref({ q, category: item.slug })}
                            className={`px-4 py-2 border-2 border-main font-bold text-sm transition-all ${category === item.slug ? 'bg-invert' : 'bg-background text-foreground hover:bg-accent hover:text-black'}`}
                        >
                            <span className="inline-flex items-center gap-2">
                                <span>{item.name}</span>
                                <span className={`inline-flex items-center justify-center min-w-6 px-1.5 py-0.5 text-xs rounded-full border border-current ${category === item.slug ? "bg-background text-foreground" : "bg-invert"
                                    }`}>
                                    {item.skill_count || 0}
                                </span>
                            </span>
                        </Link>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
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
                    <div className="col-span-full text-center py-20 border-2 border-dashed border-black rounded-lg bg-gray-50">
                        <p className="text-xl font-bold text-gray-500">No skills found matching your criteria.</p>
                    </div>
                )}
            </div>

            <div className="flex justify-center items-center gap-4 pt-8 border-t-2 border-main">
                {safePage <= 1 ? (
                    <span className="px-6 py-2 border-2 rounded-lg text-sm font-bold bg-foreground/5 text-foreground/40 cursor-not-allowed border-foreground/20">
                        Previous
                    </span>
                ) : (
                    <Link
                        href={buildSkillsHref({ q, category, page: safePage - 1 })}
                        className="px-6 py-2 border-2 border-main rounded-lg text-sm font-bold transition-all bg-invert hover:bg-accent hover:text-black hover:translate-x-[1px] hover:translate-y-[1px]"
                    >
                        Previous
                    </Link>
                )}
                <span className="text-sm font-bold bg-accent text-black px-3 py-1 rounded border-2 border-black">
                    Page {data.page} of {data.pages}
                </span>
                {safePage >= data.pages ? (
                    <span className="px-6 py-2 border-2 rounded-lg text-sm font-bold bg-foreground/5 text-foreground/40 cursor-not-allowed border-foreground/20">
                        Next
                    </span>
                ) : (
                    <Link
                        href={buildSkillsHref({ q, category, page: safePage + 1 })}
                        className="px-6 py-2 border-2 border-main rounded-lg text-sm font-bold transition-all bg-invert hover:bg-accent hover:text-black hover:translate-x-[1px] hover:translate-y-[1px]"
                    >
                        Next
                    </Link>
                )}
            </div>
        </div >
    );
}
