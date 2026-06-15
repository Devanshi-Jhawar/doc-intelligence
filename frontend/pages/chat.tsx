import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Mic, MicOff, Loader2, FileText } from "lucide-react";
import Layout from "../components/Layout";
import PageThumb from "../components/PageThumb";
import { chat, Citation } from "../components/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
  interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    start(): void;
    stop(): void;
    onresult: ((event: SpeechRecognitionEvent) => void) | null;
    onerror: ((event: Event) => void) | null;
    onend: (() => void) | null;
  }
  interface SpeechRecognitionEvent extends Event {
    resultIndex: number;
    results: SpeechRecognitionResultList;
  }
}
export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = useCallback(async (text?: string) => {
    const query = (text || input).trim();
    if (!query || loading) return;

    const userMsg: Message = { role: "user", content: query };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setTranscript("");
    setLoading(true);
    setError("");

    // build history for API
    const history = messages.map((m) => ({ role: m.role, content: m.content }));

    try {
      const res = await chat(query, history);
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, citations: res.citations },
      ]);
    } catch {
      setError("Failed to get a response. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }, [input, loading, messages]);

  const toggleVoice = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      setError("Voice input is not supported in this browser. Try Chrome.");
      return;
    }

    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const rec = new SR();
    rec.continuous = true;
    rec.interimResults = true;
    rec.lang = "en-US";

    rec.onresult = (event) => {
      let interim = "";
      let final = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) final += t;
        else interim += t;
      }
      setTranscript(interim);
      if (final) {
        setInput((prev) => prev + final);
        setTranscript("");
      }
    };

    rec.onerror = () => setListening(false);
    rec.onend = () => setListening(false);

    rec.start();
    recognitionRef.current = rec;
    setListening(true);
  }, [listening]);

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <Layout>
      <div className="flex flex-col h-[calc(100vh-120px)]">
        <div className="mb-4">
          <h1 className="text-xl font-semibold text-white">Document Chat</h1>
          <p className="text-sm mt-0.5" style={{ color: "#8b92a5" }}>Ask anything about your uploaded documents</p>
        </div>

        {/* message list */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1 pb-2">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-3" style={{ color: "#8b92a5" }}>
              <FileText size={40} strokeWidth={1} />
              <p className="text-sm">Upload documents and start asking questions</p>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div
                className="rounded-xl px-4 py-3 max-w-2xl text-sm leading-relaxed"
                style={
                  msg.role === "user"
                    ? { background: "rgba(108,99,255,0.25)", color: "#e2e5ed", maxWidth: "70%" }
                    : { background: "#181c27", border: "1px solid #252a38", color: "#e2e5ed", maxWidth: "85%" }
                }
              >
                <p className="whitespace-pre-wrap">{msg.content}</p>

                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-3" style={{ borderTop: "1px solid #252a38" }}>
                    <p className="text-xs mb-2" style={{ color: "#8b92a5" }}>Sources</p>
                    <div className="flex flex-wrap gap-2 items-start">
                      {msg.citations.map((c, j) => (
                        <div key={j} className="flex flex-col items-center gap-1">
                          <PageThumb docId={c.doc_id} pageNum={c.page_num} filename={c.filename} />
                          <span className="citation-badge">{c.filename.slice(0, 16)}… p.{c.page_num}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-xl px-4 py-3 text-sm" style={{ background: "#181c27", border: "1px solid #252a38", color: "#8b92a5" }}>
                <Loader2 size={14} className="animate-spin" />
                Thinking…
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {error && (
          <div className="mb-2 px-3 py-2 rounded-lg text-sm" style={{ background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.3)", color: "#ef4444" }}>
            {error}
          </div>
        )}

        {/* voice transcript preview */}
        {transcript && (
          <div className="mb-2 px-3 py-2 rounded-lg text-sm italic" style={{ background: "rgba(108,99,255,0.1)", border: "1px solid rgba(108,99,255,0.2)", color: "#a5a0ff" }}>
            {transcript}
          </div>
        )}

        {/* input bar */}
        <div className="flex items-end gap-2 pt-3" style={{ borderTop: "1px solid #252a38" }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ask about your documents… (Enter to send)"
            rows={2}
            className="flex-1 resize-none rounded-xl px-4 py-3 text-sm outline-none transition-colors"
            style={{ background: "#181c27", border: "1px solid #252a38", color: "#e2e5ed", lineHeight: 1.5 }}
          />
          <button
            onClick={toggleVoice}
            className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-colors"
            style={{ background: listening ? "rgba(239,68,68,0.15)" : "#252a38", border: `1px solid ${listening ? "rgba(239,68,68,0.4)" : "#252a38"}` }}
            title={listening ? "Stop voice" : "Start voice input"}
          >
            {listening ? <MicOff size={15} color="#ef4444" /> : <Mic size={15} color="#8b92a5" />}
          </button>
          <button
            onClick={() => send()}
            disabled={!input.trim() || loading}
            className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-opacity"
            style={{ background: "linear-gradient(135deg, #6c63ff, #3d3880)", opacity: (!input.trim() || loading) ? 0.4 : 1 }}
          >
            <Send size={15} color="white" />
          </button>
        </div>
      </div>
    </Layout>
  );
}
