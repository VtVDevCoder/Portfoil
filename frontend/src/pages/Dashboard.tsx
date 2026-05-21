import { useCallback, useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useNavigate } from "react-router-dom";
import api from "../api/client";
import UploadForm from "../components/UploadForm";

interface AnalysisResult {
  sentiment: "POSITIVE" | "NEGATIVE" | "NEUTRAL";
  category: string;
  urgency_score: number;
  summary: string;
  processed_at: string;
}

interface FeedbackItem {
  id: string;
  raw_text: string;
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED";
  analysis?: AnalysisResult;
}

interface Stats {
  sentiment_distribution: { sentiment: string; count: number }[];
  top_categories: { category: string; count: number }[];
  recent_items: FeedbackItem[];
  total_batches: number;
  total_items: number;
}

const SENTIMENT_COLORS: Record<string, string> = {
  POSITIVE: "#22c55e",
  NEGATIVE: "#ef4444",
  NEUTRAL: "#f59e0b",
};

const STATUS_STYLES: Record<string, string> = {
  COMPLETED: "bg-green-900/50 text-green-400",
  FAILED: "bg-red-900/50 text-red-400",
  PROCESSING: "bg-yellow-900/50 text-yellow-400",
  PENDING: "bg-gray-800 text-gray-400",
};

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const fetchStats = useCallback(async () => {
    try {
      const res = await api.get<Stats>("/dashboard-stats/");
      setStats(res.data);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const id = setInterval(fetchStats, 5000);
    return () => clearInterval(id);
  }, [fetchStats]);

  const handleLogout = () => {
    localStorage.clear();
    navigate("/login");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex items-center justify-center">
        <div className="text-gray-400 text-sm">Loading…</div>
      </div>
    );
  }

  const sentimentData =
    stats?.sentiment_distribution.map((d) => ({
      name: d.sentiment,
      value: d.count,
    })) ?? [];

  const categoryData =
    stats?.top_categories.map((d) => ({
      name: d.category,
      count: d.count,
    })) ?? [];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold">ReviewPulse</h1>
            <p className="text-gray-400 text-sm mt-0.5">
              AI-powered feedback analysis
            </p>
          </div>
          <button
            onClick={handleLogout}
            className="text-gray-400 hover:text-white text-sm transition-colors"
          >
            Logout
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Total Batches", value: stats?.total_batches ?? 0 },
            { label: "Total Feedbacks", value: stats?.total_items ?? 0 },
            {
              label: "Analyzed",
              value:
                stats?.recent_items.filter((i) => i.status === "COMPLETED")
                  .length ?? 0,
            },
            {
              label: "Pending",
              value:
                stats?.recent_items.filter(
                  (i) => i.status === "PENDING" || i.status === "PROCESSING",
                ).length ?? 0,
            },
          ].map(({ label, value }) => (
            <div
              key={label}
              className="bg-gray-900 rounded-xl p-5 border border-gray-800"
            >
              <p className="text-gray-400 text-xs uppercase tracking-wider">
                {label}
              </p>
              <p className="text-3xl font-bold mt-1.5">{value}</p>
            </div>
          ))}
        </div>

        {/* Upload */}
        <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
          <h2 className="text-base font-semibold mb-4">Upload Feedbacks</h2>
          <UploadForm onSuccess={fetchStats} />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <h2 className="text-base font-semibold mb-4">
              Sentiment Distribution
            </h2>
            {sentimentData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <PieChart>
                  <Pie
                    data={sentimentData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {sentimentData.map((entry) => (
                      <Cell
                        key={entry.name}
                        fill={SENTIMENT_COLORS[entry.name] ?? "#6b7280"}
                      />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#111827",
                      border: "1px solid #1f2937",
                      borderRadius: "8px",
                    }}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[220px] flex items-center justify-center text-gray-500 text-sm">
                No data yet — upload feedbacks above
              </div>
            )}
          </div>

          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <h2 className="text-base font-semibold mb-4">Top Categories</h2>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart
                  data={categoryData}
                  margin={{ top: 0, right: 0, left: -20, bottom: 0 }}
                >
                  <XAxis
                    dataKey="name"
                    tick={{ fill: "#9ca3af", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: "#9ca3af", fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#111827",
                      border: "1px solid #1f2937",
                      borderRadius: "8px",
                    }}
                    cursor={{ fill: "rgba(99,102,241,0.1)" }}
                  />
                  <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[220px] flex items-center justify-center text-gray-500 text-sm">
                No data yet — upload feedbacks above
              </div>
            )}
          </div>
        </div>

        {/* Table */}
        <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
          <div className="p-5 border-b border-gray-800">
            <h2 className="text-base font-semibold">Recent Feedbacks</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 text-xs uppercase tracking-wider border-b border-gray-800">
                  {[
                    "Feedback",
                    "Status",
                    "Sentiment",
                    "Category",
                    "Urgency",
                    "Summary",
                  ].map((h) => (
                    <th key={h} className="text-left px-4 py-3 font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800/60">
                {stats?.recent_items.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-gray-800/30 transition-colors"
                  >
                    <td className="px-4 py-3 max-w-[180px] truncate text-gray-300 font-mono text-xs">
                      {item.raw_text}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${STATUS_STYLES[item.status]}`}
                      >
                        {item.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {item.analysis && (
                        <span
                          className="text-xs font-semibold"
                          style={{
                            color: SENTIMENT_COLORS[item.analysis.sentiment],
                          }}
                        >
                          {item.analysis.sentiment}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-300 text-xs">
                      {item.analysis?.category ?? "—"}
                    </td>
                    <td className="px-4 py-3">
                      {item.analysis && (
                        <span
                          className={`font-bold text-sm ${
                            item.analysis.urgency_score >= 4
                              ? "text-red-400"
                              : item.analysis.urgency_score >= 3
                                ? "text-yellow-400"
                                : "text-green-400"
                          }`}
                        >
                          {item.analysis.urgency_score}/5
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs max-w-[240px] truncate">
                      {item.analysis?.summary ?? "—"}
                    </td>
                  </tr>
                ))}
                {!stats?.recent_items.length && (
                  <tr>
                    <td
                      colSpan={6}
                      className="px-4 py-10 text-center text-gray-500 text-sm"
                    >
                      No feedbacks yet. Upload some above to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
