import React, { createContext, useCallback, useContext, useMemo, useState } from "react";
import { playFeedbackTone, triggerHapticFeedback, type FeedbackKind } from "@/lib/feedback";

interface FeedbackContextType {
  enabled: boolean;
  toggleFeedback: () => void;
  notify: (kind: FeedbackKind) => void;
}

// Componentes também são renderizados isoladamente em testes e integrações.
// Sem um provider, o feedback é deliberadamente um no-op; no App o provider
// real substitui este fallback e habilita som/háptico conforme a preferência.
const FeedbackContext = createContext<FeedbackContextType>({
  enabled: false,
  toggleFeedback: () => undefined,
  notify: () => undefined,
});

const STORAGE_KEY = "feedback-enabled";

interface FeedbackProviderProps {
  children: React.ReactNode;
  defaultEnabled?: boolean;
}

export function FeedbackProvider({ children, defaultEnabled = true }: FeedbackProviderProps) {
  const [enabled, setEnabled] = useState<boolean>(() => {
    if (typeof window === "undefined") return defaultEnabled;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === null ? defaultEnabled : stored === "true";
  });

  const toggleFeedback = useCallback(() => {
    setEnabled((prev: boolean) => {
      const next = !prev;
      if (typeof window !== "undefined") {
        window.localStorage.setItem(STORAGE_KEY, String(next));
      }
      return next;
    });
  }, []);

  const notify = useCallback(
    (kind: FeedbackKind) => {
      if (!enabled) return;
      playFeedbackTone(kind);
      triggerHapticFeedback(kind);
    },
    [enabled],
  );

  const value = useMemo(() => ({ enabled, toggleFeedback, notify }), [enabled, toggleFeedback, notify]);

  return <FeedbackContext.Provider value={value}>{children}</FeedbackContext.Provider>;
}

export function useFeedback() {
  return useContext(FeedbackContext);
}
