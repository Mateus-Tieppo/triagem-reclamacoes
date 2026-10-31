# Design da TriIA

Direção escolhida pelo Mateus: **etiqueta de expedição**. A ferramenta parece a mesa de quem despacha pedidos: papel creme, tinta grafite, o amarelo das etiquetas de envio e códigos impressos. Cada reclamação é tratada como um volume que recebe uma etiqueta e segue para a fila certa.

## Ideia marcante

Cada fila tem um código de três letras, como os de bagagem e de centro de distribuição: ENT (entrega), FAL (item faltando), ERR (produto errado), DEF (defeito), EST (sem estoque), ATD (atendimento), COB (cobrança) e OUT (outro). O código aparece como etiqueta impressa ao lado de cada reclamação, nas barras e nas filas. O que precisa de gente recebe um carimbo de REVISÃO em vermelho tijolo.

## Modo

Operate: é uma ferramenta. Precisão e leitura rápida vêm antes de efeito. A personalidade mora nos detalhes: etiquetas, linha tracejada entre itens, números tabulares e o "IA" do nome em fundo amarelo.

## Cores

| Token | Claro | Escuro | Uso |
| --- | --- | --- | --- |
| `--papel` | #F4F1EA | #15140F | fundo da página |
| `--cartao` | #FBF9F4 | #1E1C16 | superfícies |
| `--tinta` | #1B1A17 | #EEE8DA | texto principal, barras |
| `--tinta-2` | #57534B | #A8A193 | texto de apoio |
| `--linha` | #CFC7B6 | #3A362C | divisórias |
| `--etiqueta` | #F2C230 | #F2C230 | destaque, sempre com texto `--tinta-etiqueta` (#1B1A17) |
| `--carimbo` | #B23A1E | #F08A6C | revisão humana |
| `--ok` | #2F6B3F | #7FBF8E | resolvido sem humano |

Todo par de texto e fundo passa AA (4,5:1). O amarelo nunca é cor de texto, só de fundo.

## Tipos

- **Archivo** (variável, eixos de peso e largura): títulos em largura condensada (85%), marca em largura expandida (115%), texto corrido em 100%.
- **IBM Plex Mono**: só para o que é código de verdade: códigos de fila, porcentagens, datas e identificadores. Nunca para texto corrido.
- Números sempre com `font-variant-numeric: tabular-nums`.
- Letras nunca mais apertadas que -0,03em.

## Forma

- Raio 4px em etiquetas, 12px em cartões.
- Borda de 1,5px em etiquetas (impressão), 1px nas demais.
- Divisória entre itens de lista: 1px tracejada.
- Sem sombras duras, sem gradiente em texto, sem emoji como ícone.

## Movimento

GSAP com `useGSAP`, só para dar sentido: barras crescendo uma vez ao abrir o painel e a etiqueta "carimbando" ao mover de fila. Com `prefers-reduced-motion`, nada se move.

## Navegação

Painel, Filas, Revisão, Triar as minhas e Sobre. No celular os rótulos encurtam ("Triar") e a barra fica no topo, rolando na horizontal se precisar. A fonte de dados ativa (base da Olist ou dados do usuário) aparece sempre no cabeçalho.
