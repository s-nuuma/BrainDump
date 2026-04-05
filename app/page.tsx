"use client";

import { useEffect, useState } from "react";
import { VoiceRecorder } from "@/components/voice-recorder";
import { ChatInterface } from "@/components/chat-interface";
import { HistoryView } from "@/components/history-view";
import { InsightsView } from "@/components/insights-view";
import { auth, googleProvider } from "@/lib/firebase";
import { signInWithPopup, onAuthStateChanged, signOut, User } from "firebase/auth";
import { Eye, EyeOff, LogOut } from "lucide-react";

export default function Home() {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"dump" | "archive" | "insights">("dump");
  const [status, setStatus] = useState<string>("Checking...");
  const [lastResult, setLastResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  // 新機能: ハイブリッドエディタとバッファ管理
  const [draftText, setDraftText] = useState<string>("");
  const [isDumping, setIsDumping] = useState<boolean>(false);

  // フォーカスモード
  const [isFocusMode, setIsFocusMode] = useState(false);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setIsAuthLoading(false);
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (draftText.trim().length > 0) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [draftText]);

  useEffect(() => {
    // Backend (FastAPI) のヘルスチェック
    const checkBackend = async () => {
      try {
        // Vercel統合環境では、フロントエンドから見てバックエンドは常に /api/xxxx
        // 常に絶対URLで構築することで曖昧さを排除
        const origin = window.location.origin;
        const targetUrl = `${origin}/api/health`;
        
        console.log("Checking health at:", targetUrl);
        const res = await fetch(targetUrl);
        if (!res.ok) {
          setStatus(`Offline (${res.status})`);
          console.error("Health check failed with status:", res.status);
          return;
        }
        const data = await res.json();
        setStatus(data.status === "ok" ? "Connected" : "Error");
      } catch (e: any) {
        console.error("Health check exception:", e);
        setStatus(`Offline (Connect Error)`);
      }
    };
    checkBackend();
  }, []);

  const handleLogin = async () => {
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (e: any) {
      console.error("Login failed:", e);
      alert("ログインに失敗しました。\n理由: " + (e.code || e.message));
    }
  };

  const handleLogout = async () => {
    try {
      await signOut(auth);
    } catch (e) {
      console.error("Logout failed", e);
    }
  };

  const handleSuccess = (data: any) => {
    // 文字起こし結果をエディタに追記する
    if (data.data?.content) {
      setDraftText((prev: string) => prev ? prev + "\n" + data.data.content : data.data.content);
    }
    setErrorMsg(null);
  };

  const handleDump = async () => {
    if (!draftText.trim() || !user) return;
    setIsDumping(true);
    setErrorMsg(null);
    try {
      const targetUrl = `${window.location.origin}/api/dump`;
      
      const res = await fetch(targetUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: draftText,
          user_id: user.uid,
        }),
      });

      if (!res.ok) {
        throw new Error(`Failed to dump data (${res.status})`);
      }

      const result = await res.json();
      setLastResult(result.data);
      // 送信完了時にバッファをクリア
      setDraftText("");
    } catch (e: any) {
      setErrorMsg(e.message || "思考の保存中にエラーが発生しました。");
    } finally {
      setIsDumping(false);
    }
  };

  const handleError = (error: string) => {
    setErrorMsg(error);
  };

  if (isAuthLoading) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center bg-[#0a0a0a] text-[#ededed]">
        <div className="animate-pulse text-zinc-500">Loading...</div>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-[#0a0a0a] text-[#ededed]">
        <div className="text-center space-y-8">
          <h1 className="text-5xl md:text-7xl font-light tracking-tighter text-zinc-100 italic">
            BrainDump
          </h1>
          <p className="text-zinc-400 text-lg">外部メモリへアクセスするにはログインしてください</p>
          <button 
            onClick={handleLogin} 
            className="px-8 py-3 bg-white text-black rounded-full font-medium hover:bg-zinc-200 transition-colors"
          >
            Sign in with Google
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-start p-4 md:p-24 bg-[#0a0a0a] text-[#ededed]">
      {/* Header - Hidden in Focus Mode */}
      {!isFocusMode && (
        <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex mb-12">
          <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-800 bg-zinc-900/30 pb-6 pt-8 backdrop-blur-2xl lg:static lg:w-auto lg:rounded-xl lg:border lg:bg-zinc-800/30 lg:p-4">
            BrainDump
          </p>
          <div className="fixed bottom-0 left-0 flex h-48 w-full items-end justify-center bg-gradient-to-t from-black via-black lg:static lg:h-auto lg:w-auto lg:bg-none">
            <div className="flex items-center gap-4 p-8 lg:p-0">
              <div className="flex items-center gap-2">
                <span className={`h-2 w-2 rounded-full ${status === "Connected" ? "bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]" : "bg-red-500"}`}></span>
                <span className="text-xs text-zinc-400 uppercase tracking-widest">{status}</span>
              </div>
              <button onClick={handleLogout} className="text-zinc-500 hover:text-zinc-300" title="Logout">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tabs & Focus Toggle - Hidden in Focus Mode */}
      {!isFocusMode && (
        <div className="flex flex-wrap justify-center items-center gap-4 mb-12 w-full max-w-5xl">
          <div className="flex gap-2">
            {["input", "history", "insights"].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={`px-6 py-2 rounded-full text-sm font-medium transition-colors ${
                  activeTab === tab 
                    ? "bg-zinc-100 text-black" 
                    : "bg-zinc-900 text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
          
          <div className="flex-1"></div>
          
          <button
            onClick={() => setIsFocusMode(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 rounded-full text-sm font-medium transition-colors"
          >
            <EyeOff className="w-4 h-4" />
            Focus
          </button>
        </div>
      )}

      {/* Focus Mode Exit Button - Only visible in Focus Mode */}
      {isFocusMode && (
        <div className="fixed top-8 right-8 z-50">
          <button
            onClick={() => setIsFocusMode(false)}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800 text-zinc-300 hover:bg-zinc-700 rounded-full text-sm transition-colors shadow-lg"
          >
            <Eye className="w-4 h-4" />
            Exit
          </button>
        </div>
      )}

      {/* Main Content Area */}
      {activeTab === "dump" ? (
        <>
          <div className={`relative flex place-items-center w-full justify-center ${isFocusMode ? 'mt-24' : ''}`}>
            <div className="flex flex-col items-center text-center space-y-8 w-full">
              {!isFocusMode && (
                <h1 className="text-5xl md:text-7xl font-light tracking-tighter text-zinc-100">
                  Dump your <span className="text-zinc-500 italic">chaos</span>.
                </h1>
              )}
              
              <div className={`w-full max-w-[600px] ${!isFocusMode ? 'pt-12' : ''}`}>
                <VoiceRecorder onSuccess={handleSuccess} onError={handleError} />
                
                <div className="mt-8 relative w-full">
                  <textarea
                    value={draftText}
                    onChange={(e) => setDraftText(e.target.value)}
                    placeholder="思考をテキストで入力、またはマイクで録音..."
                    className="w-full h-48 p-5 bg-zinc-900/80 border border-zinc-800 rounded-2xl text-zinc-200 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-zinc-700 resize-none leading-relaxed shadow-2xl"
                    disabled={isDumping}
                  />
                  <div className="absolute bottom-4 right-4">
                    <button
                      onClick={handleDump}
                      disabled={!draftText.trim() || isDumping}
                      className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                        !draftText.trim() || isDumping
                          ? "bg-zinc-800 text-zinc-500 cursor-not-allowed"
                          : "bg-white text-black hover:bg-zinc-200 shadow-md"
                      }`}
                    >
                      {isDumping ? "Dumping..." : "Dump"}
                    </button>
                  </div>
                </div>
              </div>

              {!isFocusMode && errorMsg && (
                <div className="mt-4 text-red-500 text-sm bg-red-500/10 px-4 py-2 rounded-lg border border-red-500/20 animate-pulse">
                  {errorMsg}
                </div>
              )}

              {!isFocusMode && lastResult && (
                <div className="mt-8 p-6 bg-zinc-900/50 rounded-xl border border-zinc-800 text-left max-w-[600px] w-full backdrop-blur-sm shadow-xl">
                  <h3 className="text-xl font-semibold mb-4 text-zinc-200">Result</h3>
                  <div className="space-y-2 text-sm text-zinc-400">
                    <p><strong className="text-zinc-300">Topic:</strong> {lastResult.topic?.join(", ")}</p>
                    <p><strong className="text-zinc-300">Sentiment:</strong> {lastResult.sentiment?.label} ({lastResult.sentiment?.score})</p>
                    <p><strong className="text-zinc-300">Summary:</strong> {lastResult.summary}</p>
                  </div>
                  <p className="text-sm text-zinc-500 italic border-t border-zinc-800 mt-4 pt-4 leading-relaxed">
                    "{lastResult.content}"
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Chat Interface Section - Hidden in Focus Mode */}
          {!isFocusMode && (
            <div className="w-full max-w-5xl mt-24 flex justify-center">
              <ChatInterface userId={user.uid} />
            </div>
          )}
        </>
      ) : activeTab === "archive" ? (
        <HistoryView userId={user.uid} />
      ) : (
        <InsightsView userId={user.uid} />
      )}

      {/* Spacing for mobile fixed bottom navbar if any */}
      <div className="h-32" />
    </main>
  );
}
