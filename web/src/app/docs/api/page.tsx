import Link from "next/link";

export const dynamic = "force-dynamic";

export default function DeveloperApiDocsPage() {
    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <header className="space-y-3">
                <h1 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-white">Developer API</h1>
                <p className="text-sm text-gray-600 dark:text-zinc-400">
                    API key based access for listing and reading marketplace skills.
                </p>
            </header>

            <section className="space-y-3">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Authentication</h2>
                <div className="rounded-xl border border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-900/40 p-4">
                    <p className="text-sm text-gray-700 dark:text-zinc-300 mb-2">
                        Send API key via <code className="font-mono">x-api-key</code> header.
                    </p>
                    <pre className="text-xs font-mono overflow-x-auto">
{`x-api-key: skm_xxxxx_xxxxxxxxxxxxxxxxx`}
                    </pre>
                </div>
            </section>

            <section className="space-y-3">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Endpoints</h2>
                <div className="space-y-3 text-sm">
                    <div className="rounded-lg border border-gray-200 dark:border-zinc-800 p-3">
                        <code className="font-mono">GET /api/developer/skills</code>
                        <p className="text-gray-600 dark:text-zinc-400 mt-1">List skills (q/category/tags/page/size).</p>
                    </div>
                    <div className="rounded-lg border border-gray-200 dark:border-zinc-800 p-3">
                        <code className="font-mono">GET /api/developer/skills/{`{id}`}</code>
                        <p className="text-gray-600 dark:text-zinc-400 mt-1">Get skill detail by ID.</p>
                    </div>
                    <div className="rounded-lg border border-gray-200 dark:border-zinc-800 p-3">
                        <code className="font-mono">GET /api/developer/usage</code>
                        <p className="text-gray-600 dark:text-zinc-400 mt-1">Get key usage (daily/monthly).</p>
                    </div>
                </div>
            </section>

            <section className="space-y-3">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Error Codes</h2>
                <ul className="text-sm text-gray-700 dark:text-zinc-300 space-y-1">
                    <li><code className="font-mono">missing_api_key</code></li>
                    <li><code className="font-mono">invalid_api_key</code></li>
                    <li><code className="font-mono">api_key_expired</code></li>
                    <li><code className="font-mono">insufficient_scope</code></li>
                    <li><code className="font-mono">rate_limit_exceeded</code></li>
                </ul>
            </section>

            <section className="space-y-3">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Sandbox Key</h2>
                <p className="text-sm text-gray-600 dark:text-zinc-400">
                    For local/integration testing, issue a short-lived key with low rate limit (for example: 3 req/min).
                </p>
                <pre className="text-xs font-mono overflow-x-auto rounded-xl border border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-900/40 p-4">
{`curl -X POST "http://localhost:8000/api/admin/api-keys" \\
  -H "Authorization: Bearer $ADMIN_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d '{"name":"sandbox-local","scopes":["read"],"rate_limit_per_minute":3}'`}
                </pre>
            </section>

            <section className="space-y-3">
                <h2 className="text-lg font-bold text-gray-900 dark:text-white">Examples</h2>
                <div className="space-y-4">
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-zinc-500 mb-2">cURL</p>
                        <pre className="text-xs font-mono overflow-x-auto rounded-xl border border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-900/40 p-4">
{`curl -H "x-api-key: $API_KEY" "http://localhost:8000/api/developer/skills?q=coding&size=10"`}
                        </pre>
                    </div>
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-zinc-500 mb-2">TypeScript</p>
                        <pre className="text-xs font-mono overflow-x-auto rounded-xl border border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-900/40 p-4">
{`const res = await fetch("http://localhost:8000/api/developer/skills?q=agent", {
  headers: { "x-api-key": process.env.API_KEY! }
});
const data = await res.json();`}
                        </pre>
                    </div>
                    <div>
                        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-zinc-500 mb-2">Python</p>
                        <pre className="text-xs font-mono overflow-x-auto rounded-xl border border-gray-200 dark:border-zinc-800 bg-gray-50 dark:bg-zinc-900/40 p-4">
{`import requests
resp = requests.get(
    "http://localhost:8000/api/developer/skills",
    params={"q": "agent"},
    headers={"x-api-key": API_KEY},
    timeout=10,
)
print(resp.json())`}
                        </pre>
                    </div>
                </div>
            </section>

            <footer className="text-sm text-gray-500 dark:text-zinc-500">
                Admin API key issuance endpoint: <code className="font-mono">POST /api/admin/api-keys</code>.
                {" "}
                <Link href="/guide" className="underline">Guide</Link>
            </footer>
        </div>
    );
}
