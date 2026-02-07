import { api } from "@/app/lib/api";
import Link from "next/link";
import { Star, Eye, Trophy, ArrowRight } from "lucide-react";

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
        return await api.get<RankingItem[]>("/rankings/top10");
    } catch (e) {
        console.error(e);
        return [];
    }
}

export default async function RankingsPage() {
    const rankings = await getRankings();

    return (
        <div className="space-y-12 pb-20">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 tracking-tight mb-2">Rankings</h1>
                    <p className="text-gray-500 font-medium">
                        Top performing skills based on community engagement and usage.
                    </p>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-full shadow-sm text-sm font-bold text-gray-700">
                    <Trophy className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                    <span>Live Rankings</span>
                </div>
            </div>

            <div className="bg-white rounded-[24px] border border-gray-100 shadow-soft overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead>
                            <tr className="bg-gray-50/50 border-b border-gray-100 text-gray-400 text-xs font-bold uppercase tracking-wider">
                                <th className="px-6 py-4 font-bold">Rank</th>
                                <th className="px-6 py-4 font-bold w-full">Skill</th>
                                <th className="px-6 py-4 font-bold text-center whitespace-nowrap">Score</th>
                                <th className="px-6 py-4 font-bold text-center">Stars</th>
                                <th className="px-6 py-4 font-bold text-center">Views</th>
                                <th className="px-6 py-4 font-bold text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                            {rankings.length > 0 ? (
                                rankings.map((item, idx) => (
                                    <tr key={item.skill_id} className="group hover:bg-gray-50/80 transition-colors duration-200">
                                        <td className="px-6 py-4">
                                            <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold text-sm ${idx < 3 ? 'bg-black text-white shadow-md' : 'bg-gray-100 text-gray-500'}`}>
                                                {idx + 1}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <Link href={`/skills/${item.skill_id}`} className="block">
                                                <span className="font-bold text-lg text-gray-900 group-hover:text-gray-600 transition-colors block mb-0.5">
                                                    {item.name}
                                                </span>
                                                <span className="text-xs text-gray-400 font-mono">
                                                    {item.slug}
                                                </span>
                                            </Link>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="inline-flex items-center px-2.5 py-1 rounded-md bg-gray-50 border border-gray-100 text-gray-700 font-bold text-xs tabular-nums">
                                                {item.score.toFixed(1)}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="inline-flex items-center justify-center gap-1.5 font-medium text-gray-600 text-xs">
                                                <Star className="w-3.5 h-3.5 text-gray-300 group-hover:text-yellow-400 transition-colors" />
                                                <span className="tabular-nums font-bold">{item.stars}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="inline-flex items-center justify-center gap-1.5 font-medium text-gray-600 text-xs">
                                                <Eye className="w-3.5 h-3.5 text-gray-300 group-hover:text-blue-400 transition-colors" />
                                                <span className="tabular-nums font-bold">{item.views}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <Link
                                                href={`/skills/${item.skill_id}`}
                                                className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-white border border-gray-200 text-gray-400 hover:text-black hover:border-black transition-all shadow-sm hover:shadow"
                                            >
                                                <ArrowRight className="w-3.5 h-3.5" />
                                            </Link>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={6} className="px-8 py-24 text-center">
                                        <div className="flex flex-col items-center justify-center gap-3 text-gray-400">
                                            <Trophy className="w-8 h-8 opacity-20" />
                                            <p className="font-medium">No ranking data available yet.</p>
                                        </div>
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
