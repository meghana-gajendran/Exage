"use client";

import { useState, useCallback, useEffect } from "react";
import { Session, ChatMessage, LearningGoal, Gap } from "@/lib/types";
import {
  createSession,
  streamChat,
  getAllSessions,
  getSessionMessages,
} from "@/lib/api";
import Sidebar from "@/components/Sidebar";
import ChatHeader from "@/components/ChatHeader";
import MessageList from "@/components/MessageList";
import StatusBar from "@/components/StatusBar";
import InputArea from "@/components/InputArea";
import OnboardingModal from "@/components/OnboardingModal";

let msgCounter = 0;
const newId = () => `msg-${++msgCounter}`;

export default function ChatPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  useEffect(() => {
    async function loadSessions() {
      const existing = await getAllSessions();
      if (existing.length > 0) {
        setSessions(existing);
        const latest = existing[existing.length - 1];
        setSession(latest);
        await loadMessages(latest);
      } else {
        setShowOnboarding(true);
      }
    }
    loadSessions();
  }, []);

  const loadMessages = async (s: Session) => {
    setLoadingHistory(true);
    const msgs = await getSessionMessages(s.id);
    if (msgs.length > 0) {
      setMessages(
        msgs.map((m) => ({
          id: newId(),
          role: m.role as "user" | "assistant",
          content: m.content,
        })),
      );
    } else {
      setMessages([
        {
          id: newId(),
          role: "assistant",
          content: `What do you already feel confident about in ${s.topic}? Walk me through what you know.`,
        },
      ]);
    }
    setLoadingHistory(false);
  };

  const startSession = useCallback(
    async (topic: string, goal: LearningGoal) => {
      const newSession = await createSession(topic, goal);
      setSessions((prev) => [...prev, newSession]);
      setSession(newSession);
      setMessages([
        {
          id: newId(),
          role: "assistant",
          content: `What do you already feel confident about in ${topic}? Walk me through what you know.`,
        },
      ]);
      setShowOnboarding(false);
    },
    [],
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (!session || isStreaming) return;

      const userMsg: ChatMessage = { id: newId(), role: "user", content: text };
      const assistantMsgId = newId();
      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);
      setStatus("Analyzing your explanation…");

      let accumulatedText = "";
      let detectedGaps: Gap[] = [];
      let hasError = false;

      try {
        for await (const event of streamChat(session.id, text)) {
          if (event.type === "status" && event.text) {
            setStatus(event.text);
          } else if (event.type === "token" && event.text) {
            accumulatedText += event.text;
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantMsgId
                  ? { ...m, content: accumulatedText }
                  : m,
              ),
            );
          } else if (event.type === "error") {
            hasError = true;
            accumulatedText = "Something went wrong. Please try again.";
          } else if (event.type === "done") {
            if (event.gaps) detectedGaps = event.gaps;
            const updatedSession = {
              ...session,
              phase: event.phase || session.phase,
              turn_count: event.turn || session.turn_count,
            };
            setSession(updatedSession);
            setSessions((prev) =>
              prev.map((s) =>
                s.id === updatedSession.id ? updatedSession : s,
              ),
            );
          }
        }
      } catch (err) {
        console.error("Stream error:", err);
        hasError = true;
        accumulatedText =
          "Connection lost. Please check the backend is running and try again.";
      }

      // Bug 1 fix: if no content came back at all, remove the bubble entirely
      if (!accumulatedText && !hasError) {
        setMessages((prev) => prev.filter((m) => m.id !== assistantMsgId));
      } else {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? {
                  ...m,
                  content: accumulatedText,
                  isStreaming: false,
                  gaps: detectedGaps.length ? detectedGaps : undefined,
                }
              : m,
          ),
        );
      }

      setIsStreaming(false);
      setStatus(null);
    },
    [session, isStreaming],
  );

  const switchSession = useCallback(async (s: Session) => {
    setSession(s);
    await loadMessages(s);
  }, []);

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {showOnboarding && <OnboardingModal onStart={startSession} />}

      <Sidebar
        sessions={sessions}
        activeSessionId={session?.id}
        onSelectSession={switchSession}
        onNewSession={() => setShowOnboarding(true)}
      />

      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        <ChatHeader session={session} />
        {loadingHistory ? (
          <div
            style={{
              flex: 1,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "var(--text-muted)",
              fontSize: "13px",
            }}
          >
            Loading…
          </div>
        ) : (
          <MessageList messages={messages} />
        )}
        {status && <StatusBar text={status} />}
        <InputArea onSend={sendMessage} disabled={!session || isStreaming} />
      </div>
    </div>
  );
}
