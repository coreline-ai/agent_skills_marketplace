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
        <Link href={`/skills/${id}`} className="block group">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden">
                {rank && (
                    <div className="absolute top-0 right-0 bg-blue-600 text-white px-3 py-1 rounded-bl-xl font-bold text-sm">
                        #{rank}
                    </div>
                )}
                <div className="mb-2">
                    <span className="inline-block px-2 py-1 text-xs font-semibold text-blue-600 bg-blue-50 rounded-full mb-2">
                        {category}
                    </span>
                    <h3 className="text-lg font-bold text-gray-900 group-hover:text-blue-600 transition-colors line-clamp-1">
                        {name}
                    </h3>
                </div>
                <p className="text-gray-600 text-sm mb-4 line-clamp-2 h-10">
                    {description}
                </p>
                <div className="flex items-center gap-4 text-sm text-gray-500">
                    <div className="flex items-center gap-1">
                        <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                        <span>{stars}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <Eye className="w-4 h-4" />
                        <span>{views}</span>
                    </div>
                </div>
            </div>
        </Link>
    );
}
