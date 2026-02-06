import { api } from "@/app/lib/api";
import { SkillCard } from "@/components/SkillCard";
import { Search } from "lucide-react";
import Link from "next/link";

interface SkillListItem {
    id: string;
    name: string;
    slug: string;
    description?: string;
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
    searchParams: { [key: string]: string | string[] | undefined };
}) {
    const searchParams = props.searchParams;
    const q = typeof searchParams.q === 'string' ? searchParams.q : undefined;
    const category = typeof searchParams.category === 'string' ? searchParams.category : undefined;
    const page = typeof searchParams.page === 'string' ? Number.parseInt(searchParams.page, 10) : 1;
    const safePage = Number.isFinite(page) && page > 0 ? page : 1;

    const [data, categories] = await Promise.all([
        getSkills({ q, category, page: safePage }),
        getCategories(),
    ]);
    const totalCategoryCount = categories.reduce((sum, item) => sum + (item.skill_count || 0), 0);

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <h1 className="text-3xl font-bold text-gray-900">Explore Skills</h1>
                <div className="text-sm text-gray-500">
                    Showing {data.items.length} of {data.total} skills
                </div>

                {/* Simple Search Form */}
                <form className="relative w-full md:w-96">
                    <input
                        name="q"
                        defaultValue={q}
                        placeholder="Search skills..."
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    />
                    <Search className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
                    {category && <input type="hidden" name="category" value={category} />}
                </form>
            </div>

            <div className="space-y-3">
                <p className="text-sm font-medium text-gray-700">Categories</p>
                <div className="flex flex-wrap gap-2">
                    <Link
                        href={buildSkillsHref({ q })}
                        className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                            !category
                                ? "bg-blue-600 text-white border-blue-600"
                                : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                        }`}
                    >
                        <span className="inline-flex items-center gap-2">
                            <span>All</span>
                            <span className={`inline-flex items-center justify-center min-w-6 px-1.5 py-0.5 text-xs rounded-full ${
                                !category ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-600"
                            }`}>
                                {totalCategoryCount}
                            </span>
                        </span>
                    </Link>
                    {categories.map((item) => (
                        <Link
                            key={item.id}
                            href={buildSkillsHref({ q, category: item.slug })}
                            className={`px-3 py-1.5 text-sm rounded-lg border transition-colors ${
                                category === item.slug
                                    ? "bg-blue-600 text-white border-blue-600"
                                    : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                            }`}
                        >
                            <span className="inline-flex items-center gap-2">
                                <span>{item.name}</span>
                                <span className={`inline-flex items-center justify-center min-w-6 px-1.5 py-0.5 text-xs rounded-full ${
                                    category === item.slug ? "bg-blue-500 text-white" : "bg-gray-100 text-gray-600"
                                }`}>
                                    {item.skill_count || 0}
                                </span>
                            </span>
                        </Link>
                    ))}
                </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.items.length > 0 ? (
                    data.items.map((skill) => (
                        <SkillCard
                            key={skill.id}
                            id={skill.id}
                            name={skill.name}
                            slug={skill.slug}
                            description={skill.description || "No description provided."}
                            views={skill.views}
                            stars={skill.stars}
                            score={skill.score}
                            category={skill.category?.name || "Uncategorized"}
                        />
                    ))
                ) : (
                    <div className="col-span-full text-center py-12 text-gray-500">
                        No skills found matching your criteria.
                    </div>
                )}
            </div>

            <div className="flex justify-center items-center gap-4 pt-8 border-t border-gray-100">
                    <Link
                        href={buildSkillsHref({ q, category, page: safePage - 1 })}
                        className={`px-4 py-2 border rounded-md text-sm font-medium transition-colors ${safePage <= 1
                            ? "border-gray-200 text-gray-300 pointer-events-none"
                            : "border-gray-300 text-gray-700 hover:bg-gray-50"
                        }`}
                    >
                    Previous
                </Link>
                    <span className="text-sm font-medium text-gray-600">
                        Page {data.page} of {data.pages}
                    </span>
                    <Link
                        href={buildSkillsHref({ q, category, page: safePage + 1 })}
                        className={`px-4 py-2 border rounded-md text-sm font-medium transition-colors ${safePage >= data.pages
                            ? "border-gray-200 text-gray-300 pointer-events-none"
                            : "border-gray-300 text-gray-700 hover:bg-gray-50"
                        }`}
                    >
                    Next
                </Link>
            </div>
        </div>
    );
}
