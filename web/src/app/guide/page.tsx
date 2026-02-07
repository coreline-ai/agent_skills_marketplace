export const metadata = {
  title: "Guide | Agent Skills Marketplace",
  description: "How Skills work and how to create high-quality SKILL.md-based skills.",
};

export default function GuidePage() {
  return (
    <div className="space-y-8 pb-20 max-w-4xl">
      <header className="space-y-4 border-b border-gray-100 dark:border-white/5 pb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white tracking-tight">User Guide</h1>
        <p className="text-base text-gray-600 dark:text-zinc-400 max-w-2xl leading-relaxed font-medium">
          This marketplace is intentionally strict: we only index repositories that publish Skills as canonical{" "}
          <span className="font-bold text-gray-900 dark:text-white">SKILL.md</span> files under <span className="font-mono text-xs bg-gray-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded text-gray-800 dark:text-zinc-300 mx-1">skills/*/SKILL.md</span>{" "}
          or <span className="font-mono text-xs bg-gray-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded text-gray-800 dark:text-zinc-300 mx-1">.claude/skills/*/SKILL.md</span>. That is how we avoid “random OSS repos” and
          keep the catalog useful.
        </p>
      </header>

      <div className="grid gap-8">
        <section className="bg-white dark:bg-card p-8 rounded-[24px] border border-gray-100 dark:border-white/10 shadow-sm hover:shadow-md transition-shadow duration-300">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-xl">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-book-open"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" /></svg>
            </div>
            <div className="space-y-3 flex-1">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">What Are Skills?</h2>
              <p className="text-base text-gray-600 dark:text-zinc-400 leading-relaxed font-medium">
                A Skill is a reusable, installable capability for an agent. In this project, a Skill is defined by a single
                SKILL.md document (with YAML frontmatter + body) stored in a canonical folder layout.
              </p>
            </div>
          </div>
        </section>

        <section className="bg-white dark:bg-card p-8 rounded-[24px] border border-gray-100 dark:border-white/10 shadow-sm hover:shadow-md transition-shadow duration-300">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-xl">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-folder-plus"><path d="M12 10v6" /><path d="M9 13h6" /><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z" /></svg>
            </div>
            <div className="space-y-4 flex-1">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Creating Skills</h2>
              <p className="text-base text-gray-600 dark:text-zinc-400 leading-relaxed font-medium">
                Create a public GitHub repository that is dedicated to Skills (recommended), then add one or more SKILL.md
                files using one of the canonical layouts below.
              </p>
              <div className="bg-gray-50 dark:bg-black border border-gray-200 dark:border-white/10 p-5 rounded-xl overflow-x-auto">
                <pre className="text-sm font-mono text-gray-800 dark:text-gray-300 whitespace-pre-wrap">
                  {`skills/my-skill/SKILL.md
.claude/skills/my-skill/SKILL.md`}
                </pre>
              </div>
            </div>
          </div>
        </section>

        <section className="bg-white dark:bg-card p-8 rounded-[24px] border border-gray-100 dark:border-white/10 shadow-sm hover:shadow-md transition-shadow duration-300">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-green-50 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-xl">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-file-text"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" /><path d="M14 2v4a2 2 0 0 0 2 2h4" /><path d="M10 9H8" /><path d="M16 13H8" /><path d="M16 17H8" /></svg>
            </div>
            <div className="space-y-4 flex-1">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Writing SKILL.md</h2>
              <p className="text-base text-gray-600 dark:text-zinc-400 leading-relaxed font-medium">
                We parse YAML frontmatter and validate a small set of quality rules so broken or incomplete docs do not enter
                the public catalog.
              </p>
              <div className="bg-gray-50 dark:bg-black border border-gray-200 dark:border-white/10 p-5 rounded-xl overflow-x-auto">
                <pre className="text-sm font-mono text-gray-800 dark:text-gray-300 whitespace-pre-wrap">
                  {`---
name: My Skill
description: One-line description that explains what the skill does.
category: Tools
---

## Overview
Explain what it does, inputs/outputs, and how to use it.`}
                </pre>
              </div>
            </div>
          </div>
        </section>

        <div className="grid md:grid-cols-2 gap-8">
          <section className="bg-white dark:bg-card p-8 rounded-[24px] border border-gray-100 dark:border-white/10 shadow-sm hover:shadow-md transition-shadow duration-300">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-sparkles text-yellow-500"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275Z" /></svg>
              Advanced Features
            </h2>
            <p className="text-gray-600 dark:text-zinc-400 leading-relaxed text-sm font-medium">
              Add concrete examples, constraints, and triggers in a consistent format. The goal is to make Skills searchable,
              comparable, and safe to reuse.
            </p>
          </section>

          <section className="bg-white dark:bg-card p-8 rounded-[24px] border border-gray-100 dark:border-white/10 shadow-sm hover:shadow-md transition-shadow duration-300">
            <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-layers text-indigo-500"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z" /><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65" /><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65" /></svg>
              Collections (Planned)
            </h2>
            <p className="text-gray-600 dark:text-zinc-400 leading-relaxed text-sm font-medium">
              We plan to support “Collections” (curated sets of Skills) so teams can share a bundle that works well together.
            </p>
          </section>
        </div>

        <section className="bg-red-50/50 dark:bg-red-900/10 p-8 rounded-[24px] border border-red-100/50 dark:border-red-500/20">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-white dark:bg-red-900/20 text-red-500 rounded-xl shadow-sm border border-red-100 dark:border-red-500/30">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-alert-circle"><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></svg>
            </div>
            <div className="space-y-4 flex-1">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Troubleshooting</h2>
              <p className="text-base text-gray-600 dark:text-zinc-400 leading-relaxed font-medium">
                If your Skill is not showing up, check these common issues:
              </p>
              <ul className="space-y-2">
                <li className="flex items-center gap-3 text-sm text-gray-700 dark:text-zinc-300 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                  <span>Not using the canonical path (<span className="font-mono text-gray-500 dark:text-zinc-500 text-xs bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 px-1 py-0.5 rounded">skills/*/SKILL.md</span>)</span>
                </li>
                <li className="flex items-center gap-3 text-sm text-gray-700 dark:text-zinc-300 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                  <span>Broken or missing YAML frontmatter</span>
                </li>
                <li className="flex items-center gap-3 text-sm text-gray-700 dark:text-zinc-300 font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-red-400"></span>
                  <span>Missing description field</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

      </div>
    </div>
  );
}
