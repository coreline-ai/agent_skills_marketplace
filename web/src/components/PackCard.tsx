"use client";

import Link from "next/link";
import { FolderKanban, GitBranch, Layers } from "lucide-react";

export function PackCard(props: {
    id: string;
    repo_full_name: string;
    repo_url: string;
    skill_count: number;
    updated_at: string;
    dotclaude_skill_count?: number;
    skills_dir_skill_count?: number;
    description?: string | null;
}) {
    const dotclaude = props.dotclaude_skill_count ?? 0;
    const skillsDir = props.skills_dir_skill_count ?? 0;
    const updated = props.updated_at ? new Date(props.updated_at).toLocaleDateString() : "";

    return (
        <Link
            href={`/packs/${props.id}`}
            className="group block bg-white dark:bg-zinc-900/40 border border-gray-200 dark:border-zinc-800 rounded-2xl p-6 hover:shadow-md hover:-translate-y-0.5 transition-all"
        >
            <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                    <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-gray-400 dark:text-zinc-500">
                        <FolderKanban className="w-4 h-4" />
                        Skill Pack
                    </div>
                    <h3 className="mt-2 text-lg font-bold text-gray-900 dark:text-white truncate">
                        {props.repo_full_name}
                    </h3>
                    <p className="mt-1 text-xs text-gray-500 dark:text-zinc-500 truncate">
                        {props.repo_url.replace(/^https?:\/\//, "")}
                    </p>
                </div>

                <div className="shrink-0 text-right">
                    <div className="text-2xl font-black text-gray-900 dark:text-white">
                        {props.skill_count}
                    </div>
                    <div className="text-xs font-bold text-gray-500 dark:text-zinc-500">
                        skills
                    </div>
                </div>
            </div>

            {props.description && (
                <p className="mt-4 text-sm text-gray-600 dark:text-zinc-400 line-clamp-2">
                    {props.description}
                </p>
            )}

            <div className="mt-5 flex flex-wrap gap-2">
                <span className="inline-flex items-center gap-1 text-[11px] font-bold px-3 py-1 rounded-full bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-zinc-200">
                    <Layers className="w-3 h-3" />
                    skills/*: {skillsDir}
                </span>
                <span className="inline-flex items-center gap-1 text-[11px] font-bold px-3 py-1 rounded-full bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-zinc-200">
                    <GitBranch className="w-3 h-3" />
                    .claude: {dotclaude}
                </span>
                {updated && (
                    <span className="inline-flex items-center text-[11px] font-bold px-3 py-1 rounded-full bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-zinc-200">
                        updated {updated}
                    </span>
                )}
            </div>
        </Link>
    );
}

