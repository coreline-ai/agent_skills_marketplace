"use client";

import { useEffect, useState } from "react";
import { api } from "@/app/lib/api";
import Link from "next/link";
import { ArrowUpRight, CheckCircle, Clock, AlertCircle } from "lucide-react";

export default function AdminDashboardPage() {
    // In a real app we'd fetch stats
    // const [stats, setStats] = useState(null);

    return (
        <div className="space-y-8">
            <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 font-medium">Total Skills</h3>
                        <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
                            <CheckCircle className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">124</p>
                    <p className="text-sm text-green-600 mt-2 flex items-center gap-1">
                        <ArrowUpRight className="w-4 h-4" /> +12% this week
                    </p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 font-medium">Pending Review</h3>
                        <div className="p-2 bg-yellow-50 text-yellow-600 rounded-lg">
                            <Clock className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">8</p>
                    <p className="text-sm text-gray-500 mt-2">
                        Needs attention
                    </p>
                    <div className="mt-4">
                        <Link href="/admin/skills?status=pending" className="text-sm text-blue-600 hover:underline">
                            View all pending
                        </Link>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-gray-500 font-medium">Flagged Issues</h3>
                        <div className="p-2 bg-red-50 text-red-600 rounded-lg">
                            <AlertCircle className="w-5 h-5" />
                        </div>
                    </div>
                    <p className="text-3xl font-bold text-gray-900">3</p>
                    <p className="text-sm text-gray-500 mt-2">
                        Quality alerts
                    </p>
                    <div className="mt-4">
                        <Link href="/admin/quality" className="text-sm text-blue-600 hover:underline">
                            Review issues
                        </Link>
                    </div>
                </div>
            </div>

            {/* Recent Activity Section placeholder */}
            <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="font-bold text-gray-900">Recent Raw Skills Ingested</h3>
                </div>
                <div className="p-6 text-center text-gray-500">
                    Loading recent activity...
                </div>
            </div>
        </div>
    );
}
