import { api } from "@/app/lib/api";
import Link from "next/link";
import { Star, Eye } from "lucide-react";

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
                <h1 className="text-3xl font-bold text-gray-900 mb-4">Global Leaderboard</h1>
                <p className="text-gray-600 max-w-2xl mx-auto">
                    Top performing skills based on community engagement, quality, and usage.
                </p>
            </div>

            <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm text-gray-600">
                        <thead className="bg-gray-50 border-b border-gray-200 text-xs uppercase font-semibold text-gray-500">
                            <tr>
                                <th className="px-6 py-4 w-16 text-center">Rank</th>
                                <th className="px-6 py-4">Skill</th>
                                <th className="px-6 py-4 text-center">Popularity Score</th>
                                <th className="px-6 py-4 text-center">Views</th>
                                <th className="px-6 py-4 text-center">Stars</th>
                                <th className="px-6 py-4 text-center">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-100">
                            {rankings.length > 0 ? (
                                rankings.map((item, index) => (
                                    <tr key={item.skill_id} className="hover:bg-gray-50 transition-colors">
                                        <td className="px-6 py-4 text-center">
                                            <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full font-bold ${index < 3 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'
                                                }`}>
                                                {index + 1}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <Link href={`/skills/${item.skill_id}`} className="font-semibold text-gray-900 hover:text-blue-600">
                                                {item.name}
                                            </Link>
                                        </td>
                                        <td className="px-6 py-4 text-center font-medium text-blue-600">
                                            {item.score.toFixed(1)}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="inline-flex items-center gap-1">
                                                <Eye className="w-4 h-4 text-gray-400" />
                                                {item.views}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="inline-flex items-center gap-1">
                                                <Star className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                                                {item.stars}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <Link href={`/skills/${item.skill_id}`} className="text-blue-600 hover:underline text-xs font-semibold">
                                                View
                                            </Link>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
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
