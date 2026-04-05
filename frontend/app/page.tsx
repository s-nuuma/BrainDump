"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [status, setStatus] = useState<string>("Checking...");

  useEffect(() => {
    // Backend (FastAPI) のヘルスチェック
    const checkBackend = async () => {
      try {
        const res = await fetch("http://localhost:8000/health");
        const data = await res.json();
        setStatus(data.status === "ok" ? "Connected" : "Error");
      } catch (e) {
        setStatus("Offline (Backend not running)");
      }
    };
    checkBackend();
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-8 md:p-24 bg-[#0a0a0a] text-[#ededed]">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-800 bg-zinc-900/30 pb-6 pt-8 backdrop-blur-2xl lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-zinc-800/30 lg:p-4">
          BrainDump&nbsp;
          <code className="font-bold">v0.1.0-mvp</code>
        </p>
        <div className="fixed bottom-0 left-0 flex h-48 w-full items-end justify-center bg-gradient-to-t from-black via-black lg:static lg:h-auto lg:w-auto lg:bg-none">
          <div className="flex items-center gap-2 p-8 lg:p-0">
            <span className={`h-2 w-2 rounded-full ${status === "Connected" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500"}`}></span>
            <span className="text-xs text-zinc-400 uppercase tracking-widest">{status}</span>
          </div>
        </div>
      </div>

      <div className="relative flex place-items-center">
        <div className="flex flex-col items-center text-center space-y-8">
          <h1 className="text-5xl md:text-7xl font-light tracking-tighter text-zinc-100">
            Dump your <span className="text-zinc-500 italic">chaos</span>.
          </h1>
          <p className="max-w-[600px] text-zinc-400 text-lg md:text-xl font-light leading-relaxed">
            就寝前の雑音を外部へ。脳のメモリを解放し、<br className="hidden md:inline" />
            明日のあなたへ繋ぐ「第2の脳」。
          </p>
          
          <div className="pt-12">
            <button className="group relative px-8 py-4 bg-zinc-100 text-zinc-950 rounded-full font-medium overflow-hidden transition-all hover:pr-12 active:scale-95">
              <span className="relative z-10">思考をダンプする</span>
              <span className="absolute right-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-all">→</span>
            </button>
          </div>
        </div>
      </div>

      <div className="mb-32 grid text-center lg:mb-0 lg:w-full lg:max-w-5xl lg:grid-cols-3 lg:text-left">
        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-800 hover:bg-zinc-800/30">
          <h2 className="mb-3 text-2xl font-semibold">Voice Dump</h2>
          <p className="m-0 max-w-[30ch] text-sm text-zinc-400">
            声を出すだけで、AIがトピックを整理。
          </p>
        </div>
        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-800 hover:bg-zinc-800/30">
          <h2 className="mb-3 text-2xl font-semibold">Reflection</h2>
          <p className="m-0 max-w-[30ch] text-sm text-zinc-400">
            過去の自分に問いかけ、答えを得る。
          </p>
        </div>
        <div className="group rounded-lg border border-transparent px-5 py-4 transition-colors hover:border-gray-800 hover:bg-zinc-800/30">
          <h2 className="mb-3 text-2xl font-semibold">Low Stimulus</h2>
          <p className="m-0 max-w-[30ch] text-sm text-zinc-400">
            夜の使用に最適化したミニマルなUX。
          </p>
        </div>
      </div>
    </main>
  );
}
