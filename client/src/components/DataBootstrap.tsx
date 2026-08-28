import { Capacitor } from "@capacitor/core";
import { useEffect, useState, type ReactNode } from "react";
import { Download, RefreshCw, Wifi } from "lucide-react";
import { NativeEngine } from "@/lib/offline/nativeEngine";

const DEFAULT_MANIFEST_URL = "https://github.com/Kyra2214/FutManager-data/releases/download/v1.0.0/manifest.json";

export function DataBootstrap({ children }: { children: ReactNode }) {
  const isNative = Capacitor.isNativePlatform();
  const [ready, setReady] = useState<boolean | undefined>(isNative ? undefined : true);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const checkStatus = async () => {
    if (!isNative) return;
    setError("");
    try {
      const status = await NativeEngine.getDataStatus();
      setReady(status.ready);
    } catch (reason) {
      setReady(false);
      setError(reason instanceof Error ? reason.message : "Não foi possível verificar os dados locais.");
    }
  };

  useEffect(() => {
    void checkStatus();
  }, [isNative]);

  const prepare = async () => {
    setPending(true);
    setError("");
    try {
      await NativeEngine.prepareData({
        manifestUrl: import.meta.env.VITE_FUTMANAGER_DATA_MANIFEST_URL || DEFAULT_MANIFEST_URL,
      });
      setReady(true);
    } catch (reason) {
      setReady(false);
      setError(reason instanceof Error ? reason.message : "Não foi possível baixar os dados do jogo.");
    } finally {
      setPending(false);
    }
  };

  if (!isNative || ready === true) return <>{children}</>;

  return <main className="career-start-shell data-bootstrap-shell">
    <section className="career-start-hero">
      <div className="career-start-brand"><span>FUT</span><b>MANAGER</b></div>
      <div className="career-start-kicker">PREPARAÇÃO INICIAL · PRIMEIRO ACESSO</div>
      <h1>Seu universo<br /><em>está chegando.</em></h1>
      <p>O aplicativo foi instalado de forma enxuta. Agora vamos baixar o banco e os escudos uma única vez para liberar o jogo offline.</p>
    </section>
    <section className="career-start-panel data-bootstrap-panel" aria-live="polite">
      <div className="data-bootstrap-icon">{pending ? <RefreshCw size={28} className="data-bootstrap-spin" /> : <Download size={28} />}</div>
      <span className="eyebrow">PACOTE DE DADOS FUTMANAGER</span>
      <h2>{pending ? "Baixando os dados…" : "Conecte-se para preparar o jogo"}</h2>
      <p>{pending ? "O download pode levar alguns minutos. Não feche o aplicativo." : "Essa etapa é necessária somente na primeira execução. Depois dela, o banco e os assets ficam salvos no aparelho e o jogo funciona offline."}</p>
      {error && <p className="career-error" role="alert">Não foi possível preparar os dados. Verifique sua conexão e tente novamente. <small>{error}</small></p>}
      <button className="career-start-action" type="button" disabled={pending} onClick={() => void prepare()}>{pending ? "Preparando jogo…" : "Baixar dados e começar"}<Download size={18} /></button>
      <div className="data-bootstrap-note"><Wifi size={15} /><span>Internet exigida somente nesta preparação inicial</span></div>
    </section>
  </main>;
}
