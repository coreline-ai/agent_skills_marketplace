import Link from "next/link";
import { Star, Eye } from "lucide-react";

interface SkillCardProps {
    id: string;
    name: string;
    slug: string;
    description: string;
    category: string;
    views: number;
    stars: number;
    score: number;
    rank?: number;
}

export function SkillCard({ id, name, slug, description, category, views, stars, rank }: SkillCardProps) {
    return (
        <Link href={`/skills/${id}`} className="block group" aria-label={`${name} (${slug})`}>
            <div className="h-full bg-white rounded-2xl border border-gray-100 p-6 shadow-sm hover:shadow-xl hover:border-blue-100 hover:-translate-y-1 transition-all duration-300 relative overflow-hidden flex flex-col">
                {rank && (
                    <div className="absolute top-0 right-0 bg-blue-600 text-white px-3 py-1 rounded-bl-xl font-bold text-sm shadow-sm">
                        #{rank}
                    </div>
                )}
                <div className="mb-4">
                    <span className="inline-block px-3 py-1 text-xs font-semibold text-blue-700 bg-blue-50 rounded-full mb-3">
                        {category}
                    </span>
                    <h3 className="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                        {name}
                    </h3>
                </div>
                <p className="text-gray-600 text-sm mb-6 line-clamp-2 leading-relaxed flex-grow">
                    {description}
                </p>
                <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t border-gray-50">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1.5">
                            <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                            <span className="font-medium text-gray-700">{stars}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <Eye className="w-4 h-4 text-gray-400" />
                            <span className="font-medium text-gray-700">{views}</span>
                        </div>
                    </div>
                    <span className="text-xs font-medium text-blue-600 group-hover:underline">View Details</span>
                </div>
            </div>
        </Link>
    );
}
