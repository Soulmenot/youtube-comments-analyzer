import type { Analysis, CommentResult } from "@/lib/api";

const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold">{value}</div>
    </div>
  );
}

function Bar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const w = total ? (value / total) * 100 : 0;
  return (
    <div className="mb-2">
      <div className="mb-1 flex justify-between text-sm">
        <span className="capitalize">{label}</span>
        <span className="text-slate-500">{value} ({w.toFixed(0)}%)</span>
      </div>
      <div className="h-2 rounded bg-slate-200">
        <div className={`h-2 rounded ${color}`} style={{ width: `${w}%` }} />
      </div>
    </div>
  );
}

function CommentList({ title, items }: { title: string; items: CommentResult[] }) {
  if (!items.length) return null;
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="mb-3 font-semibold">{title}</h3>
      <ul className="space-y-3">
        {items.map((r) => (
          <li key={r.comment.id} className="text-sm">
            <p className="whitespace-pre-line">{r.comment.text}</p>
            <p className="mt-1 text-xs text-slate-500">
              {r.comment.author} · {r.comment.like_count} likes · sentiment {r.sentiment.toFixed(2)}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function AnalysisView({ data }: { data: Analysis }) {
  const s = data.sentiment;
  const sTotal = s.positive + s.neutral + s.negative;
  const topics = Object.entries(data.topics);
  const tTotal = topics.reduce((a, [, n]) => a + n, 0);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4 rounded-lg border border-slate-200 bg-white p-4">
        {data.video.thumbnail && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={data.video.thumbnail} alt="" className="h-20 rounded" />
        )}
        <div>
          <h2 className="font-semibold">{data.video.title}</h2>
          <p className="text-sm text-slate-500">{data.video.channel}</p>
        </div>
      </div>

      {data.summary && (
        <section className="rounded-lg border border-slate-200 bg-white p-4">
          <h3 className="mb-2 font-semibold">AI summary</h3>
          <p className="whitespace-pre-line text-sm leading-relaxed text-slate-700">{data.summary}</p>
        </section>
      )}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Stat label="Comments analyzed" value={String(data.classified)} />
        <Stat label="Avg sentiment" value={s.mean.toFixed(2)} />
        <Stat label="Like-weighted sentiment" value={s.like_weighted_mean.toFixed(2)} />
        <Stat label="Spam rate" value={pct(data.spam_rate)} />
        <Stat label="Question rate" value={pct(data.question_rate)} />
        <Stat label="Toxic rate" value={pct(data.toxic_rate)} />
        <Stat label="Unclassified" value={String(data.unclassified)} />
        <Stat label="Fetched" value={String(data.total_fetched)} />
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-lg border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold">Sentiment</h3>
          <Bar label="positive" value={s.positive} total={sTotal} color="bg-green-500" />
          <Bar label="neutral" value={s.neutral} total={sTotal} color="bg-slate-400" />
          <Bar label="negative" value={s.negative} total={sTotal} color="bg-red-500" />
        </section>
        <section className="rounded-lg border border-slate-200 bg-white p-4">
          <h3 className="mb-3 font-semibold">Topics</h3>
          {topics.map(([t, n]) => (
            <Bar key={t} label={t} value={n} total={tTotal} color="bg-indigo-500" />
          ))}
        </section>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <CommentList title="Most positive" items={data.most_positive} />
        <CommentList title="Most negative" items={data.most_negative} />
        <CommentList title="Top viewer questions" items={data.top_questions} />
        <CommentList title="Most liked" items={data.most_liked} />
      </div>
    </div>
  );
}
