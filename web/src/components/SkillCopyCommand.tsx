"use client";

import { Check, Copy } from "lucide-react";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";

interface SkillCopyCommandProps {
    skillId: string;
    slug: string;
    installUrl?: string | null;
    sourceLinks?: Array<{ url?: string | null; external_id?: string | null }>;
}

type ClientKey = "claude" | "cursor" | "vscode" | "gemini";

interface EventTrackResponse {
    status: string;
    event_id: string;
    counted: boolean;
}

function getSessionId(): string {
    const key = "skill_session_id";
    const cached = localStorage.getItem(key);
    if (cached) return cached;
    const next = crypto.randomUUID();
    localStorage.setItem(key, next);
    return next;
}

function toSafeName(value: string): string {
    return value.replace(/[^a-zA-Z0-9_-]/g, "-");
}

function resolveSourceUrl(
    installUrl?: string | null,
    sourceLinks?: Array<{ url?: string | null; external_id?: string | null }>,
): string | null {
    if (installUrl && /^https?:\/\//i.test(installUrl)) {
        return installUrl;
    }
    for (const link of sourceLinks || []) {
        const candidate = link.url || link.external_id;
        if (candidate && /^https?:\/\//i.test(candidate)) {
            return candidate;
        }
    }
    return null;
}

function buildCommand(client: ClientKey, slug: string, sourceUrl: string | null): string {
    const safeSlug = toSafeName(slug || "skill");
    if (!sourceUrl) {
        return [
            "# Source URL is missing.",
            "# Open 'View Source / Deploy Docs' and copy the raw SKILL.md URL first.",
            "# Then re-open this page to generate an install command.",
        ].join("\n");
    }

    if (client === "claude") {
        return `mkdir -p ~/.claude/skills/${safeSlug} && curl -fsSL "${sourceUrl}" -o ~/.claude/skills/${safeSlug}/SKILL.md`;
    }
    if (client === "cursor") {
        return `mkdir -p ~/.cursor/skills/${safeSlug} && curl -fsSL "${sourceUrl}" -o ~/.cursor/skills/${safeSlug}/SKILL.md`;
    }
    if (client === "vscode") {
        return `mkdir -p .vscode/skills/${safeSlug} && curl -fsSL "${sourceUrl}" -o .vscode/skills/${safeSlug}/SKILL.md`;
    }
    return `mkdir -p ~/.gemini/skills/${safeSlug} && curl -fsSL "${sourceUrl}" -o ~/.gemini/skills/${safeSlug}/SKILL.md`;
}

export function SkillCopyCommand({ skillId, slug, installUrl, sourceLinks }: SkillCopyCommandProps) {
    const [copied, setCopied] = useState(false);
    const [copyFailed, setCopyFailed] = useState(false);
    const [activeClient, setActiveClient] = useState<ClientKey>("claude");
    const sourceUrl = useMemo(
        () => resolveSourceUrl(installUrl, sourceLinks),
        [installUrl, sourceLinks],
    );
    const command = useMemo(
        () => buildCommand(activeClient, slug, sourceUrl),
        [activeClient, slug, sourceUrl],
    );
    const runCommand = useMemo(() => `npx @coreline-ai/skill run ${slug}`, [slug]);

    const clients: Array<{ key: ClientKey; label: string }> = [
        { key: "claude", label: "Claude" },
        { key: "cursor", label: "Cursor" },
        { key: "vscode", label: "VSCode" },
        { key: "gemini", label: "Gemini" },
    ];

    const handleCopy = async () => {
        setCopyFailed(false);
        try {
            await navigator.clipboard.writeText(command);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
            await api.post<EventTrackResponse>("/events/use", {
                type: "use",
                skill_id: skillId,
                session_id: getSessionId(),
                source: "web",
                context: `snippet-copy:${activeClient}`,
            });
        } catch (err) {
            console.error("Failed to copy!", err);
            setCopyFailed(true);
            setTimeout(() => setCopyFailed(false), 2500);
        }
    };

    return (
        <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
                {clients.map((client) => (
                    <button
                        key={client.key}
                        type="button"
                        onClick={() => setActiveClient(client.key)}
                        className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all ${activeClient === client.key
                            ? "bg-blue-600 text-white shadow-sm"
                            : "bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-zinc-400 hover:bg-gray-200 dark:hover:bg-zinc-700"
                            }`}
                    >
                        {client.label}
                    </button>
                ))}
            </div>

            {!sourceUrl && (
                <p className="text-xs font-medium text-amber-700 dark:text-amber-300">
                    Source URL is required for install snippet generation. Use docs/source link first.
                </p>
            )}

            <div className="flex items-start gap-2">
                <pre className="flex-1 bg-black/5 dark:bg-white/5 px-3 py-2 rounded-lg font-mono text-xs text-blue-800 dark:text-blue-300 border border-blue-100 dark:border-blue-500/10 overflow-x-auto">
                    {command}
                </pre>
                <button
                    type="button"
                    onClick={handleCopy}
                    className={`p-2 rounded-lg transition-all shadow-sm shrink-0 flex items-center justify-center ${copied
                        ? "bg-emerald-500 text-white"
                        : copyFailed
                            ? "bg-red-600 text-white"
                            : "bg-blue-600 dark:bg-blue-500 text-white hover:bg-blue-700 active:scale-95"
                        }`}
                    title={copied ? "Copied!" : copyFailed ? "Copy failed" : "Copy to clipboard"}
                >
                    {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
            </div>

            <div className="pt-2 border-t border-blue-100 dark:border-blue-500/20">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-500 dark:text-zinc-500 mb-2">
                    Quick run (CLI)
                </p>
                <div className="flex items-start gap-2">
                    <code className="flex-1 bg-black/5 dark:bg-white/5 px-3 py-2 rounded-lg font-mono text-xs text-gray-700 dark:text-zinc-300 border border-gray-200 dark:border-white/10 overflow-x-auto whitespace-nowrap">
                        {runCommand}
                    </code>
                </div>
            </div>
        </div>
    );
}
