// Both server-side and client-side use the same public API URL on Render.
// NEXT_PUBLIC_API_URL is available on both sides.
export const getApiBaseUrl = () => {
    if (typeof window === 'undefined') {
        // Server-side
        return process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
    }
    // Client-side
    return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
};

export const API_BASE_URL = getApiBaseUrl();

type RequestMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
type NextFetchInit = RequestInit & { next?: { revalidate?: number } };

interface CacheProfile {
    ttlMs: number;
    staleWhileRevalidateMs: number;
}

interface ServerCacheEntry {
    data: unknown;
    freshUntil: number;
    staleUntil: number;
}

const SERVER_CACHE_MAX_ENTRIES = 400;
const isServerRuntime = typeof window === "undefined";
const serverResponseCache = new Map<string, ServerCacheEntry>();
const inflightRefreshes = new Map<string, Promise<unknown>>();

export class ApiError extends Error {
    status: number;
    constructor(status: number, statusText: string) {
        super(`API Error: ${status} ${statusText}`);
        this.name = "ApiError";
        this.status = status;
    }
}

interface RequestOptions {
    method?: RequestMethod;
    headers?: Record<string, string>;
    body?: unknown;
    token?: string;
    cache?: RequestCache;
    revalidateSeconds?: number;
}

function resolveCacheProfile(endpoint: string): CacheProfile | null {
    if (endpoint.startsWith("/admin") || endpoint.startsWith("/developer")) {
        return null;
    }

    if (endpoint.startsWith("/categories") || endpoint.startsWith("/taxonomy/") || endpoint.startsWith("/tags")) {
        return { ttlMs: 10 * 60 * 1000, staleWhileRevalidateMs: 60 * 60 * 1000 };
    }
    if (endpoint.startsWith("/rankings/")) {
        return { ttlMs: 30 * 1000, staleWhileRevalidateMs: 5 * 60 * 1000 };
    }
    if (endpoint.startsWith("/skills/")) {
        return { ttlMs: 60 * 1000, staleWhileRevalidateMs: 15 * 60 * 1000 };
    }
    if (endpoint.startsWith("/skills")) {
        return { ttlMs: 20 * 1000, staleWhileRevalidateMs: 2 * 60 * 1000 };
    }
    if (endpoint.startsWith("/packs")) {
        return { ttlMs: 60 * 1000, staleWhileRevalidateMs: 5 * 60 * 1000 };
    }
    if (endpoint.startsWith("/plugins")) {
        return { ttlMs: 60 * 1000, staleWhileRevalidateMs: 5 * 60 * 1000 };
    }
    return { ttlMs: 30 * 1000, staleWhileRevalidateMs: 2 * 60 * 1000 };
}

function isPublicReadRequest(method: RequestMethod, token?: string): boolean {
    return method === "GET" && !token;
}

function pruneServerCache(now: number): void {
    for (const [key, entry] of serverResponseCache.entries()) {
        if (entry.staleUntil <= now) {
            serverResponseCache.delete(key);
        }
    }
    while (serverResponseCache.size > SERVER_CACHE_MAX_ENTRIES) {
        const oldest = serverResponseCache.keys().next().value as string | undefined;
        if (!oldest) break;
        serverResponseCache.delete(oldest);
    }
}

function readServerCache(key: string, now: number): { state: "fresh" | "stale"; data: unknown } | null {
    const cached = serverResponseCache.get(key);
    if (!cached) return null;
    if (now <= cached.freshUntil) return { state: "fresh", data: cached.data };
    if (now <= cached.staleUntil) return { state: "stale", data: cached.data };
    serverResponseCache.delete(key);
    return null;
}

function writeServerCache(key: string, data: unknown, profile: CacheProfile, now: number): void {
    serverResponseCache.set(key, {
        data,
        freshUntil: now + profile.ttlMs,
        staleUntil: now + profile.ttlMs + profile.staleWhileRevalidateMs,
    });
    pruneServerCache(now);
}

async function fetchJson<T>(endpoint: string, fullUrl: string, config: NextFetchInit): Promise<T> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    const isDev = process.env.NODE_ENV !== "production";

    try {
        if (isDev) {
            console.log(`[API Request] ${config.method || "GET"} ${fullUrl}`);
        }

        const response = await fetch(fullUrl, {
            ...config,
            signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (!response.ok) {
            if (response.status === 401) {
                throw new ApiError(response.status, response.statusText);
            }
            if (isDev) {
                console.error(`[API Error] ${response.status} ${response.statusText} at ${fullUrl}`);
            }
            throw new ApiError(response.status, response.statusText);
        }

        if (response.status === 204) {
            return {} as T;
        }

        return response.json() as Promise<T>;
    } catch (error) {
        clearTimeout(timeoutId);
        console.error(`[API Fetch Failed] ${endpoint}:`, error);
        throw error;
    }
}

async function fetchWithServerCache<T>(
    {
        endpoint,
        fullUrl,
        config,
        profile,
    }: {
        endpoint: string;
        fullUrl: string;
        config: NextFetchInit;
        profile: CacheProfile;
    },
): Promise<T> {
    const key = `${config.method || "GET"}:${fullUrl}`;
    const now = Date.now();
    const cached = readServerCache(key, now);

    const runRefresh = async () => {
        const existing = inflightRefreshes.get(key);
        if (existing) return existing as Promise<T>;
        const refresh = fetchJson<T>(endpoint, fullUrl, config)
            .then((data) => {
                writeServerCache(key, data, profile, Date.now());
                return data;
            })
            .finally(() => {
                inflightRefreshes.delete(key);
            });
        inflightRefreshes.set(key, refresh as Promise<unknown>);
        return refresh;
    };

    if (cached?.state === "fresh") {
        return cached.data as T;
    }
    if (cached?.state === "stale") {
        void runRefresh();
        return cached.data as T;
    }
    return runRefresh();
}

export async function fetchApi<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
    const { method = "GET", headers = {}, body, token, cache, revalidateSeconds } = options;
    const canUseCache = isPublicReadRequest(method, token);

    const config: NextFetchInit = {
        method,
        headers: {
            "Content-Type": "application/json",
            ...headers,
        },
        cache: cache ?? (canUseCache ? "default" : "no-store"),
    };

    if (token) {
        config.headers = {
            ...config.headers,
            Authorization: `Bearer ${token}`,
        };
    }

    if (body !== undefined) {
        config.body = JSON.stringify(body);
    }

    if (canUseCache && typeof revalidateSeconds === "number" && revalidateSeconds > 0) {
        config.next = { revalidate: revalidateSeconds };
    }

    const fullUrl = `${API_BASE_URL}${endpoint}`;
    const serverCacheEnabled =
        isServerRuntime &&
        canUseCache &&
        process.env.NEXT_DISABLE_SERVER_CACHE !== "1" &&
        config.cache !== "no-store";
    const profile = resolveCacheProfile(endpoint);

    if (serverCacheEnabled && profile) {
        return fetchWithServerCache<T>({ endpoint, fullUrl, config, profile });
    }
    return fetchJson<T>(endpoint, fullUrl, config);
}

// Helper methods
export const api = {
    get: <T>(
        endpoint: string,
        token?: string,
        options?: Omit<RequestOptions, "method" | "body" | "token">,
    ) => fetchApi<T>(endpoint, { method: "GET", token, ...(options || {}) }),
    post: <T>(endpoint: string, body: unknown, token?: string) =>
        fetchApi<T>(endpoint, { method: "POST", body, token }),
    patch: <T>(endpoint: string, body: unknown, token?: string) =>
        fetchApi<T>(endpoint, { method: "PATCH", body, token }),
    delete: <T>(endpoint: string, token?: string) => fetchApi<T>(endpoint, { method: "DELETE", token }),
};
