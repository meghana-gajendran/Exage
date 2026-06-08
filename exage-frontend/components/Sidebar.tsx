"use client";

import { useState } from "react";
import { Session } from "@/lib/types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Props {
  sessions: Session[];
  activeSessionId?: string;
  onSelectSession: (s: Session) => void;
  onNewSession: () => void;
  onDeleteSession: (sessionId: string) => void;
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
}: Props) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation(); // don't trigger session switch
    setDeletingId(sessionId);
    try {
      await fetch(`${BASE}/sessions/${sessionId}`, { method: "DELETE" });
      onDeleteSession(sessionId);
    } catch (err) {
      console.error("Failed to delete session", err);
    }
    setDeletingId(null);
  };

  return (
    <aside
      style={{
        width: "220px",
        minWidth: "220px",
        borderRight: "1px solid var(--border)",
        display: "flex",
        flexDirection: "column",
        padding: "24px 0",
        background: "var(--surface)",
      }}
    >
      <div
        style={{
          padding: "0 20px 24px",
          borderBottom: "1px solid var(--border-soft)",
        }}
      >
        <div
          style={{
            fontFamily: "var(--mono)",
            fontSize: "15px",
            fontWeight: 500,
            letterSpacing: "-0.3px",
          }}
        >
          Ex<span style={{ color: "var(--pink)" }}>Age</span>
        </div>
        <div
          style={{
            fontSize: "11px",
            color: "var(--text-muted)",
            marginTop: "2px",
            letterSpacing: "0.3px",
          }}
        >
          Expose what you don't know
        </div>
      </div>

      <div style={{ padding: "16px 20px 8px", flex: 1, overflowY: "auto" }}>
        <div
          style={{
            fontSize: "10px",
            fontWeight: 500,
            color: "var(--text-muted)",
            letterSpacing: "0.8px",
            textTransform: "uppercase",
            marginBottom: "8px",
          }}
        >
          Sessions
        </div>

        {sessions.length === 0 && (
          <div
            style={{
              fontSize: "12px",
              color: "var(--text-muted)",
              padding: "4px 0",
            }}
          >
            No sessions yet
          </div>
        )}

        {sessions.map((s) => (
          <div
            key={s.id}
            onMouseEnter={() => setHoveredId(s.id)}
            onMouseLeave={() => setHoveredId(null)}
            style={{ position: "relative", marginBottom: "2px" }}
          >
            <button
              onClick={() => onSelectSession(s)}
              style={{
                width: "100%",
                padding: "8px 10px",
                paddingRight: hoveredId === s.id ? "28px" : "10px",
                borderRadius: "6px",
                border:
                  s.id === activeSessionId
                    ? "1px solid var(--pink-border)"
                    : "1px solid transparent",
                background:
                  s.id === activeSessionId ? "var(--pink-soft)" : "transparent",
                textAlign: "left",
                cursor: "pointer",
                fontFamily: "var(--font)",
                transition: "padding-right 0.1s",
              }}
            >
              <div
                style={{
                  fontSize: "12.5px",
                  fontWeight: 500,
                  color:
                    s.id === activeSessionId
                      ? "var(--pink)"
                      : "var(--text-primary)",
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                }}
              >
                {s.topic}
              </div>
              <div
                style={{
                  fontSize: "11px",
                  color: "var(--text-muted)",
                  marginTop: "1px",
                }}
              >
                {s.learning_goal} · {s.turn_count}{" "}
                {s.turn_count === 1 ? "turn" : "turns"}
              </div>
            </button>

            {/* Delete button — only shows on hover */}
            {hoveredId === s.id && (
              <button
                onClick={(e) => handleDelete(e, s.id)}
                disabled={deletingId === s.id}
                title="Delete session"
                style={{
                  position: "absolute",
                  right: "6px",
                  top: "50%",
                  transform: "translateY(-50%)",
                  width: "18px",
                  height: "18px",
                  border: "none",
                  background: "none",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "var(--text-muted)",
                  borderRadius: "3px",
                  padding: 0,
                  opacity: deletingId === s.id ? 0.4 : 1,
                }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.color = "var(--pink)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.color = "var(--text-muted)")
                }
              >
                <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                  <path
                    d="M2 2l8 8M10 2l-8 8"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
            )}
          </div>
        ))}
      </div>

      <button
        onClick={onNewSession}
        style={{
          margin: "8px 20px 0",
          padding: "8px 12px",
          border: "1px dashed var(--border)",
          borderRadius: "6px",
          background: "none",
          fontFamily: "var(--font)",
          fontSize: "12px",
          color: "var(--text-muted)",
          cursor: "pointer",
          textAlign: "left",
          display: "flex",
          alignItems: "center",
          gap: "6px",
        }}
      >
        <span>+</span> New session
      </button>
    </aside>
  );
}
