export interface Comment { id: string; author: string; text: string; like_count: number }
export interface CommentResult {
  comment: Comment; sentiment: number; topic: string;
  is_question: number; is_spam: number; is_toxic: number;
}
export interface VideoMeta {
  video_id: string; title: string; channel: string; thumbnail: string | null;
  view_count: number | null; comment_count: number | null;
}
export interface Analysis {
  video: VideoMeta; summary: string | null; total_fetched: number; classified: number; unclassified: number;
  spam_count: number; spam_rate: number; toxic_rate: number; question_rate: number;
  sentiment: { mean: number; like_weighted_mean: number; positive: number; neutral: number; negative: number };
  topics: Record<string, number>;
  top_questions: CommentResult[]; most_positive: CommentResult[];
  most_negative: CommentResult[]; most_liked: CommentResult[];
}

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const YT = /^(https?:\/\/)?((www|m|music)\.)?(youtube\.com|youtu\.be)\//i;
export const looksLikeYouTube = (u: string) => YT.test(u.trim());

export async function analyze(url: string): Promise<Analysis> {
  let res: Response;
  try {
    res = await fetch(`${API}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
  } catch {
    throw new Error("Cannot reach the backend. Is it running?");
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${res.status})`);
  return body as Analysis;
}
