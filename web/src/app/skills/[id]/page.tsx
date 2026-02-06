// Force dynamic for detail page to ensure fresh data
export const dynamic = 'force-dynamic';

import { api } from "@/app/lib/api";
import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { SkillHeaderEngagement } from "@/components/SkillHeaderEngagement";

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
}

interface SkillDetail {
    id: string;
    name: string;
    description?: string | null;
    summary?: string | null;
    content?: string | null;
    is_official: boolean;
    category?: { name: string } | null;
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
            <Link href="/skills" className="inline-flex items-center text-gray-500 hover:text-gray-900 transition-colors">
                <ArrowLeft className="w-4 h-4 mr-2" /> Back to Skills
            </Link>

            {/* Header */}
            <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
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
                        <h1 className="text-3xl font-bold text-gray-900 mb-2">{skill.name}</h1>
                        <p className="text-gray-600 text-lg">{skill.description}</p>
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
                    <section className="bg-white border border-gray-200 rounded-xl p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Overview</h2>
                        <div className="prose prose-blue max-w-none text-gray-600">
                            {/* Render markdown content here implies using a markdown renderer */
                                skill.content || skill.summary || skill.description || "No detailed description available."}
                        </div>
                    </section>

                    {(skillInterface.inputs || skillInterface.outputs) && (
                        <section className="bg-white border border-gray-200 rounded-xl p-6">
                            <h2 className="text-xl font-bold text-gray-900 mb-4">Interface</h2>
                            <div className="grid md:grid-cols-2 gap-6">
                                <div>
                                    <h3 className="font-semibold text-gray-900 mb-2">Inputs</h3>
                                    <pre className="bg-gray-50 p-3 rounded-lg text-sm overflow-x-auto border border-gray-100">
                                        {JSON.stringify(skillInterface.inputs || {}, null, 2)}
                                    </pre>
                                </div>
                                <div>
                                    <h3 className="font-semibold text-gray-900 mb-2">Outputs</h3>
                                    <pre className="bg-gray-50 p-3 rounded-lg text-sm overflow-x-auto border border-gray-100">
                                        {JSON.stringify(skillInterface.outputs || {}, null, 2)}
                                    </pre>
                                </div>
                            </div>
                        </section>
                    )}

                    {/* Usage Guide */}
                    <section className="bg-white border border-gray-200 rounded-xl p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">How to Use</h2>
                        <div className="prose prose-blue max-w-none text-gray-600">
                            {installUrl ? (
                                <div>
                                    <p className="mb-4">
                                        This skill is hosted externally. To use or install <strong>{skill.name}</strong>, please follow the instructions in the official repository.
                                    </p>
                                    <a
                                        href={installUrl}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="inline-flex items-center text-blue-600 hover:underline font-medium"
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
                    <section className="bg-white border border-gray-200 rounded-xl p-6">
                        <h2 className="font-bold text-gray-900 mb-4">Details</h2>
                        <div className="space-y-3 text-sm">
                            <div className="flex justify-between py-2 border-b border-gray-50">
                                <span className="text-gray-500">Author</span>
                                <span className="font-medium text-gray-900">{skill.author || "Unknown"}</span>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-50">
                                <span className="text-gray-500">Version</span>
                                <span className="font-medium text-gray-900">1.0.0</span>
                            </div>
                            <div className="flex justify-between py-2 border-b border-gray-50">
                                <span className="text-gray-500">License</span>
                                <span className="font-medium text-gray-900">MIT</span>
                            </div>
                            <div className="flex justify-between py-2">
                                <span className="text-gray-500">Updated</span>
                                <span className="font-medium text-gray-900">
                                    {new Date(skill.updated_at).toLocaleDateString()}
                                </span>
                            </div>
                        </div>
                    </section>

                    <section className="bg-white border border-gray-200 rounded-xl p-6">
                        <h2 className="font-bold text-gray-900 mb-4">Tags</h2>
                        <div className="flex flex-wrap gap-2">
                            {skill.tags && skill.tags.length > 0 ? (
                                skill.tags.map((tag) => (
                                    <span key={tag.slug} className="px-2.5 py-1 text-xs font-medium text-gray-600 bg-gray-100 rounded-md">
                                        {tag.name}
                                    </span>
                                ))
                            ) : (
                                <span className="text-gray-400 text-sm">No tags</span>
                            )}
                        </div>
                    </section>

                    <section className="bg-white border border-gray-200 rounded-xl p-6">
                        <h2 className="font-bold text-gray-900 mb-4">Source</h2>
                        {skill.source_links && skill.source_links.map((link) => (
                            <a
                                key={`${link.link_type}-${link.url || "unknown"}`}
                                href={link.url || "#"}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-2 text-sm text-blue-600 hover:underline mb-2"
                            >
                                <ExternalLink className="w-4 h-4" />
                                {link.link_type}
                            </a>
                        ))}
                    </section>
                </div>
            </div>
        </div>
    );
}
