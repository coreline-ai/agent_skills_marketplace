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
    githubStars?: number | null;
    githubUpdatedAt?: string | null;
    matchReason?: string | null;
    trustScore?: number | null;
    trustLevel?: string | null;
    trustFlags?: string[] | null;
}

export function SkillCard({
    id,
    name,
    slug,
    description,
    summary,
    category,
    views,
    stars,
    rank,
    githubStars,
    githubUpdatedAt,
    matchReason,
    trustScore,
    trustLevel,
    trustFlags,
}: SkillCardProps) {
    const blurb = (summary && summary.trim()) ? summary : description;

    // Category tag style mapping based on code.html design
    const getCategoryStyle = (cat: string) => {
        const c = cat.toUpperCase();
        if (c === 'DATA') return 'bg-orange-50 text-orange-600 border-orange-100 dark:bg-[#5c4033] dark:text-[#ebdec2] dark:border-transparent';
        if (c === 'CODING') return 'bg-blue-50 text-blue-600 border-blue-100 dark:bg-zinc-800 dark:text-zinc-300 dark:border-transparent';
        if (c === 'RESEARCH') return 'bg-indigo-50 text-indigo-600 border-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-transparent';
        if (c === 'TOOLS') return 'bg-teal-50 text-teal-600 border-teal-100 dark:bg-teal-900/30 dark:text-teal-300 dark:border-transparent';
        return 'bg-gray-50 text-gray-600 border-gray-100 dark:bg-zinc-800 dark:text-zinc-400 dark:border-transparent';
    };

    return (
        <Link href={`/skills/${id}`} className="block h-full" aria-label={`${name} (${slug})`}>
            <article className="bg-white dark:bg-card border border-gray-100 dark:border-white/10 rounded-xl p-6 shadow-soft hover:shadow-hover hover:-translate-y-1 hover:bg-gray-50 dark:hover:bg-white/5 transition-all duration-300 flex flex-col h-full group relative overflow-hidden">
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

                <h3 className="text-gray-900 dark:text-white font-bold mb-2 group-hover:text-accent transition-colors text-lg line-clamp-2">
                    {name}
                </h3>

                <p className="text-sm mb-6 flex-1 line-clamp-2 text-gray-500 dark:text-gray-400 leading-relaxed">
                    {blurb}
                </p>

                {matchReason && (
                    <div className="mb-4 text-[11px] font-semibold uppercase tracking-wide text-accent">
                        {matchReason}
                    </div>
                )}
                {trustLevel && (
                    <div
                        className={`mb-4 inline-flex items-center gap-1 px-2 py-1 rounded border text-[10px] font-bold uppercase tracking-wide w-fit ${trustLevel === "ok"
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-300 dark:border-emerald-500/30"
                                : trustLevel === "warning"
                                    ? "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/20 dark:text-amber-300 dark:border-amber-500/30"
                                    : "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-900/20 dark:text-rose-300 dark:border-rose-500/30"
                            }`}
                        title={trustFlags && trustFlags.length > 0 ? trustFlags.join(", ") : "Trust score"}
                    >
                        Trust {trustScore !== undefined && trustScore !== null ? Math.round(trustScore) : "-"}
                    </div>
                )}

                <div className="flex items-center justify-between border-t border-gray-100 dark:border-white/10 pt-4 text-xs text-gray-400 dark:text-gray-500 mt-auto">
                    <div className="flex items-center gap-4">
                        <span className="flex items-center gap-1.5 hover:text-gray-600 transition-colors">
                            <Star className="w-3.5 h-3.5" />
                            <span className="font-medium">{stars}</span>
                        </span>
                        <span className="flex items-center gap-1.5 hover:text-gray-600 transition-colors">
                            <Eye className="w-3.5 h-3.5" />
                            <span className="font-medium">{views}</span>
                        </span>
                        {githubStars !== undefined && githubStars !== null && (
                            <span className="flex items-center gap-1.5 text-orange-500 font-bold">
                                <Star className="w-3.5 h-3.5 fill-current" />
                                <span>{githubStars}</span>
                            </span>
                        )}
                        {githubUpdatedAt && (
                            <span className="text-[10px] text-gray-400 dark:text-zinc-600">
                                {new Date(githubUpdatedAt).toLocaleDateString()}
                            </span>
                        )}
                    </div>
                    <div className="text-xs font-bold text-gray-900 dark:text-white flex items-center gap-1 hover:text-accent tracking-wider transition-colors">
                        DETAILS <ChevronRight className="w-2.5 h-2.5" />
                    </div>
                </div>
            </article>
        </Link>
    );
}
