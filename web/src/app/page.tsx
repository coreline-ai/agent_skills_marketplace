import { api } from "@/app/lib/api";
import { SkillCard } from "@/components/SkillCard";
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
    <div className="space-y-20">
      <section className="relative py-20 px-4 text-center neo-container !shadow-none rounded-xl overflow-hidden">
        <div className="absolute inset-0 bg-grid opacity-20 pointer-events-none"></div>
        <div className="relative z-10 space-y-8 max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-invert rounded-full font-bold text-sm border-2 border-main">
            <Sparkles className="w-4 h-4 text-accent dark:text-background" />
            <span>The Marketplace for AI Minds</span>
          </div>

          <h1 className="text-5xl sm:text-7xl font-black text-foreground tracking-tight leading-tight uppercase">
            Supercharge Your <br />
            <span className="bg-accent px-2 decoration-slice text-black">AI Agents</span>
          </h1>

          <p className="text-xl sm:text-2xl text-foreground/80 font-medium max-w-2xl mx-auto leading-relaxed">
            Discover, integrate, and deploy high-quality skills. <br className="hidden sm:block" />
            Community-driven, verified, and ready to run.
          </p>

          <div className="pt-6 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/skills" className="px-8 py-4 bg-invert text-lg font-bold border-2 border-main rounded-lg !shadow-none hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[4px_4px_0px_0px_var(--foreground)] transition-all active:translate-x-[4px] active:translate-y-[4px] active:shadow-none">
              Browse Skills library
            </Link>
            <Link href="/rankings" className="px-8 py-4 bg-background text-foreground text-lg font-bold border-2 border-main rounded-lg hover:bg-accent hover:text-black hover:translate-x-[1px] hover:translate-y-[1px] transition-all">
              View Leaderboard
            </Link>
          </div>
        </div>
      </section>

      {/* Top 10 Section */}
      <section className="space-y-8">
        <div className="flex items-center justify-between border-b-4 border-main pb-4">
          <h2 className="text-3xl font-black text-foreground uppercase tracking-wide">
            Top Trending Skills
          </h2>
          <Link href="/rankings" className="group font-bold text-lg flex items-center gap-2 hover:underline decoration-2 underline-offset-4 decoration-accent">
            See All <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {displaySkills.length === 0 ? (
          <div className="text-center py-20 bg-gray-50 border-2 border-dashed border-black rounded-lg">
            <p className="text-xl font-bold text-gray-500">No rankings available yet. Be the first to add a skill!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {displaySkills.map((skill) => (
              <SkillCard key={skill.skill_id} {...skill} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
