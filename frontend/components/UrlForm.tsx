"use client";
import { useState } from "react";
import { looksLikeYouTube } from "@/lib/api";

export default function UrlForm({ loading, onSubmit }: { loading: boolean; onSubmit: (url: string) => void }) {
  const [url, setUrl] = useState("");
  const [err, setErr] = useState("");

  return (
    <form
      className="flex flex-col gap-2 sm:flex-row"
      onSubmit={(e) => {
        e.preventDefault();
        if (!looksLikeYouTube(url)) return setErr("Enter a valid YouTube video URL.");
        setErr("");
        onSubmit(url.trim());
      }}
    >
      <div className="flex-1">
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.youtube.com/watch?v=..."
          className="w-full rounded-lg border border-slate-300 bg-white px-4 py-3 outline-none focus:border-red-500"
        />
        {err && <p className="mt-1 text-sm text-red-600">{err}</p>}
      </div>
      <button
        disabled={loading}
        className="rounded-lg bg-red-600 px-6 py-3 font-medium text-white hover:bg-red-700 disabled:opacity-50"
      >
        {loading ? "Analyzing…" : "Analyze"}
      </button>
    </form>
  );
}
