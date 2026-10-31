# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
- **Primário:** recrutador ou avaliador de uma vaga de IA (trilha AI Builder) abrindo o link do portfólio do Mateus, muitas vezes pelo celular, com poucos minutos. Precisa entender em segundos o que a ferramenta faz, ver que resolve uma dor real e conseguir usar sem instrução.
- **Secundário:** o time de atendimento de uma loja online que recebe centenas de reclamações por dia e precisa mandar cada uma para o time certo (logística, estoque, financeiro, atendimento). Quando os dois públicos pedem coisas diferentes, o recrutador vem primeiro.

## Product Purpose
TriIA lê reclamações de clientes em português e diz para qual fila cada uma vai, com a certeza e o porquê. O que o modelo não tem certeza vai para revisão humana. Sucesso: o recrutador abre, vê o painel com 7.453 reclamações reais triadas, clica numa fila, testa com uma reclamação própria e sai convencido de que é um produto real, útil e feito com capricho.

## Positioning
Triagem com machine learning clássico que roda inteiro no navegador, de graça, em menos de 1 milissegundo por mensagem, e acerta tanto quanto um LLM de 7 bilhões de parâmetros (Qwen 2.5 7B) nas mensagens rotuladas pelo Mateus. Os rótulos vieram de um guia calibrado em três rodadas entre humano e IA.

## Operating Context
- Abre já carregada com as 7.453 reclamações da base pública da Olist que o modelo nunca viu no treino.
- O usuário pode colar mensagens ou subir um CSV; tudo é processado no navegador e nada sai dele.
- Correções (mover de fila) ficam no próprio navegador.
- Site estático publicado na Vercel; link no README e no perfil do GitHub do Mateus.

## Capabilities and Constraints
- 8 categorias: sem estoque, problema de entrega, item faltando, produto errado, defeito ou qualidade, atendimento da loja, cobrança ou cancelamento, outro.
- Cada triagem tem categoria, certeza e as palavras que mais pesaram. Abaixo de 0,80 de certeza, ou sem texto, vai para revisão.
- Sem LLM, sem backend, sem banco, sem custo. Supabase só numa possível v2.
- Tempo poupado é estimativa com premissa explícita e ajustável (padrão 30 s por mensagem), nunca medição.

## Brand Commitments
- Nome: **TriIA** (lê-se "tri-ia"); o "IA" pode vir destacado.
- Subtítulo: "Triagem inteligente de reclamações".
- Slogan: "Reclamações organizadas. Decisões inteligentes."
- Interface em português do Brasil. Textos sem travessões. Não citar programa de estágio nem empresa.

## Evidence on Hand
- `web/public/painel.json`: 7.453 reclamações nunca vistas com categoria, certeza, revisão, palavras e data.
- Resultados reais em `README.md`, `DECISOES.md` e `results/resultados.md`: acurácia 75,5% nas 53 rotuladas pelo Mateus (igual ao Qwen), F1 macro 50,7% (Qwen 56,0%), 82,3% de acurácia nas 300 do teste, menos de 1 ms por mensagem, 90,3% de acerto nas que o modelo decide sozinho, calibração de 33% para 75% de concordância.
- Não há clientes, depoimentos nem horas economizadas medidas; não inventar.

## Product Principles
1. Valor em segundos: o primeiro olhar já mostra o resultado, sem setup.
2. Honestidade visível: certeza, porquê e limitações aparecem, inclusive onde o Qwen é melhor.
3. Humano na dúvida: a revisão é parte do produto, não um defeito.
4. Grátis e privado: tudo no navegador.

## Accessibility & Inclusion
Contraste AA, foco visível, navegação por teclado, `prefers-reduced-motion`, funcional a 375 px de largura.
