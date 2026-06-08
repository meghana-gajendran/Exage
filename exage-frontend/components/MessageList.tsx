"use client";

import { useEffect, useRef } from "react";
import { ChatMessage } from "@/lib/types";
import Message from "./Message";

interface Props {
  messages: ChatMessage[];
  onExplorePath?: (question: string) => void;
}

export default function MessageList({ messages, onExplorePath }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div
      style={{
        flex: 1,
        overflowY: "auto",
        padding: "32px",
        display: "flex",
        flexDirection: "column",
        gap: "24px",
      }}
    >
      {messages.length === 0 && (
        <div
          style={{
            margin: "auto",
            textAlign: "center",
            color: "var(--text-muted)",
            fontSize: "13px",
            lineHeight: 1.6,
          }}
        >
          <div style={{ fontSize: "24px", marginBottom: "12px" }}>◎</div>
          Start a session to begin exploring your understanding.
        </div>
      )}
      {messages.map((msg) => (
        <Message key={msg.id} message={msg} onExplorePath={onExplorePath} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
