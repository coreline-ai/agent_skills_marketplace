import { api } from "@/lib/api";
import Link from "next/link";
import { ArrowLeft, ExternalLink, Box, Tag, Layers, FileText, Code, Globe, User, Calendar, Shield } from "lucide-react";
import { SkillHeaderEngagement } from "@/components/SkillHeaderEngagement";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

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
}

// Ensure dynamic rendering
export const dynamic = 'force-dynamic';

async function getSkill(id: string) {
    try {
        return await api.get<SkillDetail>(`/skills/${id}`);
    } catch {
        return null;
    }
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
                        <div className="prose prose-sm prose-gray dark:prose-invert max-w-none text-gray-600 dark:text-zinc-400 leading-relaxed prose-headings:font-bold prose-headings:text-gray-900 dark:prose-headings:text-white prose-a:text-blue-600 dark:prose-a:text-accent prose-a:font-bold hover:prose-a:text-blue-800 dark:hover:prose-a:text-accent/80 prose-code:text-pink-600 dark:prose-code:text-accent prose-code:bg-pink-50 dark:prose-code:bg-accent/10 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none prose-pre:bg-gray-900 prose-pre:text-gray-50 dark:prose-pre:bg-black dark:prose-pre:border dark:prose-pre:border-white/10 prose-img:rounded-xl">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {skill.overview || skill.content || "No detailed overview available."}
                            </ReactMarkdown>
                        </div>
                    </section>

                    {/* Interface */}
                    {(skillInterface.inputs || skillInterface.outputs) && (
                        <section className="bg-white dark:bg-card border border-gray-100 dark:border-white/10 rounded-2xl p-6 shadow-sm">
                            <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-white">
                                <Code className="w-4 h-4 opacity-70" />
                                <h2 className="text-base font-bold tracking-tight">Interface</h2>
                            </div>

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
                        </section>
                    )}

                    {/* Installation / Usage */}
                    <section className="bg-white dark:bg-card border border-gray-100 dark:border-white/10 rounded-2xl p-6 shadow-sm">
                        <div className="flex items-center gap-2 mb-4 text-gray-900 dark:text-white">
                            <Layers className="w-4 h-4 opacity-70" />
                            <h2 className="text-base font-bold tracking-tight">Integration</h2>
                        </div>

                        <div className="bg-blue-50/50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-500/20 rounded-xl p-6">
                            {installUrl ? (
                                <div className="space-y-4">
                                    <p className="text-gray-700 dark:text-zinc-300 font-medium">
                                        To integrate this skill into your agent, refer to the official documentation or source repository.
                                    </p>
                                    <a
                                        href={installUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center gap-2 px-6 py-3 bg-black dark:bg-white text-white dark:text-black rounded-full font-bold shadow-md hover:bg-gray-800 dark:hover:bg-zinc-200 hover:shadow-lg transition-all"
                                    >
                                        <ExternalLink className="w-4 h-4" />
                                        View Documentation
                                    </a>
                                </div>
                            ) : (
                                <p className="text-gray-500 dark:text-zinc-500 italic">No direct integration link provided.</p>
                            )}
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
                                    {new Date(skill.updated_at).toLocaleDateString()}
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
