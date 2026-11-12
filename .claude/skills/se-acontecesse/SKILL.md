---
name: se-acontecesse
description: Fluxo diário do canal "Se Acontecesse" (vídeos "E se…?" em 3D low-poly, 80–110 s, sem narração, dados reais com fonte). Duas etapas em tarefas agendadas separadas: A PAUTA (véspera) e B PRODUÇÃO (noite). Use quando a tarefa agendada ou o Felipe pedir pauta ou episódio do canal.
---

# Se Acontecesse

Um episódio por dia, estilo Simplysimulated: cenas 3D low-poly, relógio da simulação ("+1 HORA", "+3 DIAS"), número grande no topo, frase curta em itálico embaixo, trilha e efeitos. Sem narração. Publica no TikTok e no Instagram (@eseacontecessse) pelo vidIQ na etapa de publicação da manhã (skill `publicacao`). Ninguém acompanha: decida pelas regras, registre e siga. Fale em português do Brasil.

## Caminhos
- `RAIZ` = `G:\Meu Drive\Área de Trabalho\Videos-Claude\E-Se-Fosse-Real` no PC do Felipe (`device_stage_files` para trazer, `device_commit_files` para gravar; o processamento roda no container).
- `RAIZ\_kit\` = motor three.js: `sim.html`, `kit\*.js`, `hud.css`, `render_sim.js`, `still.js`, `serve.js`, `audio_mix.py`, `convert.html/js`, `package.json`.
- `RAIZ\Base\` = `Personagens\*.glb` (20 Mixamo), `Animacoes\*.fbx` (32), `Sons\*.mp3` (Mixkit) + `CREDITOS.txt`.
- `RAIZ\_processo\` = `temas.csv`, `historico.csv`, `pautas\AAAA-MM-DD\`.
- `RAIZ\Episodios\NNN_slug\` = saída (`mkep.py`, `episodio.json`, `som.json`, vídeo, `capa.jpg`, `post.md`).
- Arquivo > 28 MB: `SendUserFile` e `device_commit_files` com o `fileUuid`.

## Portão
`estado.json` = `{"pauta": proposta|em_ajuste|aprovada, "producao": pendente|em_andamento|produzida|falhou}`. PRODUÇÃO só com `pauta` = `aprovada`. `em_ajuste` na execução das 22:41: encerre o turno; a execução das 23:41 produz a última versão gravada. Se `producao` já for `produzida`, termine em uma linha. Sem pauta nenhuma: escreva a pauta você mesmo (etapa A, sem esperar resposta) e produza.

## A. PAUTA (véspera, 18:23)
1. Tema pela skill `tendencias` (agente `pesquisador` grava `tendencias.json`). Reserva: `temas.csv` girando categorias (Terra e clima, espaço, física, corpo e vida, sociedade), nunca a mesma dois dias seguidos. Pedido do Felipe, se houver, vem antes.
2. Pesquise CADA número na web com fonte confiável (agente `pesquisador`). Sem fonte, o número não entra. Grave `fontes.md` com links e contas.
3. Roteiro pelas regras de `reference/roteiro.md`.
4. Grave `pauta.json`, `roteiro.md`, `fontes.md`, `tendencias.json`, `estado.json` (`pauta: aprovada`, `producao: pendente`) em `_processo\pautas\<amanhã>\`. A pauta não depende de aprovação.
5. Avise o Felipe (tema, gancho, 3 números principais, origem do tema) e encerre o turno. Só se ele responder antes da PRODUÇÃO: `estado.pauta: em_ajuste` antes de mexer → ajustes → `aprovada` → confirme em uma linha.

## B. PRODUÇÃO (noite, 22:41 e 23:41)
1. Portão. Traga `_kit`, `Base` e a pauta; `npm install` (não rode `playwright install`).
2. Cenários novos só se o tema pedir, em `kit/sets_<slug>.js`, longe da origem e visíveis só perto da câmera, sem quebrar o episódio 001.
3. `mkep.py` → `episodio.json`. Stills de todas as cenas (`node still.js "[...]" c1 "?s=0.6"`) + folha de contato. Conferência (agente `conferente`): câmera dentro de objeto, neblina cinza, assunto fora do quadro, texto em cima do assunto. Máx. 4 rodadas.
4. Render em 2 partes paralelas com `nohup` (`render_sim.js ini fim parts/pN "?s=0.6"`), checando os logs; concat. Refazer trecho = render só do trecho + cortes com `-ss/-frames:v` + concat demuxer (nunca vários `trim` no mesmo filtro).
5. Som: `som.json` + `audio_mix.py` (−14 LUFS). Sons novos do Mixkit pelo navegador embutido (caem em Downloads).
6. Final: crf 20, AAC 192k, **menor que 95 MB** (o Instagram recusa acima de 100 MB; ajuste `maxrate`). `capa.jpg`. `post.md` com `## Legenda (TikTok)` e `## Legenda (Instagram)` (igual ou um pouco mais longa), hashtags `#seacontecesse` + do tema, textos de capa, comentário fixado, fontes em comentários de até 150 caracteres, respostas prontas. Sem aviso de conteúdo de IA.
7. Entregue em `Episodios\NNN_slug\`; grave mudanças do `_kit` e sons novos; atualize `historico.csv` e `temas.csv`; `estado.producao: produzida`. Mensagem final curta: título, duração, arquivo, legenda pronta, hashtags, avisos; vídeo e capa por `SendUserFile`.
