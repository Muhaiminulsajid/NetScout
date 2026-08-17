import { hierarchy, tree } from "d3-hierarchy";
import type { Edge, Node } from "reactflow";
import type { GraphNode } from "../api/types";

export interface UrlNodeData {
  node: GraphNode;
  dimmed: boolean;
  selected: boolean;
}

const NODE_W = 220;
const NODE_H = 64;

/** Convert the crawl tree into positioned React Flow nodes + edges via d3 tree layout. */
export function layoutTree(
  root: GraphNode,
  filter: string,
  selectedId: string | null
): { nodes: Node<UrlNodeData>[]; edges: Edge[] } {
  const h = hierarchy<GraphNode>(root, (d) => d.children);
  const layout = tree<GraphNode>().nodeSize([NODE_H + 28, NODE_W + 120]);
  const positioned = layout(h);

  const q = filter.trim().toLowerCase();
  const nodes: Node<UrlNodeData>[] = [];
  const edges: Edge[] = [];

  positioned.each((p) => {
    const d = p.data;
    const dimmed =
      q.length > 0 &&
      !d.url.toLowerCase().includes(q) &&
      !(d.title ?? "").toLowerCase().includes(q);
    nodes.push({
      id: d.id,
      type: "urlNode",
      position: { x: p.y, y: p.x }, // horizontal layout
      data: { node: d, dimmed, selected: d.id === selectedId },
    });
    if (p.parent) {
      edges.push({
        id: `${p.parent.data.id}-${d.id}`,
        source: p.parent.data.id,
        target: d.id,
        style: { stroke: d.broken ? "#ef4444" : "#475569" },
        animated: false,
      });
    }
  });
  return { nodes, edges };
}

/** Immutably insert freshly-expanded children under the node with `id`. */
export function attachChildren(root: GraphNode, id: string, expanded: GraphNode): GraphNode {
  if (root.id === id) {
    return {
      ...root,
      title: root.title ?? expanded.title,
      http_status: root.http_status ?? expanded.http_status,
      broken: root.broken || expanded.broken,
      score: root.score ?? expanded.score,
      children: expanded.children,
      expanded: true,
    };
  }
  return { ...root, children: root.children.map((c) => attachChildren(c, id, expanded)) };
}
