/*
 * FutManager — Editorial de Arquibancada.
 * Este arquivo mantém a navegação visual e não cria regras esportivas nem estado de jogo.
 */
import { useState } from "react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import Home from "./pages/Home";

export type AppSection = "inicio" | "clube" | "partidas" | "partida" | "estadio" | "time" | "ct" | "mercado" | "patrocinadores" | "transferencias" | "financas" | "operacoes";

function App() {
  const [section, setSection] = useState<AppSection>(() => {
    const requested = new URLSearchParams(window.location.search).get("section");
    const allowed: AppSection[] = ["inicio", "clube", "partidas", "partida", "estadio", "time", "ct", "mercado", "patrocinadores", "transferencias", "financas", "operacoes"];
    return allowed.includes(requested as AppSection) ? (requested as AppSection) : "inicio";
  });
  const navigate = (next: AppSection) => {
    setSection(next);
    const url = new URL(window.location.href);
    url.searchParams.set("section", next);
    window.history.replaceState({}, "", url);
  };

  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <Toaster position="bottom-right" />
          <Home section={section} onSectionChange={navigate} />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
