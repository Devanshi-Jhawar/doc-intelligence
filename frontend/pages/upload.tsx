import { useState, useRef, useEffect, useCallback } from "react";
import { Upload, FileText, Trash2, CheckCircle, AlertCircle, Clock, Loader2, X, ChevronDown, ChevronUp } from "lucide-react";
import clsx from "clsx";
import Layout from "../components/Layout";
import { uploadDocument, getDocument, deleteDocument, getDocuments, Document } from "../components/api";

const STATUS_LABELS: Record<string, string> = {
  queued: "Queued",
  parsing: "Parsing",
  classifying: "Classifying",
  indexing: "Indexing",
  ready: "Ready",
  error: "Error",
};

const STATUS_ICON = {
  queued: <Clock size={13} />,
  parsing: <Loader2 size={13} className="animate-spin" />,
  classifying: <Loader2 size={13} className="animate-spin" />,
  indexing: <Loader2 size={13} className="animate-spin" />,
  ready: <CheckCircle size={13} />,
  error: <AlertCircle size={13} />,
};

function DocRow({ doc, onDelete }: { doc: Document; onDelete: (id: string) => void }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl overflow-hidden" style={{ background: "#181c27", border: "1px solid #252a38" }}>
      <div className="flex items-center gap-3 px-4 py-3">
        <FileText size={16} style={{ color: "#6c63ff", flexShrink: 0 }} />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-white truncate">{doc.filename}</p>
          <p className="text-xs mt-0.5" style={{ color: "#8b92a5" }}>
            {doc.num_pages ? `${doc.num_pages} pages · ` : ""}
            {new Date(doc.uploaded_at).toLocaleString()}
          </p>
        </div>

        <div className={clsx("flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 rounded-full", `status-${doc.status}`)}
          style={{ background: "rgba(255,255,255,0.05)" }}>
          {STATUS_ICON[doc.status]}
          {STATUS_LABELS[doc.status]}
        </div>

        {doc.classification && (
          <button onClick={() => setExpanded((e) => !e)} className="text-xs px-2 py-1 rounded-lg transition-colors" style={{ color: "#8b92a5" }}>
            {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        )}

        <button onClick={() => onDelete(doc.doc_id)} className="p-1.5 rounded-lg transition-colors hover:bg-red-500/10" style={{ color: "#8b92a5" }}>
          <Trash2 size={13} />
        </button>
      </div>

      {/* classification details panel */}
      {expanded && doc.classification && (
        <div className="px-4 pb-4" style={{ borderTop: "1px solid #252a38" }}>
          <div className="pt-3 grid grid-cols-2 gap-3">
            {[
              ["Type", String(doc.classification.type || "—")],
              ["Topic", String(doc.classification.topic || "—")],
              ["Sensitivity", String(doc.classification.sensitivity || "—")],
              ["Language", String(doc.classification.language || "—")],
            ].map(([label, value]) => (
              <div key={label}>
                <p className="text-xs mb-0.5" style={{ color: "#8b92a5" }}>{label}</p>
                <p className="text-sm text-white capitalize">{value}</p>
              </div>
            ))}
            {doc.classification.summary && (
              <div className="col-span-2">
                <p className="text-xs mb-0.5" style={{ color: "#8b92a5" }}>Summary</p>
                <p className="text-sm" style={{ color: "#c4c9d4" }}>{String(doc.classification.summary)}</p>
              </div>
            )}
            {doc.classification.sensitivity_reason && (
              <div className="col-span-2">
                <p className="text-xs mb-0.5" style={{ color: "#8b92a5" }}>Sensitivity reason</p>
                <p className="text-sm" style={{ color: "#c4c9d4" }}>{String(doc.classification.sensitivity_reason)}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {doc.error_msg && (
        <div className="px-4 pb-3 text-xs" style={{ color: "#ef4444" }}>
          Error: {doc.error_msg}
        </div>
      )}
    </div>
  );
}

export default function UploadPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [dragging, setDragging] = useState(false);
  const [uploads, setUploads] = useState<{ name: string; status: string }[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);

  const loadDocs = useCallback(async () => {
    try {
      const list = await getDocuments();
      setDocs(list.reverse());
    } catch {}
  }, []);

  useEffect(() => {
    loadDocs();
    // poll for status updates every 3 seconds
    pollRef.current = setInterval(loadDocs, 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [loadDocs]);

  const handleFiles = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    const arr = Array.from(files);

    setUploads(arr.map((f) => ({ name: f.name, status: "uploading" })));

    await Promise.all(
      arr.map(async (file, i) => {
        try {
          await uploadDocument(file);
          setUploads((prev) => prev.map((u, j) => j === i ? { ...u, status: "queued" } : u));
        } catch (err: unknown) {
          const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Failed";
          setUploads((prev) => prev.map((u, j) => j === i ? { ...u, status: `error: ${msg}` } : u));
        }
      })
    );

    await loadDocs();
    setTimeout(() => setUploads([]), 3000);
  };

  const handleDelete = async (docId: string) => {
    try {
      await deleteDocument(docId);
      setDocs((prev) => prev.filter((d) => d.doc_id !== docId));
    } catch {}
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  return (
    <Layout>
      <div className="max-w-3xl mx-auto">
        <div className="mb-6">
          <h1 className="text-xl font-semibold text-white">Knowledge Base</h1>
          <p className="text-sm mt-0.5" style={{ color: "#8b92a5" }}>Upload PDFs, scanned documents, and images</p>
        </div>

        {/* drop zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current?.click()}
          className="rounded-2xl border-2 border-dashed flex flex-col items-center justify-center gap-3 py-12 cursor-pointer transition-all mb-6"
          style={{
            borderColor: dragging ? "#6c63ff" : "#252a38",
            background: dragging ? "rgba(108,99,255,0.05)" : "#181c27",
          }}
        >
          <div className="w-12 h-12 rounded-xl flex items-center justify-center" style={{ background: "rgba(108,99,255,0.15)" }}>
            <Upload size={20} style={{ color: "#6c63ff" }} />
          </div>
          <div className="text-center">
            <p className="text-sm font-medium text-white">Drop files here or click to browse</p>
            <p className="text-xs mt-1" style={{ color: "#8b92a5" }}>PDF, PNG, JPG, TIFF, TXT · Max 50MB each</p>
          </div>
          <input ref={fileRef} type="file" multiple accept=".pdf,.png,.jpg,.jpeg,.tiff,.txt" className="hidden" onChange={(e) => handleFiles(e.target.files)} />
        </div>

        {/* upload progress */}
        {uploads.length > 0 && (
          <div className="mb-4 space-y-2">
            {uploads.map((u, i) => (
              <div key={i} className="flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm" style={{ background: "#181c27", border: "1px solid #252a38" }}>
                <Loader2 size={13} className="animate-spin" style={{ color: "#6c63ff", flexShrink: 0 }} />
                <span className="flex-1 truncate text-white">{u.name}</span>
                <span style={{ color: "#8b92a5" }}>{u.status}</span>
              </div>
            ))}
          </div>
        )}

        {/* document list */}
        <div className="space-y-2">
          {docs.length === 0 ? (
            <div className="text-center py-12" style={{ color: "#8b92a5" }}>
              <p className="text-sm">No documents yet. Upload some to get started.</p>
            </div>
          ) : (
            docs.map((doc) => (
              <DocRow key={doc.doc_id} doc={doc} onDelete={handleDelete} />
            ))
          )}
        </div>
      </div>
    </Layout>
  );
}
