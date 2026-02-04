import { api } from "@/app/lib/api";
import { SkillCard } from "@/components/SkillCard";
import { Search } from "lucide-react";

interface SkillListResponse {
    items: any[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

// Ensure dynamic rendering for search params
export const dynamic = 'force-dynamic';

async function getSkills(searchParams: { q?: string; category?: string }) {
    // Construct query string
    const params = new URLSearchParams();
    if (searchParams.q) params.set("q", searchParams.q);
    if (searchParams.category) params.set("category", searchParams.category);

    // In real app use full URL
    return await api.get<SkillListResponse>(`/skills?${params.toString()}`);
}

export default async function SkillsPage({
    searchParams,
}: {
    searchParams: { [key: string]: string | string[] | undefined };
}) {
    const q = typeof searchParams.q === 'string' ? searchParams.q : undefined;
    const category = typeof searchParams.category === 'string' ? searchParams.category : undefined;

    const data = await getSkills({ q, category });

    return (
        <div className="space-y-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <h1 className="text-3xl font-bold text-gray-900">Explore Skills</h1>

                {/* Simple Search Form */}
                <form className="relative w-full md:w-96">
                    <input
                        name="q"
                        defaultValue={q}
                        placeholder="Search skills..."
                        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                    />
                    <Search className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
                </form>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {data.items.length > 0 ? (
                    data.items.map((skill: any) => (
                        <SkillCard
                            key={skill.id}
                            {...skill}
                            category={skill.category?.name || "Uncategorized"}
                        />
                    ))
                ) : (
                    <div className="col-span-full text-center py-12 text-gray-500">
                        No skills found matching your criteria.
                    </div>
                )}
            </div>

            {/* Pagination control would go here */}
        </div>
    );
}
