"use client";

import { createContext, use, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { carregarPainel } from "./carregar";
import type { Painel } from "./tipos";

export type Fonte = "olist" | "usuario";

type FonteDeDados = {
  estado: { painel: Painel | null; fonte: Fonte; erro: string | null };
  acoes: { usarDadosDoUsuario: (painel: Painel) => void; voltarParaOlist: () => void };
};

const Contexto = createContext<FonteDeDados | null>(null);

/** Guarda os dados que as telas mostram: a base da Olist ou o que o usuário triou. */
export function FonteDeDadosProvider({ children }: { children: ReactNode }) {
  const [olist, setOlist] = useState<Painel | null>(null);
  const [usuario, setUsuario] = useState<Painel | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    carregarPainel().then(setOlist, (e: Error) => setErro(e.message));
  }, []);

  const usarDadosDoUsuario = useCallback((p: Painel) => setUsuario(p), []);
  const voltarParaOlist = useCallback(() => setUsuario(null), []);

  const valor = useMemo<FonteDeDados>(
    () => ({
      estado: { painel: usuario ?? olist, fonte: usuario ? "usuario" : "olist", erro },
      acoes: { usarDadosDoUsuario, voltarParaOlist },
    }),
    [olist, usuario, erro, usarDadosDoUsuario, voltarParaOlist],
  );

  return <Contexto value={valor}>{children}</Contexto>;
}

export function useFonteDeDados(): FonteDeDados {
  const v = use(Contexto);
  if (!v) throw new Error("useFonteDeDados precisa estar dentro de FonteDeDadosProvider.");
  return v;
}
