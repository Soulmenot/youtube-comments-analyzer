"use client";
import { useState } from "react";
import AnalysisView from "@/components/AnalysisView";
import UrlForm from "@/components/UrlForm";
import { analyze, type Analysis } from "@/lib/api";

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState<Analysis | null>(null);

  async function run(url: string) {
    setLoading(true);
    setError("");
    setData(null);
    try {
      setData(await analyze(url));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl space-y-6 px-4 py-10">
      <header>
        <h1 className="text-3xl font-bold">YouTube Comments Analyzer</h1>
        <p className="text-slate-600">Analyzes up to 1,000 comments with Jev and Groq.</p>
      </header>
      <UrlForm loading={loading} onSubmit={run} />
      {loading && <p className="text-slate-600">Fetching and classifying comments. This can take a minute…</p>}
      {error && <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-red-700">{error}</div>}
      {data && <AnalysisView data={data} />}
    </main>
  );
}
