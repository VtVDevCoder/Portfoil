import { useCallback, useRef, useState } from "react";
import api from "../api/client";

type Mode = "text" | "file";
type Message = { type: "success" | "error"; text: string };

const ACCEPTED = [".txt", ".csv", ".json"];
const MAX_BYTES = 10 * 1024 * 1024;

interface Props {
  onSuccess: () => void;
}

export default function UploadForm({ onSuccess }: Props) {
  const [mode, setMode] = useState<Mode>("text");
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<Message | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // --- validação de arquivo (reutilizada por drag e pelo input) ---
  const validateAndSet = useCallback((f: File): boolean => {
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      setMessage({
        type: "error",
        text: "Formato inválido. Use .txt, .csv ou .json.",
      });
      return false;
    }
    if (f.size > MAX_BYTES) {
      setMessage({
        type: "error",
        text: "Arquivo muito grande. Limite: 10 MB.",
      });
      return false;
    }
    setMessage(null);
    setFile(f);
    return true;
  }, []);

  // --- drag handlers ---
  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setDragging(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    // só desativa se sair da drop zone de verdade (não de um filho)
    if (!e.currentTarget.contains(e.relatedTarget as Node)) {
      setDragging(false);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) validateAndSet(dropped);
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0];
    if (selected) validateAndSet(selected);
  }

  function handleModeChange(next: Mode) {
    setMode(next);
    setFile(null);
    setText("");
    setMessage(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  // --- submit ---
  async function handleSubmit() {
    setLoading(true);
    setMessage(null);
    try {
      if (mode === "file" && file) {
        const formData = new FormData();
        formData.append("file", file);
        await api.post("/feedback-batches/", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
        setMessage({
          type: "success",
          text: `✓ "${file.name}" enviado para análise.`,
        });
      } else {
        const lines = text
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean);
        if (!lines.length) return;
        await api.post("/feedback-batches/", { raw_text_list: lines });
        setText("");
        setMessage({
          type: "success",
          text: `✓ ${lines.length} feedback(s) enviados para análise.`,
        });
      }
      onSuccess();
    } catch (err: any) {
      const detail =
        err?.response?.data?.error ?? "Falha no envio. Tente novamente.";
      setMessage({ type: "error", text: detail });
    } finally {
      setLoading(false);
    }
  }

  const canSubmit =
    !loading && (mode === "text" ? text.trim().length > 0 : file !== null);

  // --- render ---
  return (
    <div className="space-y-4">
      {/* Toggle */}
      <div className="flex gap-1 bg-gray-800 rounded-lg p-1 w-fit">
        {(["text", "file"] as Mode[]).map((m) => (
          <button
            key={m}
            onClick={() => handleModeChange(m)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              mode === m
                ? "bg-indigo-600 text-white"
                : "text-gray-400 hover:text-white"
            }`}
          >
            {m === "text" ? "✏️ Texto" : "📁 Arquivo"}
          </button>
        ))}
      </div>

      {/* Textarea */}
      {mode === "text" && (
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={
            "Cole os feedbacks aqui, um por linha…\n\nO app travou no checkout.\nAmei o novo design!\nO suporte demora muito."
          }
          rows={6}
          className="w-full bg-gray-800 border border-gray-700 rounded-lg p-3 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 resize-none transition-colors font-mono"
        />
      )}

      {/* Drop zone */}
      {mode === "file" && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
            dragging
              ? "border-indigo-400 bg-indigo-950/40" // estado de drag ativo
              : "border-gray-700 hover:border-indigo-500"
          }`}
        >
          {/* Ícone */}
          <div
            className={`mx-auto mb-3 w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
              dragging ? "bg-indigo-500/20" : "bg-gray-800"
            }`}
          >
            <svg
              className={`w-5 h-5 ${dragging ? "text-indigo-400" : "text-gray-400"}`}
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
              />
            </svg>
          </div>

          <p className="text-sm text-white font-medium mb-1">
            {dragging ? "Solte o arquivo aqui" : "Arraste o arquivo aqui"}
          </p>
          <p className="text-xs text-gray-500 mb-4">
            .txt · .csv · .json — máx. 10 MB
          </p>

          {/* Input oculto + label clicável */}
          <label className="cursor-pointer text-xs text-indigo-400 hover:text-indigo-300 transition-colors">
            ou selecione manualmente
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED.join(",")}
              onChange={handleInputChange}
              className="hidden"
            />
          </label>

          {/* Arquivo selecionado */}
          {file && (
            <div className="mt-4 flex items-center justify-center gap-2">
              <span className="text-xs bg-gray-800 text-indigo-400 border border-gray-700 rounded-md px-3 py-1">
                📄 {file.name} — {(file.size / 1024).toFixed(1)} KB
              </span>
              <button
                onClick={() => {
                  setFile(null);
                  if (fileInputRef.current) fileInputRef.current.value = "";
                }}
                className="text-gray-500 hover:text-red-400 transition-colors text-xs"
                aria-label="Remover arquivo"
              >
                ✕
              </button>
            </div>
          )}
        </div>
      )}

      {/* Ações */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleSubmit}
          disabled={!canSubmit}
          className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
        >
          {loading ? "Enviando…" : "Analisar Feedbacks"}
        </button>

        {message && (
          <p
            className={`text-sm ${message.type === "success" ? "text-green-400" : "text-red-400"}`}
          >
            {message.text}
          </p>
        )}
      </div>
    </div>
  );
}
