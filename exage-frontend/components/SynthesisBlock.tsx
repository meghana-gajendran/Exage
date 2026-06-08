"use client";

import { SynthesisData } from "@/lib/types";

interface Props {
  data: SynthesisData;
  onExplorePath: (question: string) => void;
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: "var(--pink)",
  important: "#f0a070",
  "nice-to-know": "var(--border)",
};

export default function SynthesisBlock({ data, onExplorePath }: Props) {
  return (
    <div
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        borderRadius: "10px",
        padding: "20px",
        maxWidth: "600px",
        display: "flex",
        flexDirection: "column",
        gap: "20px",
      }}
    >
      {/* Opening */}
      <div
        style={{
          fontSize: "13.5px",
          color: "var(--text-primary)",
          lineHeight: 1.65,
        }}
      >
        {data.opening}
      </div>

      {/* Gaps */}
      {data.gaps_summary.length > 0 && (
        <div>
          <div style={sectionLabel}>Gaps identified</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {data.gaps_summary.map((g, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  gap: "10px",
                  alignItems: "flex-start",
                }}
              >
                <div
                  style={{
                    width: "6px",
                    height: "6px",
                    borderRadius: "50%",
                    background: SEVERITY_COLORS[g.severity] || "var(--border)",
                    marginTop: "6px",
                    flexShrink: 0,
                  }}
                />
                <div>
                  <span
                    style={{
                      fontSize: "12.5px",
                      fontWeight: 500,
                      color: "var(--text-primary)",
                    }}
                  >
                    {g.concept}
                  </span>
                  <span
                    style={{
                      fontSize: "12px",
                      color: "var(--text-muted)",
                      marginLeft: "6px",
                    }}
                  >
                    — {g.one_line}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Misconceptions */}
      {data.misconceptions_summary.length > 0 && (
        <div>
          <div style={sectionLabel}>Worth revisiting</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {data.misconceptions_summary.map((m, i) => (
              <div
                key={i}
                style={{
                  display: "flex",
                  gap: "10px",
                  alignItems: "flex-start",
                }}
              >
                <div
                  style={{
                    width: "6px",
                    height: "6px",
                    borderRadius: "50%",
                    background: "var(--border-soft)",
                    border: "1px solid var(--border)",
                    marginTop: "6px",
                    flexShrink: 0,
                  }}
                />
                <div>
                  <span
                    style={{
                      fontSize: "12.5px",
                      fontWeight: 500,
                      color: "var(--text-primary)",
                    }}
                  >
                    {m.concept}
                  </span>
                  <span
                    style={{
                      fontSize: "12px",
                      color: "var(--text-muted)",
                      marginLeft: "6px",
                    }}
                  >
                    — {m.what_to_revisit}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Curiosity paths */}
      {data.curiosity_paths.length > 0 && (
        <div>
          <div style={sectionLabel}>Where to go next</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {data.curiosity_paths.map((path, i) => (
              <button
                key={i}
                onClick={() => onExplorePath(path.starter_question)}
                style={{
                  padding: "12px 14px",
                  border: "1px solid var(--border)",
                  borderRadius: "8px",
                  background: "var(--bg)",
                  textAlign: "left",
                  cursor: "pointer",
                  fontFamily: "var(--font)",
                  transition: "border-color 0.15s, background 0.15s",
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor =
                    "var(--pink-border)";
                  (e.currentTarget as HTMLElement).style.background =
                    "var(--pink-soft)";
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.borderColor =
                    "var(--border)";
                  (e.currentTarget as HTMLElement).style.background =
                    "var(--bg)";
                }}
              >
                <div
                  style={{
                    fontSize: "12.5px",
                    fontWeight: 500,
                    color: "var(--text-primary)",
                    marginBottom: "3px",
                  }}
                >
                  {path.title}
                </div>
                <div
                  style={{
                    fontSize: "12px",
                    color: "var(--text-muted)",
                    lineHeight: 1.5,
                  }}
                >
                  {path.description}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Closing thought */}
      <div
        style={{
          borderTop: "1px solid var(--border-soft)",
          paddingTop: "16px",
          fontSize: "13.5px",
          color: "var(--text-secondary)",
          lineHeight: 1.65,
          fontStyle: "italic",
        }}
      >
        {data.closing_thought}
      </div>
    </div>
  );
}

const sectionLabel: React.CSSProperties = {
  fontSize: "10px",
  fontWeight: 500,
  color: "var(--text-muted)",
  letterSpacing: "0.7px",
  textTransform: "uppercase",
  marginBottom: "10px",
};
