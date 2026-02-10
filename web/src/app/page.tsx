import { api } from "@/lib/api";
import { SkillCard } from "@/components/SkillCard";
import { HeroRobot } from "@/components/HeroRobot";
import Link from "next/link";
import { ArrowRight, Sparkles } from "lucide-react";

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
      <section className="relative rounded-[20px] hero-border overflow-hidden mb-12 bg-gray-50/50 dark:bg-black" data-purpose="hero-banner">
        <div className="absolute inset-0 dot-pattern pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between p-8 md:p-12 gap-8">
          <div className="flex-1 space-y-6 max-w-2xl">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-[20px] bg-white dark:bg-white/10 text-gray-700 dark:text-gray-300 text-[10px] font-bold tracking-[1px] uppercase border border-gray-200 dark:border-white/10 shadow-sm">
              <Sparkles className="w-3 h-3 text-accent" />
              THE MARKETPLACE FOR AI MINDS
            </span>
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white leading-tight">
              Unlock Your AI{"'"}s <br /> Agent <span className="text-transparent bg-clip-text bg-gradient-to-r from-gray-900 to-gray-500 dark:from-white dark:to-zinc-500">Skills</span>
            </h1>
            <p className="text-gray-600 dark:text-zinc-400 text-lg leading-relaxed max-w-lg">
              Discover, integrate, and deploy high-quality skills. Community-driven, verified, and ready to run.
            </p>
            <div className="flex flex-wrap gap-4 pt-2">
              <Link href="/skills" className="px-6 py-3 bg-gray-900 dark:bg-white text-white dark:text-black border border-gray-900 dark:border-white font-medium rounded-full hover:bg-gray-800 dark:hover:bg-zinc-200 hover:shadow-lg transition-all text-sm mr-2">
                Browse Skills Lib
              </Link>
              <Link href="/rankings" className="px-6 py-3 border border-gray-300 dark:border-zinc-800 bg-white dark:bg-transparent text-gray-700 dark:text-white font-medium rounded-full hover:border-gray-400 dark:hover:border-zinc-700 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors text-sm">
                View Leaderboard
              </Link>
            </div>
          </div>
          <div className="w-full max-w-[320px] md:max-w-[400px] flex-shrink-0 relative">
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[80%] bg-blue-100/60 dark:bg-accent/20 blur-[60px] dark:blur-[100px] rounded-full pointer-events-none"></div>
            <HeroRobot />
          </div>
        </div>
      </section>

      <section data-purpose="trending-skills">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">Trending Skills</h2>
          <Link href="/skills" className="text-[0.9rem] text-gray-500 dark:text-zinc-500 hover:text-accent transition-colors flex items-center gap-1 group">
            See All
            <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {displaySkills.length === 0 ? (
          <div className="text-center py-20 bg-gray-50 dark:bg-zinc-900/40 border-2 border-dashed border-gray-200 dark:border-zinc-800 rounded-xl">
            <p className="text-lg font-medium text-gray-500 dark:text-zinc-500">No rankings available yet.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {displaySkills.map((skill, index) => {
              const { rank: _, ...rest } = skill;
              return <SkillCard key={skill.skill_id} rank={index + 1} {...rest} />;
            })}
          </div>
        )}
      </section>
    </div>
  );
}
