"use client";

import Link from "next/link";
import { useId, useState, type DragEvent } from "react";
import { ItemMensagem } from "@/componentes/filas/ItemMensagem";
import { carregarModelo } from "@/dados/carregar";
import { colunaDeTexto, lerCsv, linhasColadas } from "@/dados/csv";
import { useFonteDeDados } from "@/dados/FonteDeDados";
import { numero, pct } from "@/dados/formato";
import { montarPainel } from "@/dados/painelUsuario";
import { useMensagens } from "@/dados/useMensagens";
import { preverEmLotes } from "@/modelo/prever";
import estilos from "./triar.module.css";

const LIMITE = 20000;

const EXEMPLO = [
  "Comprei há 20 dias e até agora nada, o rastreio parou",
  "Pedi duas cadeiras e só veio uma na caixa",
  "A tela chegou trincada e não liga",
  "Fui cobrado duas vezes no cartão e ninguém resolve",
  "Produto ótimo, chegou antes do prazo",
].join("\n");

type Csv = { nome: string; colunas: string[]; linhas: Record<string, string>[]; coluna: string | null };

export function Triar() {
  const { estado, acoes } = useFonteDeDados();
  const { mensagens, mover } = useMensagens();
  const [colado, setColado] = useState("");
  const [csv, setCsv] = useState<Csv | null>(null);
  const [progresso, setProgresso] = useState<{ feitos: number; total: number } | null>(null);
  const [erro, setErro] = useState("");
  const [arrastando, setArrastando] = useState(false);
  const ids = { texto: useId(), arquivo: useId(), coluna: useId() };

  const textos = csv ? (csv.coluna ? csv.linhas.map((l) => (l[csv.coluna!] ?? "").trim()).filter(Boolean) : []) : linhasColadas(colado);
  const ocupado = progresso !== null && progresso.feitos < progresso.total;

  async function abrirArquivo(arquivo: File | undefined) {
    setErro("");
    if (!arquivo) return;
    try {
      const { colunas, linhas } = lerCsv(await arquivo.text());
      if (!linhas.length) throw new Error("O arquivo não tem linhas depois do cabeçalho.");
      setCsv({ nome: arquivo.name, colunas, linhas, coluna: colunaDeTexto(colunas) });
    } catch (e) {
      setCsv(null);
      setErro(e instanceof Error ? e.message : "Não consegui ler esse arquivo como CSV.");
    }
  }

  async function triar() {
    setErro("");
    const lote = textos.slice(0, LIMITE);
    setProgresso({ feitos: 0, total: lote.length });
    try {
      const modelo = await carregarModelo();
      const predicoes = await preverEmLotes(modelo, lote, (feitos) => setProgresso({ feitos, total: lote.length }));
      acoes.usarDadosDoUsuario(montarPainel(lote, predicoes, modelo.regras, estado.olist ?? { regras_top: {} }));
    } catch (e) {
      setProgresso(null);
      setErro(e instanceof Error ? e.message : "Algo deu errado ao triar.");
    }
  }

  function soltar(e: DragEvent) {
    e.preventDefault();
    setArrastando(false);
    void abrirArquivo(e.dataTransfer.files[0]);
  }

  const resultado = estado.fonte === "usuario" && estado.painel && mensagens;

  return (
    <div className={estilos.triar}>
      <form
        className={estilos.form}
        onSubmit={(e) => {
          e.preventDefault();
          void triar();
        }}
      >
        {csv ? (
          <div className={estilos.arquivo}>
            <p>
              <strong>{csv.nome}</strong>{" "}
              <span className="apoio">· {numero.format(csv.linhas.length)} linhas</span>
            </p>
            <label htmlFor={ids.coluna} className={estilos.rotulo}>
              Coluna com o texto da reclamação
            </label>
            <select
              id={ids.coluna}
              name="coluna"
              value={csv.coluna ?? ""}
              onChange={(e) => setCsv({ ...csv, coluna: e.target.value || null })}
              className={estilos.select}
            >
              <option value="">Escolha a coluna</option>
              {csv.colunas.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <button type="button" className={estilos.secundario} onClick={() => setCsv(null)}>
              Trocar por texto colado
            </button>
          </div>
        ) : (
          <>
            <div className={estilos.linhaRotulo}>
              <label htmlFor={ids.texto} className={estilos.rotulo}>
                Reclamações, uma por linha
              </label>
              <button type="button" className={estilos.link} onClick={() => setColado(EXEMPLO)}>
                Usar um exemplo
              </button>
            </div>
            <textarea
              id={ids.texto}
              name="reclamacoes"
              value={colado}
              onChange={(e) => setColado(e.target.value)}
              rows={7}
              className={estilos.texto}
              placeholder={"Comprei e não chegou até hoje\nVeio a cor errada"}
              spellCheck={false}
            />
            <div
              className={estilos.soltar}
              data-ativo={arrastando || undefined}
              onDragOver={(e) => {
                e.preventDefault();
                setArrastando(true);
              }}
              onDragLeave={() => setArrastando(false)}
              onDrop={soltar}
            >
              <label htmlFor={ids.arquivo}>
                Ou <span className={estilos.sublinhado}>escolha um CSV</span> ou solte o arquivo aqui
              </label>
              <input
                id={ids.arquivo}
                name="arquivo"
                type="file"
                accept=".csv,.txt,text/csv"
                className={estilos.oculto}
                onChange={(e) => void abrirArquivo(e.target.files?.[0])}
              />
            </div>
          </>
        )}

        {textos.length > LIMITE ? (
          <p className="apoio">
            Vou triar as primeiras {numero.format(LIMITE)} de {numero.format(textos.length)}.
          </p>
        ) : null}
        {erro ? (
          <p role="alert" className={estilos.erro}>
            {erro}
          </p>
        ) : null}

        <button type="submit" className={estilos.primario} disabled={!textos.length || ocupado}>
          {ocupado
            ? "Triando…"
            : textos.length
              ? `Triar ${numero.format(Math.min(textos.length, LIMITE))} ${textos.length === 1 ? "reclamação" : "reclamações"}`
              : "Triar"}
        </button>
        {progresso ? (
          <progress
            className={estilos.progresso}
            value={progresso.feitos}
            max={progresso.total}
            aria-label="Progresso da triagem"
          />
        ) : null}
      </form>

      <section aria-live="polite" className={estilos.resultado}>
        {resultado ? (
          <>
            <h2 className={estilos.titulo}>
              {numero.format(estado.painel!.total)} triadas,{" "}
              {pct.format(estado.painel!.total ? estado.painel!.sem_humano / estado.painel!.total : 0)} sem precisar de
              ninguém.
            </h2>
            <p className="apoio">
              O painel, as filas e a revisão agora mostram as suas reclamações.{" "}
              <Link href="/">Ver no painel</Link> · <Link href="/filas">Ver as filas</Link> ·{" "}
              <button type="button" className={estilos.link} onClick={acoes.voltarParaOlist}>
                voltar para a base da Olist
              </button>
            </p>
            <ol className={estilos.lista}>
              {mensagens.slice(0, 5).map((m) => (
                <li key={m.id}>
                  <ItemMensagem m={m} onMover={mover} />
                </li>
              ))}
            </ol>
            {mensagens.length > 5 ? (
              <Link href="/filas" className="apoio">
                e mais {numero.format(mensagens.length - 5)} nas filas
              </Link>
            ) : null}
          </>
        ) : (
          <p className="apoio">
            O resultado aparece aqui, com a fila de cada reclamação, a certeza e as palavras que mais pesaram.
          </p>
        )}
      </section>
    </div>
  );
}
