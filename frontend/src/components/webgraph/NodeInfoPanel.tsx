import type { GraphNode } from "../../api/types";

interface Props {
  node: GraphNode;
  expanding: boolean;
  onExpand: (node: GraphNode) => void;
  onClose: () => void;
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-3 border-b border-slate-800 py-1.5 text-sm">
      <span className="shrink-0 text-slate-500">{label}</span>
      <span className="truncate text-right text-slate-200">{value}</span>
    </div>
  );
}

export default function NodeInfoPanel({ node, expanding, onExpand, onClose }: Props) {
  const score = node.score;
  const details = (score?.details ?? {}) as any;
  const ssl = details.ssl as { valid: boolean | null; issuer: string | null } | undefined;
  const age = details.domain_age_days as number | null | undefined;
  const heuristics = details.heuristics as { flags: string[] } | undefined;

  const verdictCls =
    score?.verdict === "red" ? "bg-red-500/15 text-red-400"
    : score?.verdict === "amber" ? "bg-amber-500/15 text-amber-400"
    : "bg-emerald-500/15 text-emerald-400";

  return (
    <aside className="absolute right-3 top-3 z-10 w-80 rounded-xl border border-slate-700 bg-slate-900/95 p-4 shadow-xl backdrop-blur">
      <div className="mb-2 flex items-start justify-between gap-2">
        <h3 className="break-all text-sm font-semibold text-slate-100">
          {node.title ?? node.url}
        </h3>
        <button onClick={onClose} className="text-slate-500 hover:text-slate-300">✕</button>
      </div>
      <a
        href={node.url} target="_blank" rel="noreferrer"
        className="mb-3 block break-all text-xs text-sky-400 hover:underline"
      >
        {node.url}
      </a>

      {score && (
        <div className={`mb-3 flex items-center justify-between rounded-lg px-3 py-2 ${verdictCls}`}>
          <span className="text-sm font-medium capitalize">{score.verdict}</span>
          <span className="text-sm font-bold">{score.score} / 100</span>
        </div>
      )}

      <Row label="HTTP status" value={node.http_status ?? (node.broken ? "unreachable" : "—")} />
      <Row label="SSL" value={ssl ? (ssl.valid === true ? "valid" : ssl.valid === false ? "invalid" : "n/a") : "—"} />
      {ssl?.issuer && <Row label="Issuer" value={ssl.issuer.split(",").pop()} />}
      <Row label="Domain age" value={age != null ? `${age} days` : "unknown"} />
      <Row label="Links found" value={node.link_count ?? node.children.length} />

      {heuristics && heuristics.flags.length > 0 && (
        <div className="mt-2">
          <p className="mb-1 text-xs text-slate-500">Heuristic flags</p>
          <div className="flex flex-wrap gap-1">
            {heuristics.flags.map((f) => (
              <span key={f} className="rounded bg-slate-800 px-1.5 py-0.5 text-[10px] text-amber-300">
                {f}
              </span>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={() => onExpand(node)}
        disabled={expanding}
        className="mt-4 w-full rounded-md bg-sky-600 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
      >
        {expanding ? "Expanding…" : node.children.length > 0 ? "Re-expand node" : "Expand links"}
      </button>
    </aside>
  );
}
