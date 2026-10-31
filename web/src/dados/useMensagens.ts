"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { aplicarCorrecoes, lerCorrecoes, salvarCorrecao } from "./correcoes";
import { useFonteDeDados } from "./FonteDeDados";
import type { Categoria, MensagemTriada } from "./tipos";

/** Mensagens da fonte ativa já com as correções feitas por pessoas neste navegador. */
export function useMensagens(): {
  mensagens: MensagemTriada[] | null;
  erro: string | null;
  mover: (id: string, categoria: Categoria) => void;
} {
  const { estado } = useFonteDeDados();
  const [correcoes, setCorrecoes] = useState<Record<string, string>>({});

  useEffect(() => setCorrecoes(lerCorrecoes()), []);

  const mover = useCallback((id: string, categoria: Categoria) => {
    salvarCorrecao(id, categoria);
    setCorrecoes((c) => ({ ...c, [id]: categoria }));
  }, []);

  const mensagens = useMemo(
    () => (estado.painel ? aplicarCorrecoes(estado.painel.mensagens, correcoes) : null),
    [estado.painel, correcoes],
  );

  return { mensagens, erro: estado.erro, mover };
}
