"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/app/lib/api";
import { clearAdminSession, getAdminToken, setAdminToken } from "@/app/lib/admin-auth";

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
                    setError("Incorrect username or password.");
                    setLoading(false);
                    return;
                }
                // Unexpected error - log it
                const text = await res.text();
                setError(`Login error (${res.status})`);
                console.warn(`Login failed: ${res.status}`, text);
                return;
            }

            const data = await res.json();

            setAdminToken(data.access_token);
            router.replace("/admin/dashboard");

        } catch (err) {
            // Network errors etc
            setError("Connection failed. Please check network.");
            console.error("Login Network Error:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
            <div className="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-sm border border-gray-200">
                <div className="text-center">
                    <h2 className="mt-6 text-3xl font-extrabold text-gray-900">Admin Login</h2>
                    <p className="mt-2 text-sm text-gray-600">
                        Sign in to manage the marketplace (v1.2)
                    </p>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleLogin}>
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg text-sm">
                            {error}
                        </div>
                    )}
                    <div className="space-y-4">
                        <div>
                            <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                                Username
                            </label>
                            <input
                                id="username"
                                name="username"
                                type="text"
                                required
                                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                        </div>
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                                Password
                            </label>
                            <input
                                id="password"
                                name="password"
                                type="password"
                                required
                                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-lg shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className="group relative w-full flex justify-center py-2.5 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-colors"
                        >
                            {loading ? "Signing in..." : "Sign in"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
