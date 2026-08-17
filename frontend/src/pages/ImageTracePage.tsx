import { useCallback, useEffect, useRef, useState } from "react";
import { api, downloadFile } from "../api/client";
import type { ImageSearch } from "../api/types";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

function EngineBadge({ engine }: { engine: string }) {
  const styles: Record<string, string> = {
    bing: "bg-teal-500/15 text-teal-300",
    google_vision: "bg-indigo-500/15 text-indigo-300",
    local_cache: "bg-slate-500/15 text-slate-300",
  };
  const labels: Record<string, string> = {
    bing: "Bing Visual", google_vision: "Google Vision", local_cache: "Cache",
  };
  return (
    <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${styles[engine] ?? styles.local_cache}`}>
      {labels[engine] ?? engine}
    </span>
  );
}

export default function ImageTracePage() {
  const [search, setSearch] = useState<ImageSearch | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef(0);

  useEffect(() => () => { pollRef.current += 1; }, []); // cancel polls on unmount

  const upload = useCallback(async (file: File) => {
    setError("");
    setBusy(true);
    setSearch(null);
    setPreview(URL.createObjectURL(file));
    const myPoll = ++pollRef.current;
    try {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<ImageSearch>("/imagetrace/search", form);
      let current = data;
      while ((current.status === "pending" || current.status === "running") && pollRef.current === myPoll) {
        await sleep(2000);
        current = (await api.get<ImageSearch>(`/imagetrace/search/${data.id}`)).data;
      }
      setSearch(current);
    } catch (err: any) {
      setError(err.response?.data?.detail ?? "Upload failed");
    } finally {
      setBusy(false);
    }
  }, []);

  const dated = search?.matches.filter((m) => m.published_at) ?? [];
  const undated = search?.matches.filter((m) => !m.published_at) ?? [];
  const earliest = dated[0];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">ImageTrace — reverse image search</h1>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          const file = e.dataTransfer.files[0];
          if (file) upload(file);
        }}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-10 transition-colors
          ${dragOver ? "border-sky-400 bg-sky-500/5" : "border-slate-700 bg-slate-900 hover:border-slate-500"}`}
      >
        <input
          ref={inputRef} type="file" accept="image/*" hidden
          onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
        />
        <p className="text-slate-300">Drop an image here or click to browse</p>
        <p className="mt-1 text-xs text-slate-500">JPEG, PNG, WebP, GIF, BMP — up to 10 MB</p>
      </div>

      {error && <p className="rounded-lg bg-red-500/10 px-4 py-2 text-sm text-red-400">{error}</p>}
      {busy && <p className="text-sm text-slate-400">Fingerprinting locally, then querying Bing Visual Search + Google Vision…</p>}

      {(preview || search) && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-4">
            {preview && (
              <img src={preview} alt="query" className="w-full rounded-xl border border-slate-800 object-contain" />
            )}
            {search && (
              <div className="rounded-xl border border-slate-800 bg-slate-900 p-4 text-sm">
                <h3 className="mb-2 font-semibold">EXIF metadata</h3>
                <dl className="space-y-1 text-slate-300">
                  <div className="flex justify-between"><dt className="text-slate-500">Camera</dt><dd>{search.exif?.camera ?? "—"}</dd></div>
                  <div className="flex justify-between"><dt className="text-slate-500">Captured</dt><dd>{search.exif?.captured_at ?? "—"}</dd></div>
                  <div className="flex justify-between">
                    <dt className="text-slate-500">GPS</dt>
                    <dd>
                      {search.exif?.gps ? (
                        <a
                          className="text-sky-400 hover:underline"
                          target="_blank" rel="noreferrer"
                          href={`https://www.openstreetmap.org/?mlat=${search.exif.gps.lat}&mlon=${search.exif.gps.lon}`}
                        >
                          {search.exif.gps.lat}, {search.exif.gps.lon}
                        </a>
                      ) : "—"}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt className="text-slate-500">pHash</dt>
                    <dd className="truncate font-mono text-xs">{search.phash}</dd>
                  </div>
                </dl>
                {search.status === "done" && (
                  <div className="mt-4 flex gap-2">
                    <button
                      onClick={() => downloadFile(`/imagetrace/search/${search.id}/export.pdf`, "netscout-report.pdf")}
                      className="flex-1 rounded-md bg-sky-600 py-2 text-xs font-medium text-white hover:bg-sky-500"
                    >
                      Export PDF
                    </button>
                    <button
                      onClick={() => downloadFile(`/imagetrace/search/${search.id}/export.csv`, "netscout-report.csv")}
                      className="flex-1 rounded-md border border-slate-700 py-2 text-xs text-slate-300 hover:bg-slate-800"
                    >
                      Export CSV
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="lg:col-span-2">
            {search?.error && (
              <p className="mb-3 rounded-lg bg-amber-500/10 px-4 py-2 text-sm text-amber-400">{search.error}</p>
            )}
            {search && search.status === "done" && (
              <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
                <h3 className="mb-3 font-semibold">
                  Source timeline
                  <span className="ml-2 text-sm font-normal text-slate-500">
                    {search.matches.length} matches, earliest first
                  </span>
                </h3>
                {search.matches.length === 0 && (
                  <p className="text-sm text-slate-500">No matches found.</p>
                )}
                <ol className="relative space-y-3 border-l border-slate-700 pl-5">
                  {[...dated, ...undated].map((m) => (
                    <li key={m.id} className="relative">
                      <span className={`absolute -left-[26px] top-1.5 h-3 w-3 rounded-full border-2 border-slate-900
                        ${m.id === earliest?.id ? "bg-emerald-400" : "bg-slate-500"}`} />
                      <div className="rounded-lg border border-slate-800 bg-slate-950 p-3">
                        <div className="flex flex-wrap items-center gap-2">
                          {m.id === earliest?.id && (
                            <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-300">
                              EARLIEST KNOWN
                            </span>
                          )}
                          <EngineBadge engine={m.engine} />
                          <span className="text-xs text-slate-500">
                            {m.published_at ? new Date(m.published_at).toLocaleDateString() : "date unknown"}
                          </span>
                          <span className="ml-auto text-xs font-semibold text-sky-300">
                            {m.similarity.toFixed(0)}% similar
                          </span>
                        </div>
                        <a
                          href={m.page_url} target="_blank" rel="noreferrer"
                          className="mt-1 block truncate text-sm text-slate-200 hover:text-sky-400"
                        >
                          {m.title ?? m.page_url}
                        </a>
                        <div className="mt-1 h-1.5 rounded-full bg-slate-800">
                          <div className="h-1.5 rounded-full bg-sky-500" style={{ width: `${m.similarity}%` }} />
                        </div>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
