import Link from "next/link";
import { Star, Eye, ChevronRight } from "lucide-react";

interface SkillCardProps {
    id: string;
    name: string;
    slug: string;
    description: string;
    summary?: string | null;
    category: string;
    views: number;
    stars: number;
    score: number;
    rank?: number;
}

export function SkillCard({ id, name, slug, description, summary, category, views, stars, rank }: SkillCardProps) {
    const blurb = (summary && summary.trim()) ? summary : description;

    // Category tag style mapping based on code.html design
    const getCategoryStyle = (cat: string) => {
        const c = cat.toUpperCase();
        if (c === 'DATA') return 'bg-orange-50 text-orange-600 border-orange-100';
        if (c === 'CODING') return 'bg-blue-50 text-blue-600 border-blue-100';
        if (c === 'RESEARCH') return 'bg-indigo-50 text-indigo-600 border-indigo-100';
        if (c === 'TOOLS') return 'bg-teal-50 text-teal-600 border-teal-100';
        return 'bg-gray-50 text-gray-600 border-gray-100';
    };

    return (
        <Link href={`/skills/${id}`} className="block h-full" aria-label={`${name} (${slug})`}>
            <article className="bg-white border border-gray-100 rounded-xl p-6 shadow-soft hover:shadow-hover hover:-translate-y-1 hover:bg-gray-50 transition-all duration-300 flex flex-col h-full group relative overflow-hidden">
                {/* Rank Badge - kept for ranking context, styled cleanly */}
                {rank && (
                    <div className="absolute top-0 right-0 bg-gray-900 text-white px-3 py-1 text-xs font-bold rounded-bl-xl shadow-sm z-10">
                        #{rank}
                    </div>
                )}

                <div className="flex justify-between items-start mb-4">
                    <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider border ${getCategoryStyle(category)}`}>
                        {category.toUpperCase()}
                    </span>
                </div>

                <h3 className="text-gray-900 font-bold mb-2 group-hover:text-gray-600 transition-colors text-lg line-clamp-2">
                    {name}
                </h3>

                <p className="text-sm mb-6 flex-1 line-clamp-2 text-gray-500 leading-relaxed">
                    {blurb}
                </p>

                <div className="flex items-center justify-between border-t border-gray-100 pt-4 text-xs text-gray-400 mt-auto">
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1.5 hover:text-gray-600 transition-colors">
                            <Star className="w-3.5 h-3.5" />
                            <span className="font-medium">{stars}</span>
                        </span>
                        <span className="flex items-center gap-1.5 hover:text-gray-600 transition-colors">
                            <Eye className="w-3.5 h-3.5" />
                            <span className="font-medium">{views}</span>
                        </span>
                    </div>
                    <div className="text-xs font-bold text-gray-900 flex items-center gap-1 hover:text-accent tracking-wider transition-colors">
                        DETAILS <ChevronRight className="w-2.5 h-2.5" />
                    </div>
                </div>
            </article>
        </Link>
    );
}
