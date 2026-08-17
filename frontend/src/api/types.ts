export interface NodeScore {
  score: number;
  verdict: "green" | "amber" | "red";
  details: Record<string, unknown>;
}

export interface GraphNode {
  id: string;
  url: string;
  title: string | null;
  http_status: number | null;
  broken: boolean;
  error?: string | null;
  score: NodeScore | null;
  link_count?: number;
  children: GraphNode[];
  expanded?: boolean;
}

export interface CrawlJob {
  id: string;
  root_url: string;
  depth: number;
  status: "pending" | "running" | "done" | "failed";
  error: string | null;
  result: { tree: GraphNode; visited_count: number } | null;
  created_at: string;
}

export interface ImageMatch {
  id: string;
  engine: string;
  page_url: string;
  image_url: string | null;
  title: string | null;
  published_at: string | null;
  similarity: number;
}

export interface ExifData {
  camera: string | null;
  captured_at: string | null;
  gps: { lat: number; lon: number } | null;
  raw: Record<string, string>;
}

export interface ImageSearch {
  id: string;
  filename: string;
  phash: string;
  status: "pending" | "running" | "done" | "failed";
  error: string | null;
  exif: ExifData | null;
  created_at: string;
  matches: ImageMatch[];
}

export interface Quota {
  crawls_used: number;
  crawls_limit: number;
  image_searches_used: number;
  image_searches_limit: number;
}

export interface User {
  id: string;
  email: string;
  created_at: string;
}
