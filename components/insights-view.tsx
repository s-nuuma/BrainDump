"use client";

import { useState, useEffect } from "react";
import { Activity, Hash, Target } from "lucide-react";

interface InsightData {
  sentiment_trend: { date: string; score: number }[];
  top_topics: { topic: string; count: number }[];
  total_entries: number;
  actionable_ratio: number;
}

export function InsightsView({ userId }: { userId: string }) {
  const [data, setData] = useState<InsightData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [days, setDays] = useState(30);

  useEffect(() => {
    const fetchInsights = async () => {
      setIsLoading(true);
      try {
        const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
        const res = await fetch(`${backendUrl}/api/insights?user_id=${userId}&days=${days}`);
        if (!res.ok) throw new Error("Failed to fetch insights");
        
        const json = await res.json();
        setData(json.data);
      } catch (e: any) {
        setError(e.message || "分析データの取得に失敗しました");
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchInsights();
  }, [days]);

  if (isLoading) return <div className="text-center py-12 text-zinc-500">Loading insights...</div>;
  if (error) return <div className="text-center py-12 text-red-500">{error}</div>;
  if (!data) return null;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-semibold text-zinc-100">Insights</h2>
        <select 
          value={days} 
          onChange={(e) => setDays(Number(e.target.value))}
          className="bg-zinc-900 border border-zinc-800 text-zinc-300 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-zinc-700 cursor-pointer"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
          <div className="flex items-center gap-2 text-zinc-400 mb-2"><Activity className="w-4 h-4" /> Total Dumps</div>
          <div className="text-4xl font-light text-zinc-100">{data.total_entries}</div>
        </div>
        <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
          <div className="flex items-center gap-2 text-zinc-400 mb-2"><Target className="w-4 h-4" /> Actionable Ratio</div>
          <div className="text-4xl font-light text-zinc-100">{data.actionable_ratio}%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
          <h3 className="text-lg font-medium text-zinc-200 mb-6 flex items-center gap-2">
            <Hash className="w-5 h-5 text-zinc-500" />
            Top Topics
          </h3>
          <div className="space-y-4">
            {data.top_topics.map((item, i) => {
              const maxCount = data.top_topics[0]?.count || 1;
              const width = Math.max(1, (item.count / maxCount) * 100);
              return (
                <div key={i} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-zinc-300">{item.topic}</span>
                    <span className="text-zinc-500">{item.count}</span>
                  </div>
                  <div className="w-full bg-zinc-800 rounded-full h-2">
                    <div className="bg-zinc-400 h-2 rounded-full" style={{ width: `${width}%` }}></div>
                  </div>
                </div>
              )
            })}
            {data.top_topics.length === 0 && <p className="text-sm text-zinc-500">No topics found.</p>}
          </div>
        </div>

        <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl">
          <h3 className="text-lg font-medium text-zinc-200 mb-6 flex items-center gap-2">
            <Activity className="w-5 h-5 text-zinc-500" />
            Sentiment Trend (Daily Avg)
          </h3>
          <div className="space-y-3">
            {data.sentiment_trend.map((item, i) => {
              const posWidth = item.score > 0 ? (item.score * 100) : 0;
              const negWidth = item.score < 0 ? (-item.score * 100) : 0;
              return (
                <div key={i} className="flex items-center gap-4 text-sm">
                  <span className="text-zinc-500 w-24 tabular-nums">{item.date}</span>
                  <div className="flex-1 flex items-center h-4 relative">
                    <div className="w-1/2 h-full flex justify-end pr-1">
                      {item.score < 0 && <div className="bg-red-500/50 h-full rounded-l-sm" style={{ width: `${negWidth}%` }}></div>}
                    </div>
                    <div className="w-px h-6 bg-zinc-700 absolute left-1/2 -translate-x-1/2 z-10"></div>
                    <div className="w-1/2 h-full pl-1">
                      {item.score > 0 && <div className="bg-green-500/50 h-full rounded-r-sm" style={{ width: `${posWidth}%` }}></div>}
                    </div>
                  </div>
                  <span className="text-zinc-500 w-12 text-right">{item.score.toFixed(2)}</span>
                </div>
              )
            })}
            {data.sentiment_trend.length === 0 && <p className="text-sm text-zinc-500">No sentiment data found.</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
