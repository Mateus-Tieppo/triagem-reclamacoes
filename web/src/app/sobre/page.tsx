import { CabecalhoSecao } from "@/componentes/CabecalhoSecao";
import estilos from "./sobre.module.css";

const REPOSITORIO = "https://github.com/Mateus-Tieppo/triagem-reclamacoes";

const RESULTADOS = [
  { nome: "TriIA (ML clássico)", acc53: "75,5%", f153: "50,7%", acc300: "82,3%", latencia: "menos de 1 ms", destaque: true },
  { nome: "Qwen 2.5 7B (LLM local)", acc53: "75,5%", f153: "56,0%", acc300: "81,3%", latencia: "1.123 ms" },
  { nome: "Llama 3.2 3B (LLM local)", acc53: "58,5%", f153: "38,0%", acc300: "66,0%", latencia: "517 ms" },
];

export default function Sobre() {
  return (
    <>
      <CabecalhoSecao titulo="Sobre a TriIA">
        Um classificador de reclamações de e-commerce em português que roda inteiro no navegador, sem LLM e sem custo,
        e acerta tanto quanto um LLM de 7 bilhões de parâmetros na acurácia.
      </CabecalhoSecao>

      <section aria-labelledby="como" className={estilos.secao}>
        <h2 id="como">Como funciona</h2>
        <ol className={estilos.passos}>
          <li>
            <span className="codigo">01</span>
            <div>
              <h3>Um guia de rotulagem calibrado</h3>
              <p>
                Eu e o Claude rotulamos as mesmas mensagens às cegas, em três rodadas. A concordância subiu de 33% nas
                mensagens difíceis para 75%, o que é perto do teto realista: nem duas pessoas concordam sempre sobre
                qual é o problema principal.
              </p>
            </div>
          </li>
          <li>
            <span className="codigo">02</span>
            <div>
              <h3>Rotulagem uma vez só</h3>
              <p>
                O Claude rotulou 3.000 reclamações do treino seguindo o guia. Depois disso, nenhuma IA generativa é
                chamada: a triagem é só o modelo treinado.
              </p>
            </div>
          </li>
          <li>
            <span className="codigo">03</span>
            <div>
              <h3>Machine learning clássico no navegador</h3>
              <p>
                TF-IDF de palavras e de caracteres, mais 44 regras legíveis como &ldquo;não recebi&rdquo; e &ldquo;só
                veio um&rdquo;, numa regressão logística. O modelo foi exportado do Python e dá a mesma resposta em
                todas as mensagens testadas. Abaixo de 80% de certeza, a reclamação vai para uma pessoa.
              </p>
            </div>
          </li>
        </ol>
      </section>

      <section aria-labelledby="acerto" className={estilos.secao}>
        <h2 id="acerto">O quanto acerta</h2>
        <p className="apoio">
          Conjunto de teste de 300 reclamações, usado só na avaliação final. A régua principal são as 53 que eu rotulei à
          mão, porque o Claude rotulou o treino.
        </p>
        <div className={estilos.tabelaRolagem}>
          <table className={estilos.tabela}>
            <thead>
              <tr>
                <th scope="col">Abordagem</th>
                <th scope="col">Acurácia nas 53</th>
                <th scope="col">F1 macro nas 53</th>
                <th scope="col">Acurácia nas 300</th>
                <th scope="col">Tempo por mensagem</th>
              </tr>
            </thead>
            <tbody>
              {RESULTADOS.map((r) => (
                <tr key={r.nome} data-destaque={r.destaque || undefined}>
                  <th scope="row">{r.nome}</th>
                  <td>{r.acc53}</td>
                  <td>{r.f153}</td>
                  <td>{r.acc300}</td>
                  <td>{r.latencia}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <ul className={estilos.pontos}>
          <li>
            <strong>Na acurácia, empata com o Qwen</strong> e passa do Llama, rodando mais de mil vezes mais rápido.
          </li>
          <li>
            <strong>No F1 macro, o Qwen ainda ganha.</strong> Essa métrica dá o mesmo peso a cada categoria, e o Qwen vai
            melhor nas pequenas, como sem estoque e atendimento da loja.
          </li>
          <li>
            <strong>A revisão é pequena e confiável:</strong> no teste, o modelo decide sozinho 72% das mensagens e
            acerta 90,3% delas.
          </li>
          <li>
            <strong>O painel é honesto:</strong> mostra só as 7.453 reclamações que o modelo nunca viu no treino.
          </li>
        </ul>
      </section>

      <section aria-labelledby="dados" className={estilos.secao}>
        <h2 id="dados">Dados e código</h2>
        <p>
          Avaliações públicas do{" "}
          <a href="https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce">Brazilian E-Commerce Public Dataset by Olist</a>
          , de 2016 a 2018, sob a licença CC BY-NC-SA 4.0. O código, os testes e a análise completa estão no{" "}
          <a href={REPOSITORIO}>repositório no GitHub</a>.
        </p>
      </section>
    </>
  );
}
