import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { SkillCard } from "./SkillCard";

describe("SkillCard", () => {
    it("renders match reason and trust badge", () => {
        render(
            <SkillCard
                id="skill-1"
                name="Skill One"
                slug="skill-one"
                description="desc"
                summary="summary"
                category="Coding"
                views={10}
                stars={2}
                score={42}
                matchReason="hybrid: keyword + vector"
                trustLevel="ok"
                trustScore={87}
                trustFlags={["manual_reviewed"]}
            />,
        );

        expect(screen.getByText("Skill One")).toBeInTheDocument();
        expect(screen.getByText("hybrid: keyword + vector")).toBeInTheDocument();
        expect(screen.getByText("Trust 87")).toBeInTheDocument();
    });
});
