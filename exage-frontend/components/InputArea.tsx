"use client";

import { useState, useRef, KeyboardEvent } from "react";

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export default function InputArea({ onSend, disabled }: Props) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // B4 fix: trim and check before sending
  const canSend = value.trim().length > 0 && !disabled;

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  };

  return (
    <div
      style={{
        padding: "16px 32px 20px",
        background: "var(--surface)",
        borderTop: "1px solid var(--border)",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "flex-end",
          gap: "10px",
          border: "1px solid var(--border)",
          borderRadius: "10px",
          padding: "10px 12px",
          background: "var(--bg)",
          transition: "border-color 0.15s",
        }}
        onFocus={(e) =>
          (e.currentTarget.style.borderColor = "var(--pink-border)")
        }
        onBlur={(e) => (e.currentTarget.style.borderColor = "var(--border)")}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          disabled={disabled}
          placeholder={
            disabled
              ? "Start a session to begin…"
              : "Explain what you know, or respond to the question above…"
          }
          rows={1}
          style={{
            flex: 1,
            border: "none",
            background: "none",
            fontFamily: "var(--font)",
            fontSize: "13.5px",
            color: "var(--text-primary)",
            resize: "none",
            outline: "none",
            lineHeight: 1.5,
            minHeight: "20px",
            maxHeight: "120px",
            overflowY: "auto",
          }}
        />
        <button
          onClick={handleSend}
          disabled={!canSend}
          style={{
            width: "30px",
            height: "30px",
            borderRadius: "6px",
            border: "none",
            background: canSend ? "var(--pink)" : "var(--border)",
            color: "white",
            cursor: canSend ? "pointer" : "not-allowed",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
            transition: "background 0.15s",
          }}
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path
              d="M7 12V2M2 7l5-5 5 5"
              stroke="white"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </button>
      </div>
      <div
        style={{
          fontSize: "11px",
          color: "var(--text-muted)",
          marginTop: "8px",
          paddingLeft: "2px",
        }}
      >
        Press Enter to send · Shift+Enter for new line
      </div>
    </div>
  );
}
