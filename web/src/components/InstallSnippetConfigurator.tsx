
"use client";

import { useState } from "react";
import { Check, Copy, Terminal } from "lucide-react";
import { CLIENTS, ClientType, generateInstallCommand, getClientConfigExample } from "@/lib/snippets";

interface InstallSnippetConfiguratorProps {
    skillUrl: string;
    skillName: string;
}

export function InstallSnippetConfigurator({ skillUrl, skillName }: InstallSnippetConfiguratorProps) {
    const [activeClient, setActiveClient] = useState<ClientType>("claude");
    const [copied, setCopied] = useState(false);

    const command = generateInstallCommand(activeClient, { skillUrl });
    const configExample = getClientConfigExample(activeClient, { skillUrl });

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(command);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error("Failed to copy", err);
        }
    };

    return (
        <div className="w-full bg-gray-50 dark:bg-zinc-900/50 rounded-xl border border-gray-200 dark:border-zinc-800 overflow-hidden">
            <div className="flex items-center gap-1 p-2 border-b border-gray-200 dark:border-zinc-800 overflow-x-auto scrolbar-hide">
                {CLIENTS.map((client) => (
                    <button
                        key={client.id}
                        onClick={() => setActiveClient(client.id)}
                        className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all whitespace-nowrap ${activeClient === client.id
                                ? "bg-white dark:bg-zinc-800 text-gray-900 dark:text-white shadow-sm ring-1 ring-gray-200 dark:ring-zinc-700"
                                : "text-gray-500 dark:text-zinc-500 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-zinc-800"
                            }`}
                    >
                        {client.label}
                    </button>
                ))}
            </div>

            <div className="p-4 space-y-4">
                <div className="space-y-2">
                    <div className="flex items-center justify-between">
                        <label className="text-xs font-bold text-gray-500 dark:text-zinc-500 uppercase tracking-wider">
                            Installation Command
                        </label>
                        {configExample && (
                            <span className="text-[10px] bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded-full font-medium">
                                Config Required
                            </span>
                        )}
                    </div>

                    <div className="relative group">
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 dark:text-zinc-600">
                            <Terminal className="w-4 h-4" />
                        </div>
                        <code className="block w-full bg-white dark:bg-black border border-gray-200 dark:border-zinc-800 rounded-lg py-3 pl-10 pr-12 text-sm font-mono text-gray-800 dark:text-zinc-300 overflow-x-auto">
                            {command}
                        </code>
                        <button
                            onClick={handleCopy}
                            className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
                            title="Copy to clipboard"
                        >
                            {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                        </button>
                    </div>
                </div>

                {configExample && (
                    <div className="space-y-2 pt-2 border-t border-gray-200 dark:border-zinc-800 border-dashed">
                        <label className="text-xs font-bold text-gray-500 dark:text-zinc-500 uppercase tracking-wider">
                            Configuration (e.g. claude_desktop_config.json)
                        </label>
                        <div className="relative">
                            <pre className="bg-white dark:bg-black border border-gray-200 dark:border-zinc-800 rounded-lg p-3 text-xs font-mono text-gray-600 dark:text-zinc-400 overflow-x-auto">
                                {configExample}
                            </pre>
                        </div>
                    </div>
                )}

                <p className="text-[10px] text-gray-400 dark:text-zinc-600">
                    * Requires <a href="https://modelcontextprotocol.io/" target="_blank" rel="noopener noreferrer" className="underline hover:text-gray-900 dark:hover:text-zinc-400">MCP CLI</a> or compatible client.
                </p>
            </div>
        </div>
    );
}
