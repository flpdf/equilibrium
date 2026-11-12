---
name: se-acontecesse-video
description: Fluxo diário do canal "Se Acontecesse" (vídeos "E se…?" em 3D low-poly, 80–110 s, sem narração, com dados reais): PAUTA da véspera para o Felipe aprovar e PRODUÇÃO à noite de 1 episódio no Drive. Use nas execuções agendadas ou quando ele pedir pauta, roteiro ou episódio do canal.
---

# Se Acontecesse: 1 episódio "E se…?" por dia

Canal de simulações "E se…?" no estilo Simplysimulated: cenas 3D low-poly bonitas, relógio da simulação ("+1 HORA", "+3 DIAS"), um número grande no topo, uma frase curta em itálico embaixo, trilha e efeitos. **Sem narração.** Temas gerais: Terra e clima, espaço, física, corpo e vida, sociedade (ex.: o elétron sumir por 10 s, o Sol sumir, os oceanos secarem por 1 h, as mulheres pararem de gestar para sempre). Publica no TikTok e no Instagram, sempre com legenda completa e hashtags.

Esta versão no Drive (`_processo\SKILL.md`) é a que manda. Se houver uma skill "se-acontecesse-video" com texto diferente, vale a do Drive.

## Caminhos (computador do Felipe, Windows)
- `RAIZ` = `G:\Meu Drive\Área de Trabalho\E-Se-Fosse-Real` (o nome da pasta ficou do nome provisório; o canal é "Se Acontecesse")
  - `_kit\` → motor three.js: `sim.html`, `kit\*.js` (engine, city, weather, sets, people), `kit\hud.css`, `render_sim.js`, `still.js`, `serve.js`, `audio_mix.py`, `convert.html`/`convert.js`, `package.json`
  - `Base\Personagens\*.glb` (20 Mixamo), `Base\Animacoes\*.fbx` (32), `Base\Sons\*.mp3` (Mixkit) + `Base\CREDITOS.txt`
  - `Episodios\NNN_slug\` → `mkep.py`, `episodio.json`, `som.json`, `efrNNN_slug.mp4`, `capa.jpg`, `post.md`
  - `_processo\` → este arquivo, `temas.csv`, `historico.csv`, `pautas\AAAA-MM-DD\` (`pauta.json`, `roteiro.md`, `fontes.md`, `estado.json`)
- `DL` = `C:\Users\amori\Downloads` (onde o navegador do app salva downloads)
- O terminal do computador (device_bash) NÃO enxerga a pasta G:. Use `device_list_dir`, `device_stage_files` (até 50 arquivos e 500 MB por chamada) e `device_commit_files`. Todo o trabalho pesado roda no container.
- `device_commit_files` com `stagedPath` falha (HTTP 400) para arquivos acima de ~28 MB. Para o vídeo final: `SendUserFile` primeiro (status `proactive`) e depois `device_commit_files` com o `fileUuid`.

## Portões entre etapas (`estado.json` da pauta)
`{"pauta":"proposta|em_ajuste|aprovada","producao":"pendente|em_andamento|produzida|falhou"}`
- A produção só começa com `pauta` = `proposta` ou `aprovada`. Com `em_ajuste`, espere (send_later 15 min) até 23:30; depois disso produza a última versão gravada e avise.
- Sem pauta para amanhã até a hora da produção: escreva você mesmo a pauta (etapa A sem esperar resposta) e produza.

---

## A. PAUTA (véspera, ~18:23) — para o episódio de AMANHÃ

1. `device_stage_files` de `_processo\temas.csv`, `_processo\historico.csv` e deste SKILL.md.
2. **Escolha do tema**: o próximo `livre` em `temas.csv`, girando as categorias (nunca a mesma categoria 2 dias seguidos; olhe as últimas no `historico.csv`). Se o Felipe pediu um tema na conversa ou nos comentários, ele vem antes. Sem tema bom, crie um novo e acrescente ao `temas.csv`.
   - Bons temas têm: uma pergunta absurda e fácil de entender em 1 linha; uma escalada clara no tempo; pelo menos 6 números reais e checáveis; cenas que o motor consegue mostrar bem (cidade, céu, água, morro, espaço, planeta, multidão).
   - Temas sensíveis (ex.: mulheres pararem de gestar): trate como demografia e consequência social, com respeito, sem gore, sem culpar ninguém, sem imagem de criança em perigo.
3. **Pesquisa (obrigatória)**: WebSearch para cada número. Use fonte primária ou de referência (IBGE, INMET, NASA, ONU, IPCC, artigos, Wikipédia só como ponte para a fonte). Cada número entra em `fontes.md` com link e a conta, quando houver. Se não achar fonte, o número não entra. Hipóteses físicas impossíveis (o elétron sumir) são permitidas; as consequências mostradas precisam seguir a física real e o que os especialistas dizem.
4. **Roteiro** (`roteiro.md` + `pauta.json`): 80–110 s em 17–22 cenas ("beats") de 3,5–6 s.
   - 0–4 s: GANCHO. Título-pergunta grande sobre uma vista aérea bonita. Nada de introdução lenta.
   - Até 10 s: o "normal" (rápido) e o evento começando.
   - Uma cena nova a cada 4–6 s; um número grande (`stat`) a cada ~10 s; o relógio sempre avançando (+1 s, +1 min, +1 hora… ou +1 dia, +1 mês, +1 ano).
   - Escalada: cada cena mais grave ou mais surpreendente que a anterior. Uma virada por volta de 70–80% ("e o pior ainda não chegou" ou um efeito inesperado).
   - Penúltima cena: consequência de longo prazo ("+1 ANO"). Última: CTA (pergunta para comentar e "qual o próximo e se?").
   - Por cena: tempo, relógio, cenário e câmera (aérea, rua, close, espaço), o que acontece, `stat` (número + linha curta), legenda em itálico (até 2 linhas de ~35 caracteres) e som principal.
   - Textos de tela em português do Brasil, números no formato brasileiro (1.154; 1,8×), sem palavrão, sem alarmismo falso.
5. Grave em `_processo\pautas\<amanhã>\`: `pauta.json` (`{"data","num","slug","titulo","categoria","duracao","beats":[...]}`, status "proposta"), `roteiro.md`, `fontes.md`, `estado.json` (`pauta:"proposta"`, `producao:"pendente"`). Commit com `device_commit_files`.
6. Mande ao Felipe com SendUserMessage, curto:
   🎬 Se Acontecesse — pauta de <data>
   **E se <título>?** (<categoria>, ~<duração> s)
   Gancho: <1 linha>
   Roteiro: 6–8 linhas no formato "+TEMPO · o que aparece · número"
   Fontes principais: 2–3 links
   Responda "ok", peça ajustes ou troque o tema.
   Encerre o turno esperando.
7. Se ele responder: marque `estado.pauta` = "em_ajuste" ANTES de mexer, aplique os ajustes (trocou o tema → refaça os passos 2–5), grave com status "aprovada" e confirme em uma linha. Sem resposta, não faça mais nada: a produção usa a pauta proposta.

---

## B. PRODUÇÃO (noite, ~22:41) — episódio de AMANHÃ

Ninguém está acompanhando: não faça perguntas; decida, registre e siga. Um problema numa cena não pode travar o episódio inteiro.

### B1. Montar a área de trabalho
1. Portão (ver acima). Marque `estado.producao` = "em_andamento".
2. `device_stage_files`: `_kit\*` (inclusive `kit\`), `Base\Personagens\*.glb` (20), `Base\Animacoes\*.fbx` (32), `Base\Sons\*.mp3` em 2–3 chamadas, mais a pasta da pauta. Copie para `run/` no scratchpad:
   `run/` = `_kit/*`; `run/assets/mixamo/glb/` = Personagens; `run/assets/mixamo/anims/` = Animações; `run/assets/audio/` = Sons.
3. `cd run && npm install --no-audit --no-fund` (three 0.160.0, @fontsource/newsreader, @fontsource/inter). O Chromium e o Playwright já vêm instalados: NÃO rode `playwright install`.

### B2. Cenários novos (quando o tema pedir)
- O kit já tem: cidade de SP procedural (prédios com janelas, avenida, árvores cúbicas, postes, fiação, carros), céu (sol, nuvens, tempestade, noite), chuva, enchente com reflexo, raio, morro com casas e deslizamento, marginal/rio, represa, mercado, personagens e multidões.
- Para tema novo, crie um módulo `kit/sets_<slug>.js` (ex.: planeta e órbita, Sol, oceano esvaziando, laboratório, hospital, estádio) longe da origem (±4000–9000 m), registre no `engine.js` com a mesma regra de "só visível perto da câmera" e, se precisar, novos parâmetros em `setEnv`/`fx` no `sim.html`. **Não quebre o que existe**: o episódio 001 tem que continuar renderizando igual.
- Estética: low-poly limpo, cores suaves, luz de sol definida com sombra, céu com gradiente, materiais foscos, nada de textura realista. Espaço: fundo preto com estrelas, planetas com atmosfera em degradê.

### B3. Episódio
1. `Episodios/NNN_slug/mkep.py` gera `episodio.json` (ver formato abaixo). Copie o do episódio 001 como molde.
2. **Stills antes de renderizar**: `node still.js "[t1,t2,...]" c1 "?s=0.6"` com 1 instante por cena (meio da cena) e o primeiro quadro do gancho. Monte uma folha de contato (PIL, 270×480 cada) e OLHE. Reprove e corrija:
   - câmera dentro de prédio, morro ou árvore; objeto tapando tudo em primeiro plano;
   - neblina demais (cena "cinza"): ajuste `fogNear`/`fogFar` por cena;
   - assunto da cena fora do quadro ou pequeno demais; horizonte torto sem motivo;
   - texto em cima do assunto ou estourando a largura; números errados;
   - cenas repetidas em sequência (mesmo enquadramento).
   No máximo 4 rodadas; cena que não fica boa é trocada por outra mais simples.
3. **Render** (2 CPUs; ~1h20 para 100 s): 2 partes em paralelo com `nohup`, e cheque o log a cada poucos minutos (cada comando tem limite de 10 min):
   `nohup node render_sim.js 0 50 parts/p1 "?s=0.6" > parts/p1.log 2>&1 &` e `nohup node render_sim.js 50 <dur> parts/p2 "?s=0.6" > parts/p2.log 2>&1 &`
   Junte com o concat do ffmpeg (`-c copy`). Para refazer uma cena: renderize só o trecho (início e fim em múltiplos de 1/30 s), corte as partes boas com `-ss <t> -frames:v <n>` (reencode crf 17) e junte com concat demuxer. Nunca use `trim` com várias saídas no mesmo filtro (estoura a memória).
4. **Som**: `som.json` (trilhas, leitos e efeitos) + `python3 audio_mix.py episodio.json som.json som.wav` (já normaliza para −14 LUFS). Regras: trilha cinematográfica do início ao fim (troca de faixa na virada, com crossfade); um efeito em cada corte importante (whoosh, impacto); leito ambiente que acompanha a cena; impacto forte no gancho (~3–4 s) e no CTA.
   - Precisa de som novo (espaço, oceano, alarme, coração…): baixe do Mixkit (licença gratuita) pelo navegador embutido do app: abra a página do efeito/música, pegue a URL da prévia (`assets.mixkit.co/active_storage/sfx/<id>/<id>-preview.mp3` ou `assets.mixkit.co/music/<id>/<id>.mp3`) e baixe com um `<a download>`; o arquivo cai em `DL` (às vezes como `.tmp`; identifique pelo tamanho). Traga com `device_stage_files`, salve em `assets/audio/` com nome curto e grave depois em `Base\Sons\` + uma linha em `Base\CREDITOS.txt`.
5. **Final**: `ffmpeg -i video.mp4 -i som.wav -map 0:v -map 1:a -c:v libx264 -preset veryfast -crf 20 -maxrate 9M -bufsize 18M -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart -shortest efrNNN_slug.mp4` (alvo: < 95 MB, serve para TikTok e Instagram — Instagram recusa > 100 MB; se passar, baixe o -crf/-maxrate e refaça).
6. **Conferência final**: duração 80–110 s; `ffprobe` com áudio; folha de contato `fps=1/5,scale=216:-1,tile=7x3` e OLHE; ouça o pico do áudio (sem estouro).
7. **Capa** `capa.jpg` (1080×1920) — OBRIGATÓRIA em todo episódio; é entregável junto com o vídeo (o Felipe põe a capa manualmente no TikTok/Instagram). Mantenha sempre a mesma estética:
   - Fundo: quadro limpo e forte do vídeo (de preferência o gancho/aérea do início, com o título já na tela), **sem HUD, relógio ou painéis** por cima. Se o quadro não tiver título, escreva a pergunta "E se…?" no topo: Newsreader 600 branca com sombra suave, palavra-chave em itálico azul claro (RGB 172,200,240), rótulo pequeno em caixa alta espaçada "E SE FOSSE REAL" acima.
   - Faixa escura suave em degradê no centro (sem caixa dura) para dar leitura.
   - Centro: o número mais chocante do episódio em Newsreader 700 ~170 px azul claro (ex.: "165 mm"); embaixo uma linha em caixa alta espaçada (sans bold ~27 px, branca) explicando o número; embaixo uma frase curta em Newsreader itálico ~52 px branca (pergunta que dá vontade de ver).
   - Todo o texto na área central segura (entre y≈300 e y≈1100, margens laterais ≥ 80 px) para não cortar no grid 4:5/1:1 do Instagram nem sob os botões do TikTok.
   - Sombra: alfa do texto com GaussianBlur(8) a ~85%. JPG qualidade 93. Fontes Newsreader em `_kit` (ou @fontsource/newsreader convertido para TTF).
   - Abra a imagem e confira antes de entregar (nada cortado, nada sobreposto).

### B4. Entregar e registrar
1. `post.md` no formato do episódio 001: 3 legendas (pergunta / números / curta), hashtags (principais: `#seacontecesse` + 4–5 do tema; extras para variar), 3 textos de capa, comentário fixado, fontes em comentários de até 150 caracteres, 3 respostas prontas, links das fontes e contas. O mesmo texto vale para TikTok e Instagram. Não marque nem peça para marcar como conteúdo gerado por IA.
2. Grave em `Episodios\NNN_slug\`: vídeo (via `fileUuid`), `capa.jpg`, `post.md`, `mkep.py`, `episodio.json`, `som.json`.
3. Se mexeu no motor: grave os arquivos alterados/novos de `_kit\` (e sons novos em `Base\Sons\`).
4. `historico.csv`: acrescente `data;num;slug;titulo;categoria;duracao_s;arquivo;musicas;observacoes`; em `temas.csv`, status do tema = `usado`. Grave os dois com `expectedMtimeMs`.
5. `estado.producao` = "produzida".
6. Mensagem final curta (SendUserMessage): título, duração, link/nome do arquivo, a legenda recomendada pronta para colar, hashtags, e avisos (cenas trocadas, números que saíram). Mande também o vídeo e a capa (`capa.jpg`) com SendUserFile — a capa sempre vai junto, com o lembrete: "capa pronta para você colocar ao postar".

---

## Formato do `episodio.json`
`{"dur":100,"timerLabel":"SEM PARAR DE CHOVER","gaugeMax":1154,"gaugeRec":151.8,"beats":[...]}`
Cada beat (`beat(t0,t1,cam,env,**k)` no mkep.py):
- `t`: [início, fim] em s. `cam`: [pos, alvo, fov, pos2, alvo2, fov2] (interpola do 1º para o 2º; câmera na mão leve, `fx.hand` 0 = parada).
- `env` (e `env2` para interpolar até o fim da cena): storm, rain, wet, night, lit, black, blackR, blackC, waterY, water ("city"|"river"|"dam"), flash, fogNear, fogFar, exposure, sat, envI, refl, lamps, carLights, clearWater.
- `title` (gancho, HTML com `<em>`), `timer` ("+1 HORA"), `gauge` [de, até], `stat` ({"v":165,"dec":0,"suf":" mm","s":"linha"} conta de 0 até v; ou {"n":"1,8×","s":"linha","size":118} fixo), `cap` (itálico, `<br>` para quebrar), `people` (lista de {char, anim, pos, rot, walk, ofs} ou {"crowd":{n, xs, z0, z1, walks, speed, stand, idles, chars}}).
- `fx`: overlay ("phone"|"board"|"ruler"|"cta"), blur, dim, flash [tempos], flashK, flashScreen, bolt, cloud, shake, shakeAt, slide, slideAt, tree, lampsOffAt, blackAfter, traffic, stall, float, fill, ruler, shadow, sun, camEase. `fadeIn`/`fadeOut` na cena.
- Cidade: quarteirões de 80 m, ruas de 20 m, avenida de 34 m em x=0 (meio-fio em |x|≈13), árvores em x=±18,6. Câmera de rua: x=−13,6, y=1,7, olhando para x≈−10,5. Cenários fora da cidade: morro (4000,0,0), rio (−4000,0,0), represa (0,0,6000; barragem em z=6185), mercado (0,0,−6000).

## Desempenho (2 CPUs, sem GPU)
- Sempre `?s=0.6` (render a 60% e a tela de textos em resolução cheia). Bloom só à noite (night > 0,25). GTAO desligado. Cenários só visíveis perto da câmera. Carregamento ~3,5 s; quadro 0,7–3 s.
- Personagens em GLB (leves). Para um personagem Mixamo novo: baixe o FBX, converta com `convert.html` (`node convert.js`) e grave o `.glb` em `Base\Personagens\`.

## Se algo quebrar
- `PAGE ERROR` no still: quase sempre JSON inválido, campo com nome errado ou erro no módulo novo.
- Servidor local caindo: use o `serve.js` (os scripts de still e render já sobem o próprio servidor).
- Render parou no meio: renderize só o trecho que falta e junte.
- Computador offline (stage/commit falhando): termine o que der no container, mande o vídeo ao Felipe por SendUserFile e diga o que faltou gravar no Drive.
