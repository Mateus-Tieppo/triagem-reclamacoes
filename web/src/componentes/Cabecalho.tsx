"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useFonteDeDados } from "@/dados/FonteDeDados";
import estilos from "./Cabecalho.module.css";

const SECOES = [
  { href: "/", rotulo: "Painel" },
  { href: "/filas", rotulo: "Filas" },
  { href: "/revisao", rotulo: "Revisão" },
  { href: "/triar", rotulo: "Triar as minhas", curto: "Triar" },
  { href: "/sobre", rotulo: "Sobre" },
];

const numero = new Intl.NumberFormat("pt-BR");

export function Cabecalho() {
  const caminho = usePathname();
  const { estado, acoes } = useFonteDeDados();

  return (
    <header className={estilos.cabecalho}>
      <div className={estilos.topo}>
        <Link href="/" className={estilos.marca} aria-label="TriIA, página inicial" translate="no">
          Tri<span className={estilos.ia}>IA</span>
        </Link>
        <p className={`${estilos.fonte} codigo`} aria-live="polite">
          {estado.fonte === "usuario" ? (
            <>
              Seus dados · {numero.format(estado.painel?.total ?? 0)}{" "}
              <button type="button" className={estilos.voltar} onClick={acoes.voltarParaOlist}>
                voltar para a Olist
              </button>
            </>
          ) : (
            <>Base Olist{estado.painel ? ` · ${numero.format(estado.painel.total)}` : ""}</>
          )}
        </p>
      </div>
      <nav aria-label="Seções" className={estilos.nav}>
        <ul>
          {SECOES.map((s) => {
            const ativo = s.href === "/" ? caminho === "/" : caminho.startsWith(s.href);
            return (
              <li key={s.href}>
                <Link
                  href={s.href}
                  aria-current={ativo ? "page" : undefined}
                  aria-label={s.curto ? s.rotulo : undefined}
                  className={estilos.link}
                >
                  {s.curto ? (
                    <>
                      <span className={estilos.longo}>{s.rotulo}</span>
                      <span className={estilos.curto} aria-hidden>
                        {s.curto}
                      </span>
                    </>
                  ) : (
                    s.rotulo
                  )}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </header>
  );
}
