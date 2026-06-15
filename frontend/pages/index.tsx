import Link from "next/link";
import { Brain, Upload, MessageSquare, Shield, Zap, FileSearch } from "lucide-react";
import Layout from "../components/Layout";

export default function Home() {
  return (
    <Layout>
      <div className="max-w-2xl mx-auto pt-12 text-center">
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6" style={{ background: "linear-gradient(135deg, #6c63ff, #3d3880)" }}>
          <Brain size={30} color="white" />
        </div>
        <h1 className="text-3xl font-semibold text-white mb-3">Document Intelligence</h1>
        <p className="text-base leading-relaxed mb-10" style={{ color: "#8b92a5" }}>
          Upload messy real-world documents — scanned PDFs, handwritten pages, image-heavy reports — and get grounded answers with exact source citations.
        </p>

        <div className="flex gap-3 justify-center mb-14">
          <Link href="/upload" className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white no-underline transition-opacity hover:opacity-90"
            style={{ background: "linear-gradient(135deg, #6c63ff, #3d3880)" }}>
            <Upload size={15} /> Upload Documents
          </Link>
          <Link href="/chat" className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium no-underline transition-colors hover:bg-white/5"
            style={{ border: "1px solid #252a38", color: "#e2e5ed" }}>
            <MessageSquare size={15} /> Start Chatting
          </Link>
        </div>

        <div className="grid grid-cols-3 gap-4 text-left">
          {[
            { icon: FileSearch, title: "Smart Parsing", desc: "Handles PDFs, scans, tables, and handwriting via OCR." },
            { icon: Zap, title: "Agentic RAG", desc: "Retrieves relevant chunks and answers with inline citations." },
            { icon: Shield, title: "Secure by Design", desc: "File validation, path sanitization, and rate limiting at every layer." },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="rounded-xl p-4" style={{ background: "#181c27", border: "1px solid #252a38" }}>
              <div className="w-8 h-8 rounded-lg flex items-center justify-center mb-3" style={{ background: "rgba(108,99,255,0.15)" }}>
                <Icon size={16} style={{ color: "#6c63ff" }} />
              </div>
              <p className="text-sm font-medium text-white mb-1">{title}</p>
              <p className="text-xs leading-relaxed" style={{ color: "#8b92a5" }}>{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
