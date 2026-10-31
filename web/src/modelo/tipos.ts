export type Bloco = {
  vocab: Record<string, number>;
  idf: number[];
  ngram: [number, number];
};

export type RegraExportada = { nome: string; padrao: string };

/** O modelo exportado por `python -m triagem.exportar_web`. */
export type Modelo = {
  classes: string[];
  palavras: Bloco;
  caracteres: Bloco;
  regras: RegraExportada[];
  coef: number[][];
  intercepto: number[];
  limiar: number;
};

export type Motivo = "" | "certeza baixa" | "texto sem conteúdo";

export type Predicao = {
  categoria: string;
  probas: Record<string, number>;
  certeza: number;
  revisao: boolean;
  motivo: Motivo;
  palavras: string[];
};
