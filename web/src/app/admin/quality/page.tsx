"use client";

import { ShieldAlert, ShieldCheck } from "lucide-react";

const MOCK_QUALITY_ISSUES = [
    { id: "1", name: "Legacy Skill", issue: "Description too short", severity: "medium" },
    { id: "2", name: "Broken Wrapper", issue: "Missing input schema", severity: "high" },
];

export default function AdminQualityPage() {
    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-900">Quality Control</h1>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-green-50 text-green-600 rounded-lg">
                            <ShieldCheck className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-900">Quality Score</h3>
                            <p className="text-sm text-gray-500">Overall marketplace health</p>
                        </div>
                    </div>
                    <div className="text-4xl font-extrabold text-gray-900">92<span className="text-lg text-gray-400 font-normal">/100</span></div>
                </div>

                <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-red-50 text-red-600 rounded-lg">
                            <ShieldAlert className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="font-bold text-gray-900">Critical Issues</h3>
                            <p className="text-sm text-gray-500">Requires immediate action</p>
                        </div>
                    </div>
                    <div className="text-4xl font-extrabold text-gray-900">{MOCK_QUALITY_ISSUES.length}</div>
                </div>
            </div>

            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="font-bold text-gray-900">Detected Issues</h3>
                </div>
                <ul className="divide-y divide-gray-200">
                    {MOCK_QUALITY_ISSUES.map((item) => (
                        <li key={item.id} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50">
                            <div>
                                <h4 className="font-semibold text-gray-900">{item.name}</h4>
                                <p className="text-sm text-gray-500">{item.issue}</p>
                            </div>
                            <span className={`px-2 py-1 text-xs font-bold rounded-full uppercase ${item.severity === 'high' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                                }`}>
                                {item.severity}
                            </span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}
