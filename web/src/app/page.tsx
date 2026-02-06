import { api } from "@/app/lib/api";
import { SkillCard } from "@/components/SkillCard";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

interface RankingItem {
  rank: number;
  skill_id: string;
  slug: string;
  name: string;
  score: number;
  views: number;
  stars: number;
  description?: string;
  category?: string;
}

// Force dynamic to resolve API at runtime (Docker networking)
export const dynamic = 'force-dynamic';

async function getTopSkills() {
  try {
    // In a real server component, we can use fetch directly with full URL
    // But we are using a helper that uses process.env
    // Server components can use full URL env var
    const res = await api.get<RankingItem[]>("/rankings/top10");
    return res;
  } catch (e) {
    console.error(e);
    return [];
  }
}

export default async function Home() {
  const topSkills = await getTopSkills();

  const displaySkills = topSkills.map(s => ({
    ...s,
    id: s.skill_id,
    description: s.description || "No description provided.",
    category: s.category || "Uncategorized",
  }));

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <section className="text-center space-y-4 py-12">
        <h1 className="text-4xl sm:text-5xl font-extrabold text-gray-900 tracking-tight">
          Find the Best <span className="text-blue-600">AI Agent Skills</span>
        </h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Discover, share, and integrate high-quality skills for your autonomous agents.
          Community-driven, verified, and ready to use.
        </p>
        <div className="pt-4">
          <Link href="/skills" className="inline-flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors">
            Browse All Skills
          </Link>
        </div>
      </section>

      {/* Top 10 Section */}
      <section>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Top 10 Trending Skills</h2>
          <Link href="/rankings" className="text-blue-600 hover:text-blue-700 font-medium flex items-center gap-1">
            View Leaderboard <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {displaySkills.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
            <p className="text-gray-500">No rankings available yet. Be the first to add a skill!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {displaySkills.map((skill) => (
              <SkillCard key={skill.skill_id} {...skill} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
