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
            setError("연결에 실패했습니다. 네트워크를 확인해주세요.");
            console.error("Login Network Error:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-black py-12 px-4 sm:px-6 lg:px-8 font-sans selection:bg-white/20">
            <div className="max-w-md w-full space-y-10 bg-zinc-950 p-10 rounded-[40px] shadow-[0_0_50px_-12px_rgba(255,255,255,0.05)] border border-white/5 relative overflow-hidden ring-1 ring-white/10">
                {/* Decoration */}
                <div className="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-zinc-800 via-white/20 to-zinc-800"></div>

                <div className="text-center space-y-4">
                    <div className="mx-auto h-14 w-14 bg-white rounded-2xl flex items-center justify-center text-black shadow-[0_0_20px_rgba(255,255,255,0.2)] mb-8 transform -rotate-2 hover:rotate-0 transition-all duration-500 cursor-default">
                        <Lock className="h-7 w-7" />
                    </div>
                    <h2 className="text-4xl font-extrabold text-white tracking-tight">Admin Console</h2>
                    <p className="text-sm text-zinc-500 font-semibold uppercase tracking-widest">
                        Marketplace Management (v1.2)
                    </p>
                </div>

                <form className="mt-10 space-y-8" onSubmit={handleLogin}>
                    {error && (
                        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-5 py-4 rounded-2xl text-sm font-bold flex items-center gap-3 animate-in fade-in slide-in-from-top-2 duration-300">
                            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" className="shrink-0"><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></svg>
                            {error}
                        </div>
                    )}
                    <div className="space-y-4">
                        <div className="relative group">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-600 group-focus-within:text-white transition-colors duration-300">
                                <User className="h-5 w-5" />
                            </div>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                required
                                className="block w-full pl-12 pr-4 py-4 bg-white/5 border border-white/5 rounded-2xl text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-white/10 focus:border-white/20 transition-all duration-300 font-medium text-sm"
                                placeholder="사용자 이름"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                        </div>
                        <div className="relative group">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-zinc-600 group-focus-within:text-white transition-colors duration-300">
                                <Lock className="h-5 w-5" />
                            </div>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                className="block w-full pl-12 pr-4 py-4 bg-white/5 border border-white/5 rounded-2xl text-white placeholder-zinc-600 focus:outline-none focus:ring-2 focus:ring-white/10 focus:border-white/20 transition-all duration-300 font-medium text-sm"
                                placeholder="비밀번호"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="group relative w-full flex justify-center py-4.5 px-4 border border-transparent text-sm font-black rounded-2xl text-black bg-white hover:bg-zinc-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-white disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 shadow-[0_8px_20px_-4px_rgba(255,255,255,0.2)] hover:shadow-[0_12px_25px_-4px_rgba(255,255,255,0.3)] hover:-translate-y-1 active:translate-y-0 uppercase tracking-widest"
                        >
                            {loading ? (
                                <span className="flex items-center gap-3">
                                    <svg className="animate-spin h-5 w-5 text-black" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
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
                <p className="mt-8 text-center text-xs font-bold text-zinc-600 uppercase tracking-widest">
                    Authorized Personnel Only
                </p>
            </div>
        </div>
    );
}
