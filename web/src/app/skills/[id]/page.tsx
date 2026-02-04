import { api } from "@/app/lib/api";
import Link from "next/link";
import { ArrowLeft, Star, Share2, Download, ExternalLink } from "lucide-react";

interface SkillDetailProps {
    params: { id: string };
}

async function getSkill(id: string) {
    try {
        return await api.get<any>(`/skills/${id}`);
    } catch (e) {
        return null;
    }
}

export default async function SkillDetailPage({ params }: SkillDetailProps) {
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

    const skillInterface = skill.interface || {};

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
                    <div className="flex gap-2">
                        <button className="p-2 text-gray-400 hover:text-yellow-500 transition-colors border border-gray-200 rounded-lg hover:bg-gray-50">
                            <Star className="w-5 h-5" />
                        </button>
                        <button className="p-2 text-gray-400 hover:text-blue-600 transition-colors border border-gray-200 rounded-lg hover:bg-gray-50">
                            <Share2 className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                <div className="mt-8 flex items-center gap-6 pt-6 border-t border-gray-100">
                    <div className="flex items-center gap-2 text-gray-600">
                        <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                        <span className="font-medium">{skill.stars}</span> stars
                    </div>
                    <div className="flex items-center gap-2 text-gray-600">
                        <Download className="w-5 h-5" />
                        <span className="font-medium">{skill.views}</span> views
                    </div>
                    <div className="ml-auto">
                        <a
                            href={`http://localhost:8000/api/skills/${skill.id}/download`} // Mock download link
                            className="inline-flex items-center gap-2 bg-gray-900 text-white px-5 py-2.5 rounded-lg hover:bg-gray-800 transition-colors font-medium"
                        >
                            <Download className="w-4 h-4" /> Install Skill
                        </a>
                    </div>
                </div>
            </div>

            {/* Content */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-8">
                    <section className="bg-white border border-gray-200 rounded-xl p-6">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Overview</h2>
                        <div className="prose prose-blue max-w-none text-gray-600">
                            {/* Render markdown content here implies using a markdown renderer */
                                skill.content || skill.summary || "No detailed description available."}
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
                                skill.tags.map((tag: any) => (
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
                        {skill.source_links && skill.source_links.map((link: any) => (
                            <a
                                key={link.url}
                                href={link.url}
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
