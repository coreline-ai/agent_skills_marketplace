"use client";

import { useEffect, useState } from "react";
import { Download, Eye, Share2, Star } from "lucide-react";
import { api } from "@/app/lib/api";

interface SkillHeaderEngagementProps {
    skillId: string;
    skillName: string;
    initialStars: number;
    initialViews: number;
    installUrl: string | null;
}

function getSessionId(): string {
    const key = "skill_session_id";
    const cached = localStorage.getItem(key);
    if (cached) return cached;
    const next = crypto.randomUUID();
    localStorage.setItem(key, next);
    return next;
}

export function SkillHeaderEngagement({
    skillId,
    skillName,
    initialStars,
    initialViews,
    installUrl,
}: SkillHeaderEngagementProps) {
    const [stars, setStars] = useState(initialStars || 0);
    const [views, setViews] = useState(initialViews || 0);
    const [favorited, setFavorited] = useState(false);
    const [shared, setShared] = useState(false);

    useEffect(() => {
        // Count one view per tab session for this skill detail.
        const viewKey = `viewed:${skillId}`;
        if (sessionStorage.getItem(viewKey) === "1") return;
        sessionStorage.setItem(viewKey, "1");

        api.post("/events/view", {
            type: "view",
            skill_id: skillId,
            session_id: getSessionId(),
            source: "web",
            context: "skill-detail",
        })
            .then(() => setViews((prev) => prev + 1))
            .catch((error) => {
                console.warn("Failed to track view event", error);
            });
    }, [skillId]);

    const onFavorite = async () => {
        if (favorited) return;
        setFavorited(true);
        setStars((prev) => prev + 1);
        localStorage.setItem(`favorite:${skillId}`, "1");

        try {
            await api.post("/events/favorite", {
                type: "favorite",
                skill_id: skillId,
                session_id: getSessionId(),
                source: "web",
                context: "detail-favorite",
            });
        } catch (error) {
            console.warn("Failed to track favorite event", error);
        }
    };

    const onShare = async () => {
        const shareUrl = `${window.location.origin}/skills/${skillId}`;
        try {
            if (navigator.share) {
                await navigator.share({
                    title: skillName,
                    text: `Check this skill: ${skillName}`,
                    url: shareUrl,
                });
            } else if (navigator.clipboard?.writeText) {
                await navigator.clipboard.writeText(shareUrl);
            }
            setShared(true);
            setTimeout(() => setShared(false), 1500);
        } catch (error) {
            console.warn("Share cancelled or failed", error);
        }
    };

    return (
        <>
            <div className="flex justify-end">
                <div className="flex gap-2">
                    <button
                        type="button"
                        onClick={onFavorite}
                        title={favorited ? "Favorited" : "Add favorite"}
                        className={`p-2 transition-colors border border-gray-200 rounded-lg hover:bg-gray-50 ${
                            favorited ? "text-yellow-500" : "text-gray-400 hover:text-yellow-500"
                        }`}
                    >
                        <Star className={`w-5 h-5 ${favorited ? "fill-yellow-500" : ""}`} />
                    </button>
                    <button
                        type="button"
                        onClick={onShare}
                        title={shared ? "Copied" : "Share"}
                        className={`p-2 transition-colors border border-gray-200 rounded-lg hover:bg-gray-50 ${
                            shared ? "text-green-600" : "text-gray-400 hover:text-blue-600"
                        }`}
                    >
                        <Share2 className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div className="mt-8 flex items-center gap-6 pt-6 border-t border-gray-100">
                <div className="flex items-center gap-2 text-gray-600">
                    <Star className="w-5 h-5 text-yellow-500 fill-yellow-500" />
                    <span className="font-medium">{stars}</span> stars
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                    <Eye className="w-5 h-5" />
                    <span className="font-medium">{views}</span> views
                </div>
                <div className="ml-auto">
                    {installUrl ? (
                        <a
                            href={installUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 bg-gray-900 text-white px-5 py-2.5 rounded-lg hover:bg-gray-800 transition-colors font-medium"
                        >
                            <Download className="w-4 h-4" /> Open Source
                        </a>
                    ) : (
                        <button
                            type="button"
                            disabled
                            className="inline-flex items-center gap-2 bg-gray-400 text-white px-5 py-2.5 rounded-lg font-medium cursor-not-allowed"
                        >
                            <Download className="w-4 h-4" /> No Source URL
                        </button>
                    )}
                </div>
            </div>
        </>
    );
}
