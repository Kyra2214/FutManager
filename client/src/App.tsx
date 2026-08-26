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

export type AppSection = "inicio" | "estadio" | "time" | "ct" | "mercado" | "transferencias";

function App() {
  const [section, setSection] = useState<AppSection>("inicio");

  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light">
        <TooltipProvider>
          <Toaster position="bottom-right" />
          <Home section={section} onSectionChange={setSection} />
        </TooltipProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
