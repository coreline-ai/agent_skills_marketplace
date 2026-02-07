"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/app/lib/api";
import { clearAdminSession, getAdminToken, setAdminToken } from "@/app/lib/admin-auth";
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
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-[32px] shadow-2xl border border-gray-100/50 relative overflow-hidden">
                {/* Decoration */}
                <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-gray-900 to-gray-600"></div>

                <div className="text-center space-y-2">
                    <div className="mx-auto h-12 w-12 bg-gray-900 rounded-xl flex items-center justify-center text-white shadow-lg mb-6 transform rotate-3 hover:rotate-6 transition-transform">
                        <Lock className="h-6 w-6" />
                    </div>
                    <h2 className="text-3xl font-bold text-gray-900 tracking-tight">관리자 로그인</h2>
                    <p className="text-sm text-gray-500 font-medium">
                        마켓플레이스 관리를 위해 로그인하세요 (v1.2)
                    </p>
                </div>

                <form className="mt-8 space-y-6" onSubmit={handleLogin}>
                    {error && (
                        <div className="bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl text-sm font-medium flex items-center gap-2 animate-pulse">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-alert-circle"><circle cx="12" cy="12" r="10" /><line x1="12" x2="12" y1="8" y2="12" /><line x1="12" x2="12.01" y1="16" y2="16" /></svg>
                            {error}
                        </div>
                    )}
                    <div className="space-y-5">
                        <div className="relative group">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-gray-900 transition-colors">
                                <User className="h-5 w-5" />
                            </div>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                required
                                className="block w-full pl-10 pr-3 py-3 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 transition-all bg-gray-50 focus:bg-white font-medium sm:text-sm"
                                placeholder="사용자 이름"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                        </div>
                        <div className="relative group">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400 group-focus-within:text-gray-900 transition-colors">
                                <Lock className="h-5 w-5" />
                            </div>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                className="block w-full pl-10 pr-3 py-3 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900/10 focus:border-gray-900 transition-all bg-gray-50 focus:bg-white font-medium sm:text-sm"
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
                            className="group relative w-full flex justify-center py-3.5 px-4 border border-transparent text-sm font-bold rounded-xl text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900 disabled:opacity-70 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0"
                        >
                            {loading ? (
                                <span className="flex items-center gap-2">
                                    <svg className="animate-spin -ml-1 mr-3 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    로그인 중...
                                </span>
                            ) : (
                                "로그인"
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
