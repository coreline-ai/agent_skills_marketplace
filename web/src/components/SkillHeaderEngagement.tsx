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
                        className={`p-3 border-2 border-main rounded-lg transition-all neo-shadow neo-shadow-hover active:translate-x-[4px] active:translate-y-[4px] active:shadow-none ${favorited ? "bg-accent text-black" : "bg-background text-foreground hover:bg-accent hover:text-black"
                            }`}
                    >
                        <Star className={`w-5 h-5 ${favorited ? "fill-black" : ""}`} />
                    </button>
                    <button
                        type="button"
                        onClick={onShare}
                        title={shared ? "Copied" : "Share"}
                        className={`p-3 border-2 border-main rounded-lg transition-all neo-shadow neo-shadow-hover active:translate-x-[4px] active:translate-y-[4px] active:shadow-none ${shared ? "bg-green-500 text-white" : "bg-background text-foreground hover:bg-accent hover:text-black"
                            }`}
                    >
                        <Share2 className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div className="mt-8 flex flex-wrap items-center gap-6 pt-6 border-t-2 border-main">
                <div className="flex items-center gap-2 font-bold">
                    <Star className="w-6 h-6 fill-current" />
                    <span className="text-xl">{stars}</span> stars
                </div>
                <div className="flex items-center gap-2 font-bold">
                    <Eye className="w-6 h-6" />
                    <span className="text-xl">{views}</span> views
                </div>
                <div className="ml-auto">
                    {installUrl ? (
                        <a
                            href={installUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 bg-invert border-2 border-main px-6 py-3 rounded-lg font-bold text-lg neo-shadow neo-shadow-hover active:translate-x-[4px] active:translate-y-[4px] active:shadow-none"
                        >
                            <Download className="w-5 h-5" /> Open Source
                        </a>
                    ) : (
                        <button
                            type="button"
                            disabled
                            className="inline-flex items-center gap-2 bg-foreground/10 text-foreground/50 border-2 border-dashed border-main px-6 py-3 rounded-lg font-bold text-lg cursor-not-allowed opacity-70"
                        >
                            <Download className="w-5 h-5" /> No Source URL
                        </button>
                    )}
                </div>
            </div>
        </>
    );
}
