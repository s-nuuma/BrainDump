"use client";

import { useState, useRef } from "react";
import { Mic, Square, Loader2 } from "lucide-react";

interface VoiceRecorderProps {
  onSuccess: (data: any) => void;
  onError: (error: string) => void;
}

export function VoiceRecorder({ onSuccess, onError }: VoiceRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        await sendAudioToBackend(audioBlob);
        // ストップ後にマイクの使用を終了させる
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Failed to start recording:", err);
      onError("マイクへのアクセスに失敗しました。");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudioToBackend = async (blob: Blob) => {
    setIsProcessing(true);
    try {
      const formData = new FormData();
      formData.append("file", blob, "recording.webm");
      formData.append("user_id", "test-user"); // TODO: 認証実装後に動的に取得

      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/api/transcribe`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Backend processing failed");
      }

      const data = await response.json();
      onSuccess(data);
    } catch (err) {
      console.error("Error sending audio:", err);
      onError("音声の処理中にエラーが発生しました。");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex flex-col items-center gap-6">
      <div className="relative">
        {/* 外側の波紋エフェクト（録音中のみ） */}
        {isRecording && (
          <div className="absolute inset-0 animate-ping rounded-full bg-red-500/20" />
        )}
        
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={isProcessing}
          className={`relative z-10 flex h-32 w-32 items-center justify-center rounded-full transition-all active:scale-95 ${
            isRecording
              ? "bg-red-500 text-white hover:bg-red-600"
              : "bg-zinc-100 text-zinc-900 hover:bg-zinc-200"
          } ${isProcessing ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          {isProcessing ? (
            <Loader2 className="h-12 w-12 animate-spin" />
          ) : isRecording ? (
            <Square className="h-12 w-12" />
          ) : (
            <Mic className="h-12 w-12" />
          )}
        </button>
      </div>

      <p className="text-sm font-medium tracking-wide text-zinc-400">
        {isProcessing
          ? "音声を文字起こし中..."
          : isRecording
          ? "思考をアウトプット中..."
          : "タップして録音を開始"}
      </p>
    </div>
  );
}
