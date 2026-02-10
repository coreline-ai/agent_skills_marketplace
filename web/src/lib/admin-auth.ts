const ADMIN_TOKEN_KEY = "token";
const LEGACY_ADMIN_TOKEN_KEY = "admin_token";

export function getAdminToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem(ADMIN_TOKEN_KEY);
}

export function setAdminToken(token: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem(ADMIN_TOKEN_KEY, token);
    localStorage.removeItem(LEGACY_ADMIN_TOKEN_KEY);
}

export function clearAdminSession(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem(ADMIN_TOKEN_KEY);
    localStorage.removeItem(LEGACY_ADMIN_TOKEN_KEY);
}
