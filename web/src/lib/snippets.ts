
export type ClientType = "claude" | "cursor" | "vscode" | "gemini" | "windsurf";

export interface SnippetOptions {
    skillUrl: string;
    skillId?: string;
    useSsh?: boolean;
}

export const CLIENTS: { id: ClientType; label: string; icon?: string }[] = [
    { id: "claude", label: "Claude Desktop" },
    { id: "cursor", label: "Cursor" },
    { id: "windsurf", label: "Windsurf" },
    { id: "vscode", label: "VS Code" },
    // { id: "gemini", label: "Google Gemini" }, // Future support
];

export function generateInstallCommand(client: ClientType, options: SnippetOptions): string {
    const { skillUrl } = options;

    switch (client) {
        case "claude":
            // Claude Desktop typically uses MCP config directly, but if there's a CLI tool:
            return `mcp install ${skillUrl}`;

        case "cursor":
            // Cursor might use a specific command or just add to rules
            return `@mcp-install ${skillUrl}`;

        case "windsurf":
            return `surf mcp add ${skillUrl}`;

        case "vscode":
            // Generic VS Code MCP extension usage
            return `code --install-extension myskill.extension\n# Then configure in settings.json to use: ${skillUrl}`;

        default:
            return `mcp install ${skillUrl}`;
    }
}

export function getClientConfigExample(client: ClientType, options: SnippetOptions): string {
    const { skillUrl } = options;

    if (client === "claude") {
        return JSON.stringify({
            "mcpServers": {
                "my-skill": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-universal", "install", skillUrl]
                }
            }
        }, null, 2);
    }
    return "";
}
