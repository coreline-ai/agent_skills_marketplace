import { describe, expect, it } from "vitest";

import { buildSkillsHref } from "./skills-search";

describe("buildSkillsHref", () => {
    it("returns base path when params are empty", () => {
        expect(buildSkillsHref({})).toBe("/skills");
    });

    it("builds query with q/category/mode", () => {
        expect(
            buildSkillsHref({
                q: "agent",
                category: "coding",
                mode: "hybrid",
            }),
        ).toBe("/skills?q=agent&category=coding&mode=hybrid");
    });

    it("omits page when page <= 1", () => {
        expect(
            buildSkillsHref({
                q: "agent",
                page: 1,
                mode: "keyword",
            }),
        ).toBe("/skills?q=agent&mode=keyword");
    });

    it("includes page when page > 1", () => {
        expect(
            buildSkillsHref({
                q: "agent",
                page: 3,
                mode: "vector",
            }),
        ).toBe("/skills?q=agent&page=3&mode=vector");
    });
});
