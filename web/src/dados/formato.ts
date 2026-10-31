export const numero = new Intl.NumberFormat("pt-BR");
export const pct = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 0 });

const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];

/** "2017-03" vira "mar/17". */
export function mesCurto(mes: string): string {
  const [ano, m] = mes.split("-");
  return `${MESES[Number(m) - 1]}/${ano.slice(2)}`;
}
