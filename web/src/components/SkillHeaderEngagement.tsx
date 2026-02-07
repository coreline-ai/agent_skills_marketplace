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

function isFavorited(skillId: string): boolean {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(`favorite:${skillId}`) === "1";
}

export function SkillHeaderEngagement({
    skillId,
    skillName,
    initialStars,
    initialViews,
    installUrl,
}: SkillHeaderEngagementProps) {
    const favoriteKey = `favorite:${skillId}`;
    const [stars, setStars] = useState(initialStars || 0);
    const [views, setViews] = useState(initialViews || 0);
    const [favorited, setFavorited] = useState(() => isFavorited(skillId));
    const [shared, setShared] = useState(false);

    useEffect(() => {
        // Count one view per tab session for this skill detail.
        const viewKey = `viewed:${skillId}`;
        if (sessionStorage.getItem(viewKey) === "1") return;
        sessionStorage.setItem(viewKey, "1");

        api.post<EventTrackResponse>("/events/view", {
            type: "view",
            skill_id: skillId,
            session_id: getSessionId(),
            source: "web",
            context: "skill-detail",
        })
            .then((response) => {
                if (response.counted) {
                    setViews((prev) => prev + 1);
                }
            })
            .catch((error) => {
                sessionStorage.removeItem(viewKey);
                console.warn("Failed to track view event", error);
            });
    }, [skillId]);

    const onFavorite = async () => {
        if (favorited) return;
        setFavorited(true);

        try {
            const response = await api.post<EventTrackResponse>("/events/favorite", {
                type: "favorite",
                skill_id: skillId,
                session_id: getSessionId(),
                source: "web",
                context: "detail-favorite",
            });
            localStorage.setItem(favoriteKey, "1");
            if (response.counted) {
                setStars((prev) => prev + 1);
            }
        } catch (error) {
            setFavorited(false);
            localStorage.removeItem(favoriteKey);
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
            <div className="flex justify-end mb-6">
                <div className="flex gap-3">
                    <button
                        type="button"
                        onClick={onFavorite}
                        title={favorited ? "Favorited" : "Add favorite"}
                        className={`p-3 border border-border dark:border-white/10 rounded-xl transition-all shadow-soft overflow-hidden hover:shadow-hover ${favorited ? "bg-black text-white dark:bg-white dark:text-black" : "bg-background text-foreground dark:text-white hover:bg-sidebar dark:hover:bg-white/5"
                            }`}
                    >
                        <Star className={`w-5 h-5 ${favorited ? "fill-current" : ""}`} />
                    </button>
                    <button
                        type="button"
                        onClick={onShare}
                        title={shared ? "Copied" : "Share"}
                        className={`p-3 border border-border dark:border-white/10 rounded-xl transition-all shadow-soft overflow-hidden hover:shadow-hover ${shared ? "bg-green-500 text-white" : "bg-background text-foreground dark:text-white hover:bg-sidebar dark:hover:bg-white/5"
                            }`}
                    >
                        <Share2 className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div className="mt-8 flex flex-wrap items-center gap-6 pt-6 border-t border-border dark:border-white/10">
                <div className="flex items-center gap-2 font-medium text-text-muted">
                    <Star className="w-5 h-5" />
                    <span className="text-xl font-bold text-foreground dark:text-white">{stars}</span> stars
                </div>
                <div className="flex items-center gap-2 font-medium text-text-muted">
                    <Eye className="w-5 h-5" />
                    <span className="text-xl font-bold text-foreground dark:text-white">{views}</span> views
                </div>
                <div className="ml-auto">
                    {installUrl ? (
                        <a
                            href={installUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 bg-foreground dark:bg-white text-background dark:text-black px-8 py-3 rounded-full font-bold text-lg shadow-soft hover:shadow-hover hover:-translate-y-0.5 transition-all"
                        >
                            <Download className="w-5 h-5" /> Open Source
                        </a>
                    ) : (
                        <button
                            type="button"
                            disabled
                            className="inline-flex items-center gap-2 bg-sidebar dark:bg-zinc-900 text-text-muted border border-dashed border-border dark:border-white/5 px-8 py-3 rounded-full font-bold text-lg cursor-not-allowed"
                        >
                            <Download className="w-5 h-5" /> No Source URL
                        </button>
                    )}
                </div>
            </div>
        </>
    );
}
