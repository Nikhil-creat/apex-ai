"use client";
import { useRef, useState } from "react";

type Msg = { role: "user" | "assistant"; text: string };

export default function Chat() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [tools, setTools] = useState<string[]>([]);
  const [listening, setListening] = useState(false);
  const rec = useRef<any>(null);

  async function send(text: string) {
    if (!text.trim()) return;
    setMsgs((m) => [...m, { role: "user", text }, { role: "assistant", text: "" }]);
    setInput(""); setTools([]);
    const res = await fetch(`${process.env.NEXT_PUBLIC_API}/chat`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: text }),
    });
    const reader = res.body!.getReader(); const dec = new TextDecoder(); let buf = "";
    for (;;) {
      const { done, value } = await reader.read(); if (done) break;
      buf += dec.decode(value, { stream: true });
      const events = buf.split("\n\n"); buf = events.pop()!;
      for (const e of events) {
        const ev = JSON.parse(e.replace(/^data: /, ""));       // {type:"token"|"tool", data}
        if (ev.type === "tool") setTools((t) => [...t, ev.data]);
        else setMsgs((m) => { const c = [...m]; c[c.length - 1].text += ev.data; return c; });
      }
    }
  }

  function toggleVoice() {
    const SR = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SR) return alert("Voice input is not supported in this browser.");
    if (listening) { rec.current?.stop(); return; }
    rec.current = new SR(); rec.current.onresult = (e: any) => send(e.results[0][0].transcript);
    rec.current.onend = () => setListening(false); rec.current.start(); setListening(true);
  }

  return (
    <div className="mx-auto flex h-screen max-w-2xl flex-col p-4">
      <div className="flex-1 space-y-3 overflow-y-auto">
        {msgs.map((m, i) => (
          <p key={i} className={m.role === "user" ? "text-right" : ""}>{m.text}</p>
        ))}
      </div>
      <div className="flex flex-wrap gap-2 py-2">
        {tools.map((t, i) => <span key={i} className="rounded-full bg-blue-100 px-2 py-0.5 text-xs dark:bg-blue-900">{t}</span>)}
      </div>
      <div className="flex gap-2">
        <input className="flex-1 rounded border p-2" value={input} onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send(input)} placeholder="Ask APEX-AI" />
        <button onClick={toggleVoice} className="rounded border px-3" aria-pressed={listening}>{listening ? "Stop" : "Voice"}</button>
        <button onClick={() => send(input)} className="rounded bg-blue-600 px-4 text-white">Send</button>
      </div>
    </div>
  );
}
