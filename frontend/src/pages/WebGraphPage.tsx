import { toPng, toSvg } from "html-to-image";
import { useCallback, useMemo, useRef, useState, type FormEvent } from "react";
import ReactFlow, { Background, Controls, MiniMap } from "reactflow";
import { api } from "../api/client";
import type { CrawlJob, GraphNode } from "../api/types";
import NodeInfoPanel from "../components/webgraph/NodeInfoPanel";
import UrlNode from "../components/webgraph/UrlNode";
import { attachChildren, layoutTree } from "../lib/graph";

const nodeTypes = { urlNode: UrlNode };
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export default function WebGraphPage() {
  const [url, setUrl] = useState("");
  const [depth, setDepth] = useState(1);
  const [tree, setTree] = useState<GraphNode | null>(null);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [expanding, setExpanding] = useState(false);
  const flowRef = useRef<HTMLDivElement>(null);

  const { nodes, edges } = useMemo(
    () => (tree ? layoutTree(tree, filter, selectedId) : { nodes: [], edges: [] }),
    [tree, filter, selectedId]
  );

  const selectedNode = useMemo(() => {
    if (!tree || !selectedId) return null;
    const find = (n: GraphNode): GraphNode | null =>
      n.id === selectedId ? n : n.children.map(find).find(Boolean) ?? null;
    return find(tree);
  }, [tree, selectedId]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setTree(null);
    setSelectedId(null);
    setStatus("Queued…");
    try {
      const target = /^https?:\/\//i.test(url) ? url : `https://${url}`;
      const { data: job } = await api.post<CrawlJob>("/webgraph/crawl", {
        url: target, depth,
      });
      let current = job;
      while (current.status === "pending" || current.status === "running") {
        setStatus(current.status === "pending" ? "Queued…" : "Crawling & scoring…");
        await sleep(2000);
        current = (await api.get<CrawlJob>(`/webgraph/crawl/${job.id}`)).data;
      }
      if (current.status === "failed") {
        setError(current.error ?? "Crawl failed");
      } else if (current.result) {
        setTree(current.result.tree);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Request failed");
    } finally {
      setStatus("");
    }
  }

  const expandNode = useCallback(async (node: GraphNode) => {
    setExpanding(true);
    setError("");
    try {
      const { data } = await api.post<{ task_id: string }>("/webgraph/expand", { url: node.url });
      let result: any = null;
      for (let i = 0; i < 60; i++) {
        await sleep(2000);
        const poll = (await api.get(`/webgraph/expand/${data.task_id}`)).data;
        if (poll.status === "done") { result = poll.node; break; }
        if (poll.status === "failed") throw new Error(poll.error ?? "Expand failed");
      }
      if (!result) throw new Error("Expand timed out");
      setTree((t) => (t ? attachChildren(t, node.id, result) : t));
    } catch (err: any) {
      setError(err.response?.data?.detail ?? err.message ?? "Expand failed");
    } finally {
      setExpanding(false);
    }
  }, []);

  async function exportImage(kind: "png" | "svg") {
    const el = flowRef.current?.querySelector(".react-flow__viewport") as HTMLElement | null;
    if (!el) return;
    const fn = kind === "png" ? toPng : toSvg;
    const dataUrl = await fn(el, { backgroundColor: "#020617" });
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = `netscout-graph.${kind}`;
    a.click();
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">WebGraph — link topology visualizer</h1>

      <form onSubmit={onSubmit} className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-800 bg-slate-900 p-4">
        <input
          value={url} onChange={(e) => setUrl(e.target.value)} required
          placeholder="https://example.com"
          className="min-w-64 flex-1 rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
        />
        <label className="flex items-center gap-2 text-sm text-slate-400">
          Depth
          <select
            value={depth} onChange={(e) => setDepth(Number(e.target.value))}
            className="rounded-md border border-slate-700 bg-slate-800 px-2 py-2 text-slate-100"
          >
            {[1, 2, 3, 4, 5].map((d) => <option key={d} value={d}>{d}</option>)}
          </select>
        </label>
        <button
          disabled={!!status}
          className="rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-500 disabled:opacity-50"
        >
          {status || "Map it"}
        </button>
        {tree && (
          <>
            <input
              value={filter} onChange={(e) => setFilter(e.target.value)}
              placeholder="Filter nodes…"
              className="w-48 rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
            />
            <button type="button" onClick={() => exportImage("png")}
              className="rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800">
              Export PNG
            </button>
            <button type="button" onClick={() => exportImage("svg")}
              className="rounded-md border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:bg-slate-800">
              Export SVG
            </button>
          </>
        )}
      </form>

      {error && <p className="rounded-lg bg-red-500/10 px-4 py-2 text-sm text-red-400">{error}</p>}

      <div ref={flowRef} className="relative h-[70vh] rounded-xl border border-slate-800 bg-slate-950">
        {tree ? (
          <>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              fitView
              minZoom={0.05}
              onNodeClick={(_, n) => setSelectedId(n.id)}
              onPaneClick={() => setSelectedId(null)}
              proOptions={{ hideAttribution: true }}
            >
              <Background color="#1e293b" />
              <Controls />
              <MiniMap pannable zoomable className="!bg-slate-900" />
            </ReactFlow>
            {selectedNode && (
              <NodeInfoPanel
                node={selectedNode}
                expanding={expanding}
                onExpand={expandNode}
                onClose={() => setSelectedId(null)}
              />
            )}
            <div className="absolute bottom-3 left-12 flex gap-4 rounded-lg bg-slate-900/90 px-3 py-1.5 text-xs text-slate-400">
              <span><span className="text-emerald-400">●</span> safe</span>
              <span><span className="text-amber-400">●</span> suspicious</span>
              <span><span className="text-red-400">●</span> dangerous</span>
              <span className="border-l border-slate-700 pl-3">dashed = broken link</span>
            </div>
          </>
        ) : (
          <div className="flex h-full items-center justify-center text-slate-600">
            {status || "Paste a URL above to map its hyperlink structure. Click any node to inspect and expand it."}
          </div>
        )}
      </div>
    </div>
  );
}
