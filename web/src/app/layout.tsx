import type { Metadata, Viewport } from "next";
import { Archivo, IBM_Plex_Mono } from "next/font/google";
import { Cabecalho } from "@/componentes/Cabecalho";
import { FonteDeDadosProvider } from "@/dados/FonteDeDados";
import "./globals.css";

const archivo = Archivo({
  variable: "--font-archivo",
  subsets: ["latin"],
  axes: ["wdth"],
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-plex-mono",
  subsets: ["latin"],
  weight: ["400", "600"],
  display: "swap",
});

const DESCRICAO =
  "Reclamações organizadas. Decisões inteligentes. Triagem de reclamações de e-commerce em português com machine learning clássico que roda no navegador, sem LLM e sem custo.";

export const metadata: Metadata = {
  metadataBase: new URL("https://triia-mateus.vercel.app"),
  title: "TriIA · Triagem inteligente de reclamações",
  description: DESCRICAO,
  openGraph: {
    title: "TriIA · Triagem inteligente de reclamações",
    description: DESCRICAO,
    url: "/",
    siteName: "TriIA",
    locale: "pt_BR",
    type: "website",
  },
  twitter: { card: "summary_large_image" },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#f4f1ea" },
    { media: "(prefers-color-scheme: dark)", color: "#15140f" },
  ],
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="pt-BR" className={`${archivo.variable} ${plexMono.variable}`}>
      <body>
        <a className="pular" href="#conteudo">
          Pular para o conteúdo
        </a>
        <FonteDeDadosProvider>
          <Cabecalho />
          <main id="conteudo" className="conteudo">
            {children}
          </main>
        </FonteDeDadosProvider>
      </body>
    </html>
  );
}
