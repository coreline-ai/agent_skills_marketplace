"use client";

import { useState } from "react";
import { Star, Share2 } from "lucide-react";
import { api } from "@/app/lib/api";

interface SkillActionsProps {
    skillId: string;
    skillName: string;
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
    const sessionId = crypto.randomUUID();
    localStorage.setItem(key, sessionId);
    return sessionId;
}

function isFavorited(skillId: string): boolean {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(`favorite:${skillId}`) === "1";
}

export function SkillActions({ skillId, skillName }: SkillActionsProps) {
    const favoriteKey = `favorite:${skillId}`;
    const [favorited, setFavorited] = useState(() => isFavorited(skillId));
    const [shared, setShared] = useState(false);

    const onToggleFavorite = async () => {
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
            if (!response.counted) return;
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
        <div className="flex items-center gap-3">
            <button
                type="button"
                onClick={onToggleFavorite}
                title={favorited ? "Favorited" : "Add favorite"}
                className={`p-3 border-2 border-black dark:border-white rounded-lg transition-all neo-shadow hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_#000] dark:hover:shadow-[2px_2px_0px_0px_#fff] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none ${favorited ? "bg-accent text-black" : "bg-white dark:bg-black text-black dark:text-white hover:bg-gray-50 dark:hover:bg-gray-900"
                    }`}
            >
                <Star className={`w-5 h-5 ${favorited ? "fill-black" : ""}`} />
            </button>
            <button
                type="button"
                onClick={onShare}
                title={shared ? "Copied" : "Share"}
                className={`p-3 border-2 border-black dark:border-white rounded-lg transition-all neo-shadow hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_#000] dark:hover:shadow-[2px_2px_0px_0px_#fff] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none ${shared ? "bg-green-500 text-white" : "bg-white dark:bg-black text-black dark:text-white hover:bg-gray-50 dark:hover:bg-gray-900"
                    }`}
            >
                <Share2 className="w-5 h-5" />
            </button>
        </div>
    );
}
