export const metadata = {
  title: "Guide | Agent Skills Marketplace",
  description: "How Skills work and how to create high-quality SKILL.md-based skills.",
};

export default function GuidePage() {
  return (
    <div className="space-y-10">
      <header className="space-y-3 border-b-4 border-black pb-6">
        <h1 className="text-4xl sm:text-5xl font-black tracking-tight">Guide</h1>
        <p className="text-black/80 dark:text-white/80 font-medium max-w-3xl">
          This marketplace is intentionally strict: we only index repositories that publish Skills as canonical{" "}
          <span className="font-black">SKILL.md</span> files under <span className="font-mono">skills/*/SKILL.md</span>{" "}
          or <span className="font-mono">.claude/skills/*/SKILL.md</span>. That is how we avoid “random OSS repos” and
          keep the catalog useful.
        </p>
      </header>

      <section className="space-y-3">
        <h2 className="text-2xl font-black">What Are Skills?</h2>
        <p className="text-black/80 dark:text-white/80 font-medium leading-relaxed">
          A Skill is a reusable, installable capability for an agent. In this project, a Skill is defined by a single
          SKILL.md document (with YAML frontmatter + body) stored in a canonical folder layout.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl font-black">Creating Skills</h2>
        <p className="text-black/80 dark:text-white/80 font-medium leading-relaxed">
          Create a public GitHub repository that is dedicated to Skills (recommended), then add one or more SKILL.md
          files using one of the canonical layouts below.
        </p>
        <div className="bg-white dark:bg-black border-2 border-black p-4 rounded-lg neo-shadow">
          <pre className="text-sm font-mono whitespace-pre-wrap">
{`skills/my-skill/SKILL.md
.claude/skills/my-skill/SKILL.md`}
          </pre>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl font-black">Writing SKILL.md</h2>
        <p className="text-black/80 dark:text-white/80 font-medium leading-relaxed">
          We parse YAML frontmatter and validate a small set of quality rules so broken or incomplete docs do not enter
          the public catalog.
        </p>
        <div className="bg-white dark:bg-black border-2 border-black p-4 rounded-lg neo-shadow">
          <pre className="text-sm font-mono whitespace-pre-wrap">
{`---
name: My Skill
description: One-line description that explains what the skill does.
category: Tools
---

## Overview
Explain what it does, inputs/outputs, and how to use it.`}
          </pre>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl font-black">Advanced Features</h2>
        <p className="text-black/80 dark:text-white/80 font-medium leading-relaxed">
          Add concrete examples, constraints, and triggers in a consistent format. The goal is to make Skills searchable,
          comparable, and safe to reuse.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl font-black">Testing &amp; Debugging</h2>
        <p className="text-black/80 dark:text-white/80 font-medium leading-relaxed">
          If your Skill is not showing up, the most common reasons are:
        </p>
        <ul className="list-disc pl-5 space-y-1 text-black/80 dark:text-white/80 font-medium">
          <li>Not using the canonical path (<span className="font-mono">skills/*/SKILL.md</span> or <span className="font-mono">.claude/skills/*/SKILL.md</span>).</li>
          <li>Broken YAML frontmatter.</li>
          <li>Missing or too-short description.</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl font-black">Collections (Planned)</h2>
        <p className="text-black/80 dark:text-white/80 font-medium leading-relaxed">
          We plan to support “Collections” (curated sets of Skills) so teams can share a bundle that works well together.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-2xl font-black">Using With Claude Code</h2>
        <p className="text-black/80 dark:text-white/80 font-medium leading-relaxed">
          This marketplace is designed around SKILL.md-based workflows, and will keep prioritizing canonical layouts and
          repository intent detection to stay Skills-only.
        </p>
      </section>
    </div>
  );
}

