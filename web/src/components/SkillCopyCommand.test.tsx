import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { SkillCopyCommand } from "./SkillCopyCommand";

vi.mock("@/lib/api", () => ({
    api: {
        post: vi.fn(),
    },
}));

describe("SkillCopyCommand", () => {
    it("shows all client tabs and missing source message", () => {
        render(
            <SkillCopyCommand
                skillId="skill-1"
                slug="skill-one"
                installUrl={null}
                sourceLinks={[]}
            />,
        );

        expect(screen.getByRole("button", { name: "Claude" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Cursor" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "VSCode" })).toBeInTheDocument();
        expect(screen.getByRole("button", { name: "Gemini" })).toBeInTheDocument();

        expect(
            screen.getByText("Source URL is required for install snippet generation. Use docs/source link first."),
        ).toBeInTheDocument();
        expect(screen.getByText(/Source URL is missing\./)).toBeInTheDocument();
    });
});
