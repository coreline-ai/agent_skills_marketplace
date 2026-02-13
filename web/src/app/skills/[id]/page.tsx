import { api } from "@/lib/api";
import Link from "next/link";
import { ArrowLeft, ExternalLink, Box, Tag, Layers, FileText, Code, Globe, User, Calendar, Shield, Star } from "lucide-react";
import { SkillHeaderEngagement } from "@/components/SkillHeaderEngagement";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SkillCopyCommand } from "@/components/SkillCopyCommand";

interface SkillDetailProps {
    params: Promise<{ id: string }>;
}

interface SkillTag {
    slug: string;
    name: string;
}

interface SkillSourceLink {
    link_type: string;
    url?: string | null;
    external_id?: string | null;
}

interface SkillDetail {
    id: string;
    name: string;
    slug: string;
    description?: string | null;
    summary?: string | null;
    overview?: string | null;
    content?: string | null;
    is_official: boolean;
    category?: { id?: string; name?: string; slug?: string } | null;
    stars: number;
    views: number;
    author?: string | null;
    updated_at: string;
    tags?: SkillTag[];
    source_links?: SkillSourceLink[];
    url?: string | null;
    inputs?: Record<string, unknown> | null;
    outputs?: Record<string, unknown> | null;
    spec?: Record<string, unknown> | null;
    use_cases?: string[] | null;
    github_stars?: number | null;
    github_updated_at?: string | null;
    quality_score?: number | null;
    trust_score?: number | null;
    trust_level?: string | null;
    trust_flags?: string[] | null;
    trust_last_verified_at?: string | null;
}

// Ensure dynamic rendering
export const dynamic = 'force-dynamic';

async function getSkill(id: string) {
    try {
        return await api.get<SkillDetail>(`/skills/${id}`, undefined, { revalidateSeconds: 60 });
    } catch {
        return null;
    }
}

// SEO Metadata
export async function generateMetadata(props: SkillDetailProps) {
    const params = await props.params;
    const skill = await getSkill(params.id);

    if (!skill) {
        return {
            title: "Skill Not Found",
        };
    }

    return {
        title: `${skill.name} - Agent Skill | Coreline Marketplace`,
        description: skill.summary || skill.description?.slice(0, 160),
        openGraph: {
            title: `${skill.name} - Agent Skill`,
            description: skill.summary || skill.description?.slice(0, 160),
            type: "article",
            images: [
                {
                    url: `/api/og?title=${encodeURIComponent(skill.name)}&category=${encodeURIComponent(skill.category?.name || "Uncategorized")}`,
                    width: 1200,
                    height: 630,
                },
            ],
        },
        twitter: {
            card: "summary_large_image",
            title: skill.name,
            description: skill.summary || skill.description?.slice(0, 160),
        },
    };
}

export default async function SkillDetailPage(props: SkillDetailProps) {
    const params = await props.params;
    const skill = await getSkill(params.id);

    if (!skill) {
        return (
            <div className="text-center py-20 bg-gray-50 dark:bg-zinc-900/40 rounded-[24px] border border-gray-200 dark:border-zinc-800">
                <h1 className="text-2xl font-black text-gray-900 dark:text-white mb-2">Skill not found</h1>
                <p className="text-gray-500 dark:text-zinc-500 mb-6">The skill you are looking for does not exist or has been removed.</p>
                <Link href="/skills" className="px-6 py-2 bg-black dark:bg-white text-white dark:text-black rounded-full font-bold hover:bg-gray-800 dark:hover:bg-zinc-200 transition-colors inline-block">
                    Back to Skills
                </Link>
            </div>
        );
    }

    const installUrl = skill.url || null;
    const sourceUrlCandidates = (skill.source_links || [])
        .map((link) => link.url || link.external_id || null)
        .filter((value): value is string => Boolean(value));
    const primarySourceUrl = installUrl || sourceUrlCandidates[0] || null;
    const skillInterface = {
        inputs: skill.inputs,
        outputs: skill.outputs,
    };
    const spec = skill.spec || null;
    const allowedTools = Array.isArray(spec?.["allowed-tools"])
        ? (spec?.["allowed-tools"] as unknown[]).filter((v) => typeof v === "string") as string[]
        : [];
    const userInvocable = typeof spec?.["user-invocable"] === "boolean" ? (spec?.["user-invocable"] as boolean) : null;
    const disableModelInvocation =
        typeof spec?.["disable-model-invocation"] === "boolean" ? (spec?.["disable-model-invocation"] as boolean) : null;

    return (
        <div className="max-w-5xl mx-auto space-y-8 pb-12">
            <Link href="/skills" className="inline-flex items-center text-sm font-bold text-gray-500 dark:text-zinc-500 hover:text-black dark:hover:text-white transition-colors group">
                <ArrowLeft className="w-4 h-4 mr-1 group-hover:-translate-x-1 transition-transform" /> Back to Skills
            </Link>

            {/* Header */}
            <div className="bg-white dark:bg-card border border-gray-100 dark:border-white/10 rounded-2xl p-8 md:p-10 shadow-sm relative overflow-hidden">
                <div className="relative z-10 flex flex-col md:flex-row items-start justify-between gap-6">
                    <div className="space-y-4 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                            {skill.category ? (
                                <span className="px-3 py-1 text-xs font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 border border-indigo-100 dark:border-indigo-500/20 rounded-full uppercase tracking-wide">
                                    {skill.category.name}
                                </span>
                            ) : (
                                <span className="px-3 py-1 text-xs font-bold text-gray-500 dark:text-zinc-500 bg-gray-100 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-full uppercase tracking-wide">
                                    Uncategorized
                                </span>
                            )}
                            {skill.is_official && (
                                <span className="px-3 py-1 text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30 border border-emerald-100 dark:border-emerald-500/20 rounded-full uppercase tracking-wide flex items-center gap-1">
                                    <Shield className="w-3 h-3" /> Official
                                </span>
                            )}
                        </div>

                        <div>
                            <h1 className="text-xl font-bold text-gray-900 dark:text-white tracking-tight mb-2">
                                {skill.name}
                            </h1>
                            <p className="text-sm text-gray-500 dark:text-zinc-400 leading-relaxed max-w-2xl">
                                {skill.description || skill.summary}
                            </p>
                        </div>
                    </div>

                    <div className="flex-shrink-0">
                        <SkillHeaderEngagement
                            skillId={skill.id}
                            skillName={skill.name}
                            initialStars={skill.stars}
                            initialViews={skill.views}
                            installUrl={installUrl}
                        />
                    </div>
                </div>
            </div>

            {/* Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content Column */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Overview */}
                    <section className="bg-white dark:bg-card border border-gray-100 dark:border-white/10 rounded-2xl p-6 shadow-sm">
                        <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-white">
                            <FileText className="w-4 h-4 opacity-70" />
                            <h2 className="text-base font-bold tracking-tight">Overview</h2>
                        </div>
                        <div className="prose prose-sm dark:prose-invert max-w-none text-gray-600 dark:text-zinc-300">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {skill.content || skill.overview || "_No overview provided._"}
                            </ReactMarkdown>
                        </div>
                    </section>

                    {/* Use Cases - Benchmark Feature */}
                    {skill.use_cases && skill.use_cases.length > 0 && (
                        <section className="bg-white dark:bg-card border border-gray-100 dark:border-white/10 rounded-2xl p-6 shadow-sm">
                            <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-white">
                                <Box className="w-4 h-4 opacity-70" />
                                <h2 className="text-base font-bold tracking-tight">Best used for...</h2>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {skill.use_cases.map((useCase, i) => (
                                    <div key={i} className="flex items-start gap-2 p-3 bg-gray-50 dark:bg-zinc-900/40 rounded-xl border border-gray-100 dark:border-white/5 text-sm text-gray-600 dark:text-zinc-400">
                                        <div className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 shrink-0" />
                                        {useCase}
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {/* Technical Specifications - Benchmark Feature */}
                    <section className="bg-white dark:bg-card border border-gray-100 dark:border-white/10 rounded-2xl p-6 shadow-sm">
                        <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-white">
                            <Code className="w-4 h-4 opacity-70" />
                            <h2 className="text-base font-bold tracking-tight">Technical Specifications</h2>
                        </div>

                        <div className="space-y-6">
                            {(allowedTools.length > 0 || userInvocable !== null || disableModelInvocation !== null) && (
                                <div className="space-y-3">
                                    <h3 className="text-xs font-bold text-gray-500 dark:text-zinc-500 uppercase tracking-wider">Dependencies & Permissions</h3>
                                    <div className="bg-gray-50 dark:bg-zinc-900/40 rounded-xl p-4 border border-gray-100 dark:border-white/5 space-y-3">
                                        {allowedTools.length > 0 && (
                                            <div>
                                                <span className="text-xs text-gray-500 dark:text-zinc-500 mb-1.5 block">Allowed Tools</span>
                                                <div className="flex flex-wrap gap-2">
                                                    {allowedTools.map((tool) => (
                                                        <span key={tool} className="px-2 py-1 bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-gray-700 dark:text-zinc-300 rounded text-[11px] font-mono font-medium">
                                                            {tool}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                        <div className="grid grid-cols-2 gap-4">
                                            {userInvocable !== null && (
                                                <div className="flex items-center justify-between">
                                                    <span className="text-xs text-gray-500 dark:text-zinc-500">User Invocable</span>
                                                    <span className={`text-xs font-bold ${userInvocable ? "text-emerald-600 dark:text-emerald-400" : "text-gray-900 dark:text-white"}`}>
                                                        {userInvocable ? "Yes" : "No"}
                                                    </span>
                                                </div>
                                            )}
                                            {disableModelInvocation !== null && (
                                                <div className="flex items-center justify-between">
                                                    <span className="text-xs text-gray-500 dark:text-zinc-500">Model Auto-Invoke</span>
                                                    <span className={`text-xs font-bold ${!disableModelInvocation ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"}`}>
                                                        {!disableModelInvocation ? "Enabled" : "Disabled"}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {(skillInterface.inputs || skillInterface.outputs) && (
                                <div className="grid gap-4">
                                    {skillInterface.inputs && (
                                        <div className="space-y-2">
                                            <h3 className="text-xs font-bold text-gray-500 dark:text-zinc-500 uppercase tracking-wider">Inputs</h3>
                                            <div className="bg-[#1e1e1e] p-4 rounded-xl shadow-inner border border-gray-800 overflow-hidden">
                                                <pre className="text-xs text-gray-300 overflow-x-auto font-mono custom-scrollbar">
                                                    {JSON.stringify(skillInterface.inputs, null, 2)}
                                                </pre>
                                            </div>
                                        </div>
                                    )}

                                    {skillInterface.outputs && (
                                        <div className="space-y-2">
                                            <h3 className="text-xs font-bold text-gray-500 dark:text-zinc-500 uppercase tracking-wider">Outputs</h3>
                                            <div className="bg-[#1e1e1e] p-4 rounded-xl shadow-inner border border-gray-800 overflow-hidden">
                                                <pre className="text-xs text-gray-300 overflow-x-auto font-mono custom-scrollbar">
                                                    {JSON.stringify(skillInterface.outputs, null, 2)}
                                                </pre>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </section>

                    {/* Quick Start */}
                    <section className="bg-white dark:bg-card border border-gray-100 dark:border-white/10 rounded-2xl p-6 shadow-sm">
                        <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-white">
                            <Layers className="w-4 h-4 opacity-70" />
                            <h2 className="text-base font-bold tracking-tight">Quick Start</h2>
                        </div>

                        <div className="bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-500/20 rounded-xl p-6">
                            <div className="space-y-6">
                                <div>
                                    <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-2">Install Snippet</h3>
                                    <p className="text-sm text-gray-600 dark:text-zinc-400 mb-4">
                                        Pick your client, copy the command, and install this skill in one step.
                                    </p>
                                    <SkillCopyCommand
                                        skillId={skill.id}
                                        slug={skill.slug}
                                        installUrl={installUrl}
                                        sourceLinks={skill.source_links}
                                    />
                                </div>

                                {primarySourceUrl && (
                                    <div className="pt-6 border-t border-blue-100 dark:border-blue-500/20">
                                        <h3 className="text-sm font-bold text-gray-900 dark:text-white mb-2">Source / Docs</h3>
                                        <a
                                            href={primarySourceUrl}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="inline-flex items-center gap-2 px-4 py-2 bg-black dark:bg-white text-white dark:text-black rounded-lg text-xs font-bold shadow-sm hover:bg-gray-800 dark:hover:bg-zinc-200 transition-all"
                                        >
                                            <ExternalLink className="w-3 h-3" />
                                            View Source / Deploy Docs
                                        </a>
                                        {sourceUrlCandidates.length > 1 && (
                                            <div className="mt-3 flex flex-wrap gap-2">
                                                {sourceUrlCandidates.slice(1, 4).map((url) => (
                                                    <a
                                                        key={url}
                                                        href={url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-semibold text-blue-700 dark:text-blue-300 bg-blue-100/60 dark:bg-blue-900/20 rounded border border-blue-200/70 dark:border-blue-500/20"
                                                    >
                                                        <ExternalLink className="w-3 h-3" />
                                                        Alternate Source
                                                    </a>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </section>
                </div>

                {/* Sidebar Column */}
                <div className="space-y-6">
                    {/* Metadata Card */}
                    <div className="bg-white dark:bg-card border border-gray-100 dark:border-white/10 rounded-2xl p-6 shadow-sm">
                        <div className="flex items-center gap-2 mb-6 text-gray-900 dark:text-white border-b border-gray-100 dark:border-white/5 pb-4">
                            <Box className="w-5 h-5 opacity-70" />
                            <h3 className="font-bold text-lg">Details</h3>
                        </div>

                        <div className="space-y-5">
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-500 dark:text-zinc-500 flex items-center gap-2">
                                    <User className="w-4 h-4" /> Author
                                </span>
                                <span className="text-sm font-bold text-gray-900 dark:text-white text-right truncate max-w-[120px]">
                                    {skill.author || "Community"}
                                </span>
                            </div>
                            {skill.github_stars !== undefined && skill.github_stars !== null && (
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-gray-500 dark:text-zinc-500 flex items-center gap-2">
                                        <Star className="w-4 h-4 text-orange-400" /> GitHub Stars
                                    </span>
                                    <span className="text-sm font-bold text-gray-900 dark:text-white">
                                        {skill.github_stars}
                                    </span>
                                </div>
                            )}
                            {skill.trust_level && (
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-gray-500 dark:text-zinc-500 flex items-center gap-2">
                                        <Shield className="w-4 h-4" /> Trust
                                    </span>
                                    <span
                                        className={`text-xs font-bold px-2 py-1 rounded border ${skill.trust_level === "ok"
                                                ? "text-emerald-700 bg-emerald-50 border-emerald-200 dark:text-emerald-300 dark:bg-emerald-900/20 dark:border-emerald-500/20"
                                                : skill.trust_level === "warning"
                                                    ? "text-amber-700 bg-amber-50 border-amber-200 dark:text-amber-300 dark:bg-amber-900/20 dark:border-amber-500/20"
                                                    : "text-rose-700 bg-rose-50 border-rose-200 dark:text-rose-300 dark:bg-rose-900/20 dark:border-rose-500/20"
                                            }`}
                                        title={skill.trust_flags?.join(", ") || ""}
                                    >
                                        {skill.trust_level.toUpperCase()} {skill.trust_score !== undefined && skill.trust_score !== null ? Math.round(skill.trust_score) : ""}
                                    </span>
                                </div>
                            )}
                            {skill.trust_last_verified_at && (
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium text-gray-500 dark:text-zinc-500 flex items-center gap-2">
                                        <Calendar className="w-4 h-4" /> Last Verified
                                    </span>
                                    <span className="text-sm font-bold text-gray-900 dark:text-white">
                                        {new Date(skill.trust_last_verified_at).toISOString().split('T')[0]}
                                    </span>
                                </div>
                            )}
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-500 dark:text-zinc-500 flex items-center gap-2">
                                    <Shield className="w-4 h-4" /> License
                                </span>
                                <span className="text-sm font-bold text-gray-900 dark:text-white">MIT</span>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-sm font-medium text-gray-500 dark:text-zinc-500 flex items-center gap-2">
                                    <Calendar className="w-4 h-4" /> Updated
                                </span>
                                <span className="text-sm font-bold text-gray-900 dark:text-white">
                                    {new Date(skill.updated_at).toISOString().split('T')[0]}
                                </span>
                            </div>
                            {(allowedTools.length > 0 || userInvocable !== null || disableModelInvocation !== null) && (
                                <div className="pt-4 mt-2 border-t border-gray-100 dark:border-white/5">
                                    <div className="flex flex-col gap-3">
                                        <h4 className="text-xs font-bold text-gray-400 dark:text-zinc-500 uppercase tracking-wider mb-1">
                                            Claude Spec
                                        </h4>
                                        {allowedTools.length > 0 && (
                                            <div className="flex flex-wrap gap-2">
                                                {allowedTools.slice(0, 10).map((tool) => (
                                                    <span
                                                        key={tool}
                                                        className="px-2.5 py-1 bg-gray-100 dark:bg-zinc-800 text-gray-700 dark:text-zinc-300 rounded-lg text-[11px] font-bold"
                                                    >
                                                        {tool}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                        {(userInvocable !== null || disableModelInvocation !== null) && (
                                            <div className="grid grid-cols-1 gap-2">
                                                {userInvocable !== null && (
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm font-medium text-gray-500 dark:text-zinc-500">
                                                            user-invocable
                                                        </span>
                                                        <span className="text-sm font-bold text-gray-900 dark:text-white">
                                                            {userInvocable ? "true" : "false"}
                                                        </span>
                                                    </div>
                                                )}
                                                {disableModelInvocation !== null && (
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-sm font-medium text-gray-500 dark:text-zinc-500">
                                                            disable-model-invocation
                                                        </span>
                                                        <span className="text-sm font-bold text-gray-900 dark:text-white">
                                                            {disableModelInvocation ? "true" : "false"}
                                                        </span>
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                            <div className="pt-4 mt-2 border-t border-gray-100 dark:border-white/5">
                                <div className="flex flex-col gap-3">
                                    <h4 className="text-xs font-bold text-gray-400 dark:text-zinc-500 uppercase tracking-wider mb-1">Source Links</h4>
                                    {(() => {
                                        const links = skill.source_links?.map(l => ({ type: l.link_type, url: l.url || l.external_id }))
                                            .filter(l => l.url) || [];

                                        if (links.length === 0 && installUrl) {
                                            links.push({ type: "Repository", url: installUrl });
                                        }

                                        if (links.length === 0) return <span className="text-xs text-gray-400">None available</span>;

                                        return links.map((link, i) => (
                                            <a
                                                key={i}
                                                href={link.url!}
                                                target="_blank"
                                                rel="noopener"
                                                className="flex items-center gap-2 text-sm font-bold text-gray-700 dark:text-zinc-400 hover:text-blue-600 dark:hover:text-accent transition-colors"
                                            >
                                                <Globe className="w-3.5 h-3.5" />
                                                {link.type}
                                            </a>
                                        ));
                                    })()}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Tags Card */}
                    <div className="bg-white dark:bg-card border border-gray-100 dark:border-white/10 rounded-2xl p-6 shadow-sm">
                        <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-white">
                            <Tag className="w-5 h-5 opacity-70" />
                            <h3 className="font-bold text-lg">Tags</h3>
                        </div>
                        <div className="flex flex-wrap gap-2">
                            {skill.category && (
                                <Link
                                    href={`/skills?category=${skill.category.slug}`}
                                    className="px-3 py-1.5 bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-zinc-400 hover:bg-gray-200 dark:hover:bg-zinc-700 hover:text-black dark:hover:text-white rounded-lg text-xs font-bold transition-all"
                                >
                                    #{skill.category.name}
                                </Link>
                            )}
                            {skill.tags?.map((tag) => (
                                <Link
                                    key={tag.slug}
                                    href={`/skills?q=${tag.name}`}
                                    className="px-3 py-1.5 bg-gray-100 dark:bg-zinc-800 text-gray-600 dark:text-zinc-400 hover:bg-gray-200 dark:hover:bg-zinc-700 hover:text-black dark:hover:text-white rounded-lg text-xs font-bold transition-all"
                                >
                                    #{tag.name}
                                </Link>
                            ))}
                            {(!skill.tags || skill.tags.length === 0) && !skill.category && (
                                <span className="text-sm text-gray-400 italic">No tags</span>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
