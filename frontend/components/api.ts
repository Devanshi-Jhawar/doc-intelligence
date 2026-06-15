import axios from "axios";

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  timeout: 120000,
});

export interface Citation {
  filename: string;
  page_num: number;
  doc_id: string;
  image_path: string | null;
  score: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
}

export interface Document {
  doc_id: string;
  filename: string;
  status: "queued" | "parsing" | "classifying" | "indexing" | "ready" | "error";
  uploaded_at: string;
  num_pages: number | null;
  classification: Record<string, unknown> | null;
  file_hash: string | null;
  error_msg: string | null;
}

export const uploadDocument = async (file: File) => {
  const form = new FormData();
  form.append("file", file);
  const res = await API.post("/documents/upload", form);
  return res.data;
};

export const getDocuments = async (): Promise<Document[]> => {
  const res = await API.get("/documents");
  return res.data;
};

export const getDocument = async (docId: string): Promise<Document> => {
  const res = await API.get(`/documents/${docId}`);
  return res.data;
};

export const deleteDocument = async (docId: string) => {
  const res = await API.delete(`/documents/${docId}`);
  return res.data;
};

export const chat = async (query: string, history: { role: string; content: string }[]): Promise<ChatResponse> => {
  const res = await API.post("/chat", { query, history });
  return res.data;
};

export const pageImageUrl = (docId: string, pageNum: number) =>
  `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/documents/${docId}/page/${pageNum}/image`;
