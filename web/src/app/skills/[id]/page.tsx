// Force dynamic for detail page to ensure fresh data
export const dynamic = 'force-dynamic';

import { api } from "@/app/lib/api";
import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";
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
}

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
            <div className="text-center py-20">
                <h1 className="text-2xl font-bold text-gray-900">Skill not found</h1>
                <Link href="/skills" className="text-blue-600 hover:underline mt-4 inline-block">
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

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <Link href="/skills" className="inline-flex items-center text-gray-500 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
                <ArrowLeft className="w-4 h-4 mr-2" /> Back to Skills
            </Link>

            {/* Header */}
            <div className="bg-white dark:bg-black border-2 border-black dark:border-white rounded-2xl p-8 shadow-sm dark:shadow-none">
                <div className="flex items-start justify-between">
                    <div>
                        <div className="flex items-center gap-3 mb-4">
                            <span className="px-3 py-1 text-sm font-semibold text-blue-600 bg-blue-50 rounded-full">
                                {skill.category?.name || "Uncategorized"}
                            </span>
                            {skill.is_official && (
                                <span className="px-3 py-1 text-sm font-semibold text-green-600 bg-green-50 rounded-full">
                                    Official
                                </span>
                            )}
                        </div>
                        <h1 className="text-3xl font-black text-black dark:text-white mb-2">{skill.name}</h1>
                        <p className="text-gray-600 dark:text-gray-300 text-lg font-medium">{skill.description}</p>
                    </div>
                </div>
                <SkillHeaderEngagement
                    skillId={skill.id}
                    skillName={skill.name}
                    initialStars={skill.stars}
                    initialViews={skill.views}
                    installUrl={installUrl}
                />
            </div>

            {/* Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-8">
                    <section className="bg-white dark:bg-black border-2 border-black dark:border-white rounded-xl p-6">
                        <h2 className="text-xl font-black text-black dark:text-white mb-4 uppercase">Overview</h2>
                        <div className="prose prose-blue dark:prose-invert max-w-none text-gray-600 dark:text-gray-300 font-medium">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {skill.overview || skill.content || skill.summary || skill.description || "No detailed description available."}
                            </ReactMarkdown>
                        </div>
                    </section>

                    {(skillInterface.inputs || skillInterface.outputs) && (
                        <section className="bg-white dark:bg-black border-2 border-black dark:border-white rounded-xl p-6">
                            <h2 className="text-xl font-black text-black dark:text-white mb-4 uppercase">Interface</h2>
                            <div className="grid md:grid-cols-2 gap-6">
                                <div>
                                    <h3 className="font-bold text-black dark:text-white mb-2">Inputs</h3>
                                    <pre className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto border-2 border-black dark:border-white text-black dark:text-white shadow-sm dark:shadow-none">
                                        {JSON.stringify(skillInterface.inputs || {}, null, 2)}
                                    </pre>
                                </div>
                                <div>
                                    <h3 className="font-bold text-black dark:text-white mb-2">Outputs</h3>
                                    <pre className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg text-sm overflow-x-auto border-2 border-black dark:border-white text-black dark:text-white shadow-sm dark:shadow-none">
                                        {JSON.stringify(skillInterface.outputs || {}, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        </section>
                    )}

                    {/* Usage Guide */}
                    <section className="bg-white dark:bg-black border-2 border-black dark:border-white rounded-xl p-6">
                        <h2 className="text-xl font-black text-black dark:text-white mb-4 uppercase">How to Use</h2>
                        <div className="prose prose-blue dark:prose-invert max-w-none text-gray-600 dark:text-gray-300 font-medium">
                            {installUrl ? (
                                <div>
                                    <p className="mb-4">
                                        This skill is hosted externally. To use or install <strong>{skill.name}</strong>, please follow the instructions in the official repository.
                                    </p>
                                    <a
                                        href={installUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:underline font-bold"
                                    >
                                        View Installation Guide <ExternalLink className="w-4 h-4 ml-1" />
                                    </a>
                                </div>
                            ) : (
                                <p>No usage instructions available for this skill.</p>
                            )}
                        </div>
                    </section>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    <section className="bg-white dark:bg-black border-2 border-black dark:border-white rounded-xl p-6 shadow-sm dark:shadow-none">
                        <h2 className="font-black text-black dark:text-white mb-4 uppercase">Details</h2>
                        <div className="space-y-3 text-sm font-bold">
                            <div className="flex justify-between py-2 border-b-2 border-black dark:border-white/20">
                                <span className="text-gray-500 dark:text-gray-400">Author</span>
                                <span className="text-black dark:text-white">{skill.author || "Unknown"}</span>
                            </div>
                            <div className="flex justify-between py-2 border-b-2 border-black dark:border-white/20">
                                <span className="text-gray-500 dark:text-gray-400">Version</span>
                                <span className="text-black dark:text-white">1.0.0</span>
                            </div>
                            <div className="flex justify-between py-2 border-b-2 border-black dark:border-white/20">
                                <span className="text-gray-500 dark:text-gray-400">License</span>
                                <span className="text-black dark:text-white">MIT</span>
                            </div>
                            <div className="flex justify-between py-2">
                                <span className="text-gray-500 dark:text-gray-400">Updated</span>
                                <span className="text-black dark:text-white">
                                    {new Date(skill.updated_at).toLocaleDateString()}
                                </span>
                            </div>
                        </div>
                    </section>

                    <section className="bg-white border border-gray-200 rounded-xl p-6">
                        <h2 className="font-bold text-gray-900 mb-4">Tags</h2>
                        <div className="flex flex-wrap gap-2">
                            {(() => {
                                const tags = (skill.tags && skill.tags.length > 0) ? skill.tags : [];
                                if (tags.length > 0) {
                                    return tags.map((tag) => (
                                        <span key={tag.slug} className="px-2.5 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-md">
                                            {tag.name}
                                        </span>
                                    ));
                                }

                                // Fallback: many sources do not publish tags in SKILL.md; show category as a tag.
                                const categoryName = (skill.category?.name || "").trim();
                                if (!categoryName) {
                                    return <span className="text-gray-400 text-sm">No tags</span>;
                                }
                                const categorySlug = (skill.category?.slug || "")
                                    || `category-${categoryName.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "")}`;
                                return (
                                    <span key={categorySlug} className="px-2.5 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-md">
                                        {categoryName}
                                    </span>
                                );
                            })()}
                        </div>
                    </section>

                    <section className="bg-white border border-gray-200 rounded-xl p-6">
                        <h2 className="font-bold text-gray-900 mb-4">Source</h2>
                        {(() => {
                            const links: Array<{ link_type: string; url: string }> = [];
                            for (const l of skill.source_links || []) {
                                const url = (l.url || l.external_id || "").trim();
                                if (!url) continue;
                                links.push({ link_type: l.link_type, url });
                            }

                            // Fallback: many skills don't have normalized SkillSourceLink rows yet.
                            if (links.length === 0 && installUrl) {
                                links.push({ link_type: "definition", url: installUrl });
                            }

                            if (links.length === 0) {
                                return <span className="text-gray-400 text-sm">No source links</span>;
                            }

                            return links.map((link) => (
                                <a
                                    key={`${link.link_type}-${link.url}`}
                                    href={link.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-2 text-sm text-blue-600 hover:underline mb-2"
                                >
                                    <ExternalLink className="w-4 h-4" />
                                    {link.link_type}
                                </a>
                            ));
                        })()}
                    </section>
                </div>
            </div>
        </div>
    );
}
