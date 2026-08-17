import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { CrawlJob, ImageSearch, Quota } from "../api/types";

function QuotaBar({ label, used, limit }: { label: string; used: number; limit: number }) {
  const pct = Math.min((used / limit) * 100, 100);
  return (
    <div>
      <div className="mb-1 flex justify-between text-sm text-slate-400">
        <span>{label}</span><span>{used} / {limit}</span>
      </div>
      <div className="h-2 rounded-full bg-slate-800">
        <div
          className={`h-2 rounded-full ${pct > 85 ? "bg-red-500" : pct > 60 ? "bg-amber-500" : "bg-sky-500"}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [quota, setQuota] = useState<Quota | null>(null);
  const [crawls, setCrawls] = useState<CrawlJob[]>([]);
  const [searches, setSearches] = useState<ImageSearch[]>([]);

  useEffect(() => {
    api.get<Quota>("/history/quota").then((r) => setQuota(r.data)).catch(() => {});
    api.get<CrawlJob[]>("/history/crawls").then((r) => setCrawls(r.data)).catch(() => {});
    api.get<ImageSearch[]>("/history/image-searches").then((r) => setSearches(r.data)).catch(() => {});
  }, []);

  const statusColor = (s: string) =>
    s === "done" ? "text-emerald-400" : s === "failed" ? "text-red-400" : "text-amber-400";

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Your dashboard</h1>

      {quota && (
        <div className="grid gap-4 rounded-xl border border-slate-800 bg-slate-900 p-5 sm:grid-cols-2">
          <QuotaBar label="Daily crawls" used={quota.crawls_used} limit={quota.crawls_limit} />
          <QuotaBar label="Daily image searches" used={quota.image_searches_used} limit={quota.image_searches_limit} />
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Recent crawls</h2>
            <Link to="/webgraph" className="text-sm text-sky-400 hover:underline">New crawl →</Link>
          </div>
          <ul className="divide-y divide-slate-800 text-sm">
            {crawls.length === 0 && <li className="py-3 text-slate-500">No crawls yet.</li>}
            {crawls.map((c) => (
              <li key={c.id} className="flex items-center gap-3 py-2.5">
                <span className={statusColor(c.status)}>●</span>
                <span className="flex-1 truncate text-slate-300">{c.root_url}</span>
                <span className="text-slate-500">depth {c.depth}</span>
                <span className="text-slate-500">{new Date(c.created_at).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="rounded-xl border border-slate-800 bg-slate-900 p-5">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-semibold">Recent image searches</h2>
            <Link to="/imagetrace" className="text-sm text-sky-400 hover:underline">New search →</Link>
          </div>
          <ul className="divide-y divide-slate-800 text-sm">
            {searches.length === 0 && <li className="py-3 text-slate-500">No image searches yet.</li>}
            {searches.map((s) => (
              <li key={s.id} className="flex items-center gap-3 py-2.5">
                <span className={statusColor(s.status)}>●</span>
                <span className="flex-1 truncate text-slate-300">{s.filename}</span>
                <span className="text-slate-500">{s.matches.length} matches</span>
                <span className="text-slate-500">{new Date(s.created_at).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </div>
  );
}
