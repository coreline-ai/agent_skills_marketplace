export type SearchMode = "keyword" | "vector" | "hybrid";

export function buildSkillsHref(params: {
    q?: string;
    category?: string;
    page?: number;
    mode?: SearchMode;
}) {
    const query = new URLSearchParams();
    if (params.q) query.set("q", params.q);
    if (params.category) query.set("category", params.category);
    if (params.page && params.page > 1) query.set("page", params.page.toString());
    if (params.mode) query.set("mode", params.mode);
    const queryString = query.toString();
    return queryString ? `/skills?${queryString}` : "/skills";
}
