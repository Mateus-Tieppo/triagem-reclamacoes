import type { Motivo } from "@/modelo/tipos";

export const CATEGORIAS = [
  "nao_recebido_atraso",
  "item_faltando",
  "produto_errado",
  "defeito_qualidade",
  "sem_estoque",
  "atendimento_loja",
  "cobranca_cancelamento",
  "outro",
] as const;

export type Categoria = (typeof CATEGORIAS)[number];

/** Nome da fila e código de três letras, como numa etiqueta de despacho. */
export const FILAS: Record<Categoria, { nome: string; codigo: string; time: string }> = {
  nao_recebido_atraso: { nome: "Problema de entrega", codigo: "ENT", time: "Logística" },
  item_faltando: { nome: "Item faltando", codigo: "FAL", time: "Expedição" },
  produto_errado: { nome: "Produto errado", codigo: "ERR", time: "Expedição" },
  defeito_qualidade: { nome: "Defeito ou qualidade", codigo: "DEF", time: "Qualidade" },
  sem_estoque: { nome: "Sem estoque", codigo: "EST", time: "Estoque" },
  atendimento_loja: { nome: "Atendimento da loja", codigo: "ATD", time: "Relacionamento" },
  cobranca_cancelamento: { nome: "Cobrança ou cancelamento", codigo: "COB", time: "Financeiro" },
  outro: { nome: "Outro", codigo: "OUT", time: "Triagem geral" },
};

export type MensagemTriada = {
  id: string;
  texto: string;
  categoria: Categoria;
  certeza: number;
  revisao: boolean;
  motivo: Motivo;
  palavras: string[];
  data: string | null;
};

export type RegraTop = { nome: string; rotulo_legivel: string; n: number };

export type Painel = {
  total: number;
  sem_humano: number;
  por_categoria: Record<Categoria, number>;
  por_mes: ({ mes: string } & Record<Categoria, number>)[];
  regras_top: Partial<Record<Categoria, RegraTop[]>>;
  mensagens: MensagemTriada[];
};
