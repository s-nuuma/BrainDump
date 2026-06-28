"use client";

import { useState, useEffect } from "react";
import { Trash2, Download, Search, Tag } from "lucide-react";

interface Entry {
  id: string;
  content: string;
  summary: string;
  topic: string[];
  sentiment: {
    score: number;
    label: string;
  };
  is_actionable: boolean;
  created_at: string;
}

export function HistoryView({ userId }: { userId: string }) {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTag, setSelectedTag] = useState<string>("");

  const fetchEntries = async (tag?: string) => {
    setIsLoading(true);
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      let url = `${backendUrl}/api/entries?user_id=${userId}`;
      if (tag) url += `&tag=${encodeURIComponent(tag)}`;
      
      const res = await fetch(url);
      if (!res.ok) throw new Error("Failed to fetch entries");
      
      const data = await res.json();
      setEntries(data.data);
    } catch (e: any) {
      setError(e.message || "履歴の取得に失敗しました");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchEntries(selectedTag);
  }, [selectedTag]);

  const handleDelete = async (id: string) => {
    if (!confirm("本当に削除しますか？")) return;
    
    try {
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const res = await fetch(`${backendUrl}/api/entries/${id}?user_id=${userId}`, {
        method: "DELETE"
      });
      if (!res.ok) throw new Error("Failed to delete");
      
      setEntries(entries.filter(e => e.id !== id));
    } catch (e) {
      alert("削除に失敗しました");
    }
  };

  const handleExport = () => {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
    window.open(`${backendUrl}/api/export?user_id=${userId}`, '_blank');
  };

  const formatDate = (dateValue: any) => {
    if (!dateValue) return "Unknown Date";
    try {
      // Handle Firebase timestamp or ISO string
      const date = typeof dateValue === 'string' ? new Date(dateValue) : new Date(dateValue._seconds * 1000);
      return date.toLocaleString();
    } catch (e) {
      return "Invalid Date";
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-2xl font-semibold text-zinc-100">Archive</h2>
        <div className="flex gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-zinc-500" />
            <input 
              type="text" 
              placeholder="Filter by tag..." 
              value={selectedTag}
              onChange={(e) => setSelectedTag(e.target.value)}
              className="pl-9 pr-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-zinc-700 text-zinc-200 placeholder-zinc-500"
            />
          </div>
          <button 
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-lg text-sm transition-colors"
          >
            <Download className="h-4 w-4" />
            Export
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-zinc-500">Loading archives...</div>
      ) : error ? (
        <div className="text-center py-12 text-red-500">{error}</div>
      ) : entries.length === 0 ? (
        <div className="text-center py-12 text-zinc-500">記録がありません</div>
      ) : (
        <div className="space-y-4">
          {entries.map((entry) => (
            <div key={entry.id} className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:border-zinc-700 transition-colors">
              <div className="flex justify-between items-start mb-4">
                <div className="flex flex-wrap gap-2">
                  {entry.topic?.map((t, i) => (
                    <span key={i} className="flex items-center gap-1 text-xs px-2 py-1 bg-zinc-800 text-zinc-300 rounded-full">
                      <Tag className="h-3 w-3" />
                      {t}
                    </span>
                  ))}
                  <span className={`text-xs px-2 py-1 rounded-full ${entry.sentiment?.score > 0 ? 'bg-green-500/10 text-green-400' : entry.sentiment?.score < 0 ? 'bg-red-500/10 text-red-400' : 'bg-blue-500/10 text-blue-400'}`}>
                    {entry.sentiment?.label}
                  </span>
                  {entry.is_actionable && (
                    <span className="text-xs px-2 py-1 bg-yellow-500/10 text-yellow-400 rounded-full">Actionable</span>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-xs text-zinc-500">
                    {formatDate(entry.created_at)}
                  </span>
                  <button 
                    onClick={() => handleDelete(entry.id)}
                    className="text-zinc-600 hover:text-red-400 transition-colors"
                    title="Delete entry"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
              <h3 className="text-lg font-medium text-zinc-200 mb-2">{entry.summary}</h3>
              <p className="text-sm text-zinc-500 italic border-l-2 border-zinc-800 pl-4">{entry.content}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
