"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { clearAdminSession, getAdminToken, setAdminToken } from "@/lib/admin-auth";
import { Lock, User } from "lucide-react";

export default function AdminLoginPage() {
    const router = useRouter();
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const token = getAdminToken();
        if (!token) return;

        api.get<{ username: string }>("/admin/me", token)
            .then(() => {
                router.replace("/admin/dashboard");
            })
            .catch((error) => {
                if (error instanceof ApiError && error.status === 401) {
                    clearAdminSession();
                }
            });
    }, [router]);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        try {
            const formData = new URLSearchParams();
            formData.append("username", username);
            formData.append("password", password);
            formData.append("grant_type", "password"); // Required for OAuth2PasswordRequestForm

            const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
            // Let fetch handle the Content-Type header for URLSearchParams (application/x-www-form-urlencoded)
            const res = await fetch(`${baseUrl}/admin/login`, {
                method: "POST",
                body: formData // URLSearchParams object
            });

            if (!res.ok) {
                // Expected error (wrong password, etc) - Do not log to console as "Error"
                if (res.status === 401) {
                    setError("잘못된 사용자 이름 또는 비밀번호입니다.");
                    setLoading(false);
                    return;
                }
                // Unexpected error - log it
                const text = await res.text();
                setError(`로그인 오류 (${res.status})`);
                console.warn(`Login failed: ${res.status}`, text);
                return;
            }

            const data = await res.json();

            setAdminToken(data.access_token);
            router.replace("/admin/dashboard");

        } catch (err) {
            // Network errors etc
            setError(`연결에 실패했습니다: ${err instanceof Error ? err.message : String(err)}`);
            console.error("Login Network Error:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-black py-12 px-4 sm:px-6 lg:px-8 font-sans selection:bg-white/20">
            <div className="max-w-[400px] w-full space-y-8 bg-zinc-950 p-8 rounded-3xl shadow-[0_0_50px_-12px_rgba(255,255,255,0.05)] border border-white/10 relative overflow-hidden group/container transition-all duration-500">
                {/* Decoration */}
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white/10 to-transparent group-hover/container:via-white/20 transition-all duration-500"></div>

                <div className="text-center space-y-3">
                    <div className="mx-auto h-12 w-12 bg-white rounded-xl flex items-center justify-center text-black shadow-[0_0_20px_rgba(255,255,255,0.1)] mb-6 transform -rotate-1 hover:rotate-0 transition-all duration-500 cursor-default">
                        <Lock className="h-6 w-6" />
                    </div>
                    <h2 className="text-3xl font-bold text-white tracking-tight">Admin Console</h2>
                    <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-[0.2em]">
                        Marketplace Management (v1.2)
                    </p>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleLogin}>
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl text-xs font-bold flex items-center gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0"><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></svg>
                            {error}
                        </div>
                    )}
                    <div className="space-y-3">
                        <div className="relative group">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-600 group-focus-within:text-white transition-colors duration-300">
                                <User className="h-4 w-4" />
                            </div>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                required
                                className="block w-full pl-11 pr-4 py-3.5 bg-white/5 border border-white/5 rounded-xl text-white placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-white/20 focus:border-white/20 transition-all duration-300 font-medium text-xs shadow-inner"
                                placeholder="사용자 이름"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                        </div>
                        <div className="relative group">
                            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-zinc-600 group-focus-within:text-white transition-colors duration-300">
                                <Lock className="h-4 w-4" />
                            </div>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                className="block w-full pl-11 pr-4 py-3.5 bg-white/5 border border-white/5 rounded-xl text-white placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-white/20 focus:border-white/20 transition-all duration-300 font-medium text-xs shadow-inner"
                                placeholder="비밀번호"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="pt-2">
                        <button
                            type="submit"
                            disabled={loading}
                            className="group relative w-full flex justify-center py-4 px-4 border border-transparent text-xs font-black rounded-xl text-black bg-white hover:bg-zinc-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-[0_4px_12px_rgba(255,255,255,0.1)] hover:shadow-[0_8px_20px_rgba(255,255,255,0.15)] hover:-translate-y-0.5 active:translate-y-0 uppercase tracking-[0.2em]"
                        >
                            {loading ? (
                                <span className="flex items-center gap-2">
                                    <svg className="animate-spin h-4 w-4 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Verifying...
                                </span>
                            ) : (
                                "Sign In"
                            )}
                        </button>
                    </div>
                </form>

                {/* Footer text */}
                <p className="mt-8 text-center text-[10px] font-bold text-zinc-600 uppercase tracking-[0.3em]">
                    Authorized Personnel Only
                </p>
            </div>
        </div>
    );
}
