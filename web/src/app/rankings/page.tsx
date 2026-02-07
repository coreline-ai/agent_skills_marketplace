import { api } from "@/app/lib/api";
import Link from "next/link";
import { Star, Eye, Trophy } from "lucide-react";

export const dynamic = 'force-dynamic';

interface RankingItem {
    rank: number;
    skill_id: string;
    slug: string;
    name: string;
    score: number;
    views: number;
    stars: number;
}

async function getRankings() {
    try {
        // Adjust endpoint if needed. Assuming /rankings/top10 OR /rankings/weekly
        return await api.get<RankingItem[]>("/rankings/top10");
    } catch (e) {
        console.error(e);
        return [];
    }
}

export default async function RankingsPage() {
    const rankings = await getRankings();

    return (
        <div className="max-w-5xl mx-auto space-y-8">
            <div className="text-center py-10">
                <h1 className="text-4xl font-black text-black dark:text-white mb-4 uppercase tracking-tight">Global Leaderboard</h1>
                <p className="text-xl text-gray-800 dark:text-white/80 max-w-2xl mx-auto font-medium">
                    Top performing skills based on community engagement, quality, and usage.
                </p>
            </div>

            <div className="bg-background text-foreground border-2 border-main p-6 sm:p-10 mb-12 neo-shadow">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
                    <div>
                        <h1 className="text-4xl sm:text-5xl font-black mb-4 uppercase tracking-tight">Leaderboard</h1>
                        <p className="text-foreground/70 font-bold text-lg">Top performing skills across the ecosystem</p>
                    </div>
                    <div className="flex items-center gap-3 bg-accent p-2 border-2 border-black text-black">
                        <Trophy className="w-8 h-8 fill-black" />
                        <span className="text-2xl font-black">#Global</span>
                    </div>
                </div>

                <div className="overflow-x-auto border-2 border-main">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b-4 border-main bg-invert uppercase font-black text-sm">
                                <th className="px-6 py-4">Rank</th>
                                <th className="px-6 py-4">Skill</th>
                                <th className="px-6 py-4 text-center">Popularity Score</th>
                                <th className="px-6 py-4 text-center">Stars</th>
                                <th className="px-6 py-4 text-center">Views</th>
                                <th className="px-6 py-4 text-center">Action</th>
                            </tr>
                        </thead>
                        <tbody className="font-bold divide-y-2 divide-main">
                            {rankings.length > 0 ? (
                                rankings.map((item, idx) => (
                                    <tr key={item.skill_id} className="border-b-2 border-main hover:bg-accent/10 transition-colors">
                                        <td className="px-6 py-4">
                                            <span className={`inline-block w-8 h-8 rounded-none border-2 border-main flex items-center justify-center ${idx < 3 ? 'bg-accent text-black font-black' : 'bg-background text-foreground'}`}>
                                                {idx + 1}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <Link href={`/skills/${item.skill_id}`} className="font-bold text-lg hover:underline decoration-2 decoration-accent underline-offset-4">
                                                {item.name}
                                            </Link>
                                        </td>
                                        <td className="px-6 py-4 text-center font-bold text-lg">
                                            {item.score.toFixed(1)}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="inline-flex items-center gap-1 font-bold">
                                                <Eye className="w-5 h-5" />
                                                {item.views}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="inline-flex items-center gap-1 font-bold">
                                                <Star className="w-5 h-5 fill-current" />
                                                {item.stars}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <Link href={`/skills/${item.skill_id}`} className="inline-block px-3 py-1 bg-invert text-xs font-bold border-2 border-main rounded hover:bg-accent hover:text-black transition-colors">
                                                VIEW
                                            </Link>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-foreground/50 font-bold">
                                        No ranking data available.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
