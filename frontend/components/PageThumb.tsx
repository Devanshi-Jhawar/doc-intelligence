import { useState } from "react";
import { X, ZoomIn } from "lucide-react";
import { pageImageUrl } from "./api";

interface PageThumbProps {
  docId: string;
  pageNum: number;
  filename: string;
}

export default function PageThumb({ docId, pageNum, filename }: PageThumbProps) {
  const [open, setOpen] = useState(false);
  const url = pageImageUrl(docId, pageNum);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="group relative flex-shrink-0 rounded-lg overflow-hidden cursor-pointer border transition-all"
        style={{ width: 80, height: 104, background: "#252a38", borderColor: "#252a38" }}
        title={`${filename} — page ${pageNum}`}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={url}
          alt={`page ${pageNum}`}
          className="w-full h-full object-cover"
          loading="lazy"
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
        />
        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity" style={{ background: "rgba(0,0,0,0.5)" }}>
          <ZoomIn size={16} color="white" />
        </div>
        <div className="absolute bottom-0 left-0 right-0 px-1 py-0.5 text-center" style={{ background: "rgba(0,0,0,0.7)", fontSize: 9, color: "#8b92a5" }}>
          p.{pageNum}
        </div>
      </button>

      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          style={{ background: "rgba(0,0,0,0.85)" }}
          onClick={() => setOpen(false)}
        >
          <div
            className="relative rounded-xl overflow-hidden shadow-2xl"
            style={{ maxWidth: "90vw", maxHeight: "90vh" }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setOpen(false)}
              className="absolute top-3 right-3 z-10 rounded-full p-1.5"
              style={{ background: "rgba(0,0,0,0.7)" }}
            >
              <X size={16} color="white" />
            </button>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={url}
              alt={`${filename} page ${pageNum}`}
              style={{ maxWidth: "85vw", maxHeight: "85vh", objectFit: "contain" }}
            />
            <div className="absolute bottom-0 left-0 right-0 px-4 py-2 text-sm" style={{ background: "rgba(0,0,0,0.7)", color: "#8b92a5" }}>
              {filename} — page {pageNum}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
