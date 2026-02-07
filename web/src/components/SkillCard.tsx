import Link from "next/link";
import { Star, Eye, ArrowUpRight } from "lucide-react";

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
    return (
        <Link href={`/skills/${id}`} className="block group h-full" aria-label={`${name} (${slug})`}>
            <div className="h-full bg-background text-foreground rounded-lg border-2 border-main p-6 neo-shadow neo-shadow-hover relative overflow-hidden flex flex-col transition-all">
                {rank && (
                    <div className="absolute top-0 right-0 bg-accent text-black border-l-2 border-b-2 border-main px-4 py-2 font-black text-lg z-10">
                        #{rank}
                    </div>
                )}

                <div className="mb-4 pt-2">
                    <span className="inline-block px-3 py-1 text-xs font-bold uppercase tracking-wider bg-invert mb-3 border border-main">
                        {category}
                    </span>
                    <h3 className="text-2xl font-extrabold group-hover:underline decoration-2 decoration-accent underline-offset-4 line-clamp-2">
                        {name}
                    </h3>
                </div>

                <p className="text-foreground/80 text-sm font-medium mb-6 line-clamp-3 leading-relaxed flex-grow">
                    {blurb}
                </p>

                <div className="flex items-center justify-between text-sm font-bold pt-4 border-t-2 border-main mt-auto">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1.5">
                            <Star className="w-5 h-5 fill-current" />
                            <span>{stars}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                            <Eye className="w-5 h-5" />
                            <span>{views}</span>
                        </div>
                    </div>
                    <div className="flex items-center gap-1 group-hover:translate-x-1 transition-transform">
                        <span>Details</span>
                        <ArrowUpRight className="w-4 h-4" />
                    </div>
                </div>
            </div>
        </Link>
    );
}
