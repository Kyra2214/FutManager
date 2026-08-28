/*
 * FutManager — feedback sonoro e háptico (Submódulo 9d).
 *
 * Decisão de escopo (menor impacto): nenhum arquivo de áudio é adicionado ao
 * projeto — o app não tinha pipeline de assets de som (ver
 * docs/PLANO_MUDANCA_VISUAL.md, Submódulo 9d) e licenciar/escolher sons é
 * decisão de produto fora do escopo de um ajuste visual. Os tons são
 * sintetizados em tempo real via Web Audio API (osciladores simples,
 * nenhuma biblioteca nova). O háptico usa `navigator.vibrate`, com todas as
 * limitações já registradas no plano (só alguns navegadores móveis, só a
 * partir de gesto do usuário) — degradação silenciosa quando indisponível.
 */

export type FeedbackKind = "success" | "error";

let audioCtx: AudioContext | null = null;

function getAudioContext(): AudioContext | null {
  if (typeof window === "undefined") return null;
  const AudioCtor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!AudioCtor) return null;
  if (!audioCtx) {
    try {
      audioCtx = new AudioCtor();
    } catch {
      return null;
    }
  }
  if (audioCtx.state === "suspended") {
    void audioCtx.resume().catch(() => undefined);
  }
  return audioCtx;
}

/**
 * Toca um tom curto sintetizado. Dois timbres, cada um mapeado a um dos
 * tons já usados por `toast.success`/`toast.error` (sonner) nos pontos de
 * mutação da aplicação — mesma leitura, com reforço sonoro.
 */
export function playFeedbackTone(kind: FeedbackKind): void {
  const ctx = getAudioContext();
  if (!ctx) return;
  try {
    const now = ctx.currentTime;
    const gain = ctx.createGain();
    gain.connect(ctx.destination);
    gain.gain.setValueAtTime(0, now);

    const notes = kind === "success" ? [523.25, 783.99] : [220, 174.61];
    const step = 0.09;
    notes.forEach((freq, index) => {
      const osc = ctx.createOscillator();
      osc.type = kind === "success" ? "sine" : "triangle";
      osc.frequency.setValueAtTime(freq, now + index * step);
      osc.connect(gain);
      osc.start(now + index * step);
      osc.stop(now + index * step + step);
    });

    gain.gain.linearRampToValueAtTime(0.12, now + 0.01);
    gain.gain.linearRampToValueAtTime(0, now + notes.length * step + 0.05);
  } catch {
    // Síntese falhou (ex.: contexto bloqueado fora de gesto do usuário) — sem som, sem quebrar o fluxo.
  }
}

/** Dispara vibração curta, quando suportado. Falha silenciosa em qualquer outro caso. */
export function triggerHapticFeedback(kind: FeedbackKind): void {
  if (typeof navigator === "undefined" || typeof navigator.vibrate !== "function") return;
  try {
    navigator.vibrate(kind === "success" ? [18] : [30, 40, 30]);
  } catch {
    // Vibração indisponível/bloqueada — comportamento normal em boa parte dos navegadores.
  }
}
