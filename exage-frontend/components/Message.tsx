"use client";

import { ChatMessage } from "@/lib/types";
import GapBlock from "./GapBlock";
import SynthesisBlock from "./SynthesisBlock";

interface Props {
  message: ChatMessage;
  onExplorePath?: (question: string) => void;
}

export default function Message({ message, onExplorePath }: Props) {
  const isUser = message.role === "user";

  // Synthesis messages get their own full-width treatment
  if (message.isSynthesis && message.synthesisData) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: "6px",
          maxWidth: "680px",
          alignSelf: "flex-start",
          alignItems: "flex-start",
        }}
      >
        <span
          style={{
            fontSize: "10.5px",
            fontWeight: 500,
            color: "var(--text-muted)",
            letterSpacing: "0.5px",
            textTransform: "uppercase",
          }}
        >
          ExAge — Session Summary
        </span>
        <SynthesisBlock
          data={message.synthesisData}
          onExplorePath={onExplorePath || (() => {})}
        />
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        maxWidth: "680px",
        alignSelf: isUser ? "flex-end" : "flex-start",
        alignItems: isUser ? "flex-end" : "flex-start",
      }}
    >
      <span
        style={{
          fontSize: "10.5px",
          fontWeight: 500,
          color: "var(--text-muted)",
          letterSpacing: "0.5px",
          textTransform: "uppercase",
        }}
      >
        {isUser ? "You" : "ExAge"}
      </span>

      <div
        style={{
          padding: "12px 16px",
          borderRadius: isUser ? "10px 10px 2px 10px" : "2px 10px 10px 10px",
          fontSize: "13.5px",
          lineHeight: 1.65,
          background: isUser ? "var(--text-primary)" : "var(--surface)",
          color: isUser ? "#fafaf9" : "var(--text-primary)",
          border: isUser ? "none" : "1px solid var(--border)",
        }}
      >
        {message.isStreaming && !message.content ? (
          <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
            …
          </span>
        ) : (
          <span
            dangerouslySetInnerHTML={{ __html: formatContent(message.content) }}
          />
        )}
      </div>

      {message.gaps && message.gaps.length > 0 && (
        <GapBlock gaps={message.gaps} />
      )}
    </div>
  );
}

function formatContent(text: string): string {
  return text.replace(/`([^`]+)`/g, "<code>$1</code>");
}
