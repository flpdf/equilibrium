# Natação no template do Chefão (cenário de piscina)

Ativa com `"ambiente": "piscina"` no `episode.json`. Sem essa chave o template funciona exatamente como antes (academia).

## O que o motor faz
- **Piscina**: água em y=0, fundo de azulejo a 3 m (`swim.poolDepth`), faixa preta no fundo, paredes laterais, raias de boias.
- **Água**: superfície animada (ondas, reflexo, brilho do sol), visão de baixo com "janela de Snell" e espelho, tinta azul e absorção para tudo que está embaixo d'água, cáusticas (rede de luz) no fundo e no corpo.
- **Física visual**: a piscina corre para trás na velocidade do nado (com "surto" por braçada); bolhas da expiração pela boca (somem durante a respiração), bolhas de ar preso na mão após a entrada, respingos e anel na superfície quando mão/pé entra na água, gotas pingando da mão na recuperação, espuma onde o corpo cruza a superfície, esteira em V atrás da cabeça. Tudo é calculado em função do tempo (o render em 5 partes paralelas continua funcionando).
- **O erro custa velocidade**: no boneco vermelho a piscina anda mais devagar (`drag`, padrão 0,82).
- **Nadando o tempo todo**: em piscina o boneco não para no "fundo da repetição"; nada contínuo do 0 ao 33 s.

## Nados (`"swim": {"stroke": ...}`)
| stroke | como é feito | `anim` |
|---|---|---|
| `crawl` | procedural (braçada, rolagem, respiração lateral, pernada de 6 tempos) | qualquer FBX Mixamo (use `Swimming.fbx`) |
| `costas` | procedural (de barriga pra cima, braço reto por cima, puxada lateral) | `Swimming.fbx` |
| `borboleta` | procedural (braços juntos, ondulação, pernada golfinho, respiração frontal) | `Swimming.fbx` |
| `peito` | animação Mixamo, acelerada (`rate` 2,4) e posicionada na superfície | `Swimming.fbx` |
| `flutuacao` | animação Mixamo (pernada de sustentação), cabeça fora d'água | `Treading Water.fbx` |

`Swimming Breaststroke.fbx` não serve: no fim do ciclo o boneco fica em pé.

## Parâmetros do nado procedural (bom = padrão; o erro muda alguns)
`T` período da braçada (s) · `speed` cm/s · `depth` profundidade do quadril · `roll` rolagem (rad) · `elbow` cotovelo alto na puxada · `w` largura da entrada da mão (negativo = cruza a linha do corpo) · `kickAmp` / `kneeAmp` / `kickBias` pernada · `ankle` 1 = pé em ponta, 0 = pé "duro" · `headLift` cabeça levantada (crawl/borboleta) ou queixo no peito (costas) · `sink` quadril/pernas afundando · `breath` `right|left|bilateral|none` · `breathTurn` giro da cabeça · `breathLift` levantar a cabeça pra respirar · `exhale` 1 solta bolhas, 0 prende o ar · `und` ondulação (borboleta) · `drag` velocidade do boneco errado.

## Erros em piscina
Cada item de `errors` aceita `"swim": {…}` (parâmetros do boneco vermelho) além de `deform` (que continua valendo, inclusive no peito e na flutuação). Validados no still:
| erro | swim | vista |
|---|---|---|
| Cabeça alta (crawl) | `{"headLift":0.6,"sink":0.2}` | `side_under` zoom 0.75 ou `split` |
| Mão cruzando o corpo (crawl) | `{"w":-0.4}` | `top` |
| Pernada de joelho (crawl) | `{"kneeAmp":1.15,"kickAmp":0.12}` | `side_under` / `under_back_threequarter` zoom 0.75 |
Ponto de partida (conferir no still antes de usar): corpo plano `{"roll":0.05}` · puxada de braço reto `{"elbow":0}` · levanta a cabeça pra respirar `{"breathLift":0.6,"breathTurn":0.5}` · prende a respiração `{"exhale":0}` · pé duro `{"ankle":0.1}` · costas: queixo no peito `{"headLift":0.5}`, quadril sentado `{"sink":0.3,"kickBias":0.35}`, joelho saindo d'água `{"kneeAmp":1.1}` · borboleta: cabeça alta `{"breathLift":1.0}`, joelho dobrando demais `{"kneeAmp":1.2}`, corpo duro `{"und":0.02}` · peito (deform): cabeça alta `Neck x -0.45; Head x -0.3`.

## Vistas novas (além das antigas)
- Acima d'água: `top` (de cima, nadador subindo na tela — ótima para mão cruzando e largura da braçada).
- Embaixo d'água: `side_under`, `side_left_under`, `under_front`, `under_back`, `under_threequarter`, `under_back_threequarter`.
- Meio a meio (linha d'água no quadro): `split`, `split_left`, `split_front`, `split_threequarter`, `split_back`.
- Também dá para trocar a câmera das cenas fixas: `hookView`/`hookZoom`, `cardView`, `winView`/`winZoom`, `outView`/`outZoom`.
- Nadador deitado fica pequeno no vertical: use `zoom` 0.7–0.8 nas vistas laterais; `top` e `split_threequarter` deixam o boneco maior.

## Exemplo
`exemplos/natacao_crawl.episode.json` (crawl, 3 erros validados).
