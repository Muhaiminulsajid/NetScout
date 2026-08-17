import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import type { UrlNodeData } from "../../lib/graph";

const badgeColors: Record<string, string> = {
  green: "bg-emerald-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
};

function UrlNode({ data }: NodeProps<UrlNodeData>) {
  const { node, dimmed, selected } = data;
  const verdict = node.score?.verdict ?? "green";
  let host = node.url;
  try { host = new URL(node.url).hostname; } catch { /* keep raw */ }

  return (
    <div
      className={`w-[220px] rounded-lg border bg-slate-900 px-3 py-2 shadow transition-opacity
        ${selected ? "border-sky-400 ring-2 ring-sky-400/40" : "border-slate-700"}
        ${node.broken ? "border-dashed !border-red-500" : ""}
        ${dimmed ? "opacity-20" : "opacity-100"}`}
    >
      <Handle type="target" position={Position.Left} className="!bg-slate-500" />
      <div className="flex items-center gap-2">
        <span
          title={`Spam score: ${node.score?.score ?? "?"} (${verdict})`}
          className={`h-3 w-3 shrink-0 rounded-full ${badgeColors[verdict]}`}
        />
        <span className="truncate text-xs font-semibold text-slate-100">{host}</span>
        {node.http_status != null && (
          <span className={`ml-auto text-[10px] ${node.broken ? "text-red-400" : "text-slate-500"}`}>
            {node.http_status}
          </span>
        )}
        {node.broken && node.http_status == null && (
          <span className="ml-auto text-[10px] text-red-400">ERR</span>
        )}
      </div>
      <p className="mt-1 truncate text-[10px] text-slate-400">{node.title ?? node.url}</p>
      <Handle type="source" position={Position.Right} className="!bg-slate-500" />
    </div>
  );
}

export default memo(UrlNode);
