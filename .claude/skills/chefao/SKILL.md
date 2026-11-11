---
name: chefao
description: Fluxo diário do perfil "Chefão dos Treinos" (academia, boneco 3D Mixamo). Três etapas em tarefas agendadas separadas: A PAUTA (véspera), B ÁUDIO (véspera, noite), C PRODUÇÃO (madrugada). Use quando a tarefa agendada ou o Felipe pedir uma dessas etapas, uma pauta, um vídeo ou um carrossel do perfil.
---

# Chefão dos Treinos

Por dia: 3 vídeos (37 s, 1080×1920, narrados) e 3 carrosséis (5 imagens 1080×1920), todos do mesmo tema. Cada tarefa agendada diz qual etapa rodar; rode só a sua. Ninguém acompanha: não pergunte, decida pelas regras, registre e siga. Fale em português do Brasil.

## Caminhos
- `DRIVE` = `G:\Meu Drive\Área de Trabalho\Mixamo-Academia` no PC do Felipe. O terminal do PC não enxerga G:. Traga arquivos com `device_stage_files`, grave com `device_commit_files`, liste com `device_list_dir`. O processamento roda no container.
- `DRIVE\_processo\` = kit: `grade.json`, `catalogo.csv`, `historico.csv`, `exemplos\`, `template.html`, `carrossel.html`, `carrossel.js`, `stills.js`, `render.js`, `render_all.sh`, `audio_falas.py`, `mix_musica.py`, `musicas\`.
- `DRIVE\_processo\pautas\AAAA-MM-DD\` = a pauta do dia (formato em `reference/formato-pauta.md`).
- `DRIVE\Videos-Prontos\AAAA-MM-DD\` = saída.
- Scripts deste repositório: `scripts/validar_pauta.py`, `scripts/checar_audio.py`.
- Pré-checagem de toda etapa: `get_device_info`. PC offline: termine com "Computador offline às HH:MM. Etapa X do dia <data> não rodou." e nada mais.

## Portões
`estado.json` = `{"pauta": proposta|em_ajuste|aprovada|padrao, "audio": pendente|em_andamento|pronto|pronto_com_avisos|falhou, "producao": pendente|em_andamento|produzida}`. Cada etapa grava só o seu campo, depois de trazer a versão atual.
- ÁUDIO começa se a pauta existe com os 3 `narration.json` e `pauta` ≠ `em_ajuste`. A execução das 23:07 usa o motor principal; a das 00:07 não espera: vídeo ainda sem narração vai direto para a reserva.
- PRODUÇÃO de vídeos começa se `audio` ∈ {pronto, pronto_com_avisos}. Carrosséis não dependem de áudio. Prazo 05:15: depois, renderize sem narração o que não tiver `audio.json` e avise.
- Portão fechado: encerre o turno. A tarefa agendada roda de novo no próximo horário fixo e retoma de onde parou. Não use `send_later` na mesma sessão.

## A. PAUTA (véspera, 17:47)
1. Data alvo = amanhã. Traga `grade.json`, `catalogo.csv`, `historico.csv`, `exemplos\` e as pautas dos últimos 7 dias.
2. Tema do dia pela `grade.json` → `dias`. Vídeos: siga a `trilha` do tema. Manhã = o mais básico que não saiu em 7 dias; almoço = o seguinte; noite = o mais desafiador (avançado só à noite, foco em controle). Sem repetir exercício no dia. Grupo com menos de 3 livres: repita o menos recente com ângulo novo. 3 erros por vídeo inéditos para aquele exercício no `historico.csv`. Linhas "não usar" do catálogo ficam fora. Natação só quando o tema incluir `natacao` (`reference/natacao.md`).
3. Carrosséis: 3 tipos diferentes de `grade.json` → `carrosseis.tipos`, um deles de preferência "erros".
4. Escreva os arquivos com os formatos de `reference/formato-pauta.md`, respeitando `reference/regras-conteudo.md`. Deformações validadas em `reference/deforms.md`. Rode `python3 scripts/validar_pauta.py <pasta>`; corrija até 0 erros.
5. Grave em `DRIVE\_processo\pautas\<amanhã>\` com `pauta.json` `status: proposta` e `estado.json` `{"pauta":"proposta","audio":"pendente","producao":"pendente"}`.
6. Mande ao Felipe e encerre o turno:
   ```
   📋 Pauta de <dia>, <data> — <TEMA>
   🎬 07:00 · <exercício> — <erro1>, <erro2>, <erro3>
   🎬 12:30 · …   🎬 19:30 · …
   🖼️ 09:30 · <título> (<tipo>)   🖼️ 15:30 · …   🖼️ 21:30 · …
   Responda "ok" ou o que mudar. Sem resposta até as 23h, produzo assim.
   ```
7. Se ele responder: grave `estado.pauta: em_ajuste` ANTES de mexer; reescreva só os itens afetados; valide de novo; grave com `status: aprovada` e `estado.pauta: aprovada`; registre em `ajustes`; confirme em uma linha. Se o ÁUDIO já gerou a narração de um vídeo alterado, renomeie `vN\audio.json` para `audio_antigo.json`.

## B. ÁUDIO (véspera, 23:07 e 00:07)
Regra do Felipe (06/11): a narração tem que soar brasileira nativa. Nunca use voz desenhada do Voice Studio.
1. Portão. `pauta` = `proposta` → grave `padrao`. Grave `audio: em_andamento`. Traga `audio_falas.py`.
2. Para cada vídeo sem `audio.json`, gere as 10 falas separadas (`reference/narracao.md`: motor principal Voice Studio por fila, reserva ElevenLabs). Arquivos em `run/vN/falas/01..10.mp3`.
3. `python3 scripts/checar_audio.py run/vN/falas run/vN/narration.json --saida run/vN/falas/qa.json`. Refaça só as falas REFAZER (inclui arquivo ausente ou inválido), mesmos parâmetros, até 2 refações por fala. Depois disso, fique com a melhor e registre o aviso.
4. `python3 audio_falas.py montar run/vN/falas run/vN/narration.json run/vN/narracao_sync.wav`.
5. Grave em `pautas\<amanhã>\vN\`: `narracao_sync.wav`, `falas\`, `audio.json` = `{"motor": "...", "voz": "...", "creditos": N, "refeitas": [...], "avisos": [...]}`.
6. Grave `audio: pronto` (ou `pronto_com_avisos`; `falhou` se nenhum vídeo tem narração). Mensagem final: por vídeo, OK, falas refeitas, avisos, motor e voz.

## C. PRODUÇÃO (madrugada, 01:07, 03:07 e 05:07)
1. Traga `_processo\` inteiro e `pautas\<hoje>\`. Sem pauta: termine com "Sem pauta para hoje: nada foi produzido." Copie para `run/`; `npm install --no-audit --no-fund`; `nohup python3 -m http.server 8790 >/dev/null 2>&1 &`. Grave `producao: em_andamento`. Traga os `.fbx` e `.glb` dos itens para `run/anims/` e `run/objetos/`.
2. Carrosséis (c1→c3): `node carrossel.js pautas/<data>/cN/carrossel.json out/cN cN`; folha de contato das 5 imagens; corrija texto estourando (encurte mantendo o sentido) e erro pouco visível (ângulo, vista). Máx. 3 rodadas. Entregue.
3. Portão dos vídeos. Fechado: encerre o turno (carrosséis já entregues; a execução seguinte lê o `estado.json` e não refaz). Se `producao` já for `produzida`, termine em uma linha.
4. Vídeos (v1→v3): `episode.json` → `run/`; stills `node stills.js "[1.5,5,8.6,12,15,18.2,21.4,24.6,28,31,35]" c1` → folha de contato 6×2 e conferência (`reference/conferir.md`); `bash render_all.sh video.mp4 narracao_sync.wav` (sem o wav se não houver `audio.json`); música: `python3 mix_musica.py video.mp4 musicas final.mp4 --n <dia_do_ano*3 + k>` (k = 0,1,2; sem faixas, entregue só com narração e avise); conferência final; entregue. Pode ajustar vista, zoom e deform; não mude texto nem narração.
5. Entrega: `DRIVE\Videos-Prontos\<data>\` com `HHMM_video_<exercicio>.mp4` + `.txt`, `HHMM_carrossel_<slug>_1..5.jpg` + `.txt` (sufixo `_sem-narracao` quando for o caso). Copie para `/mnt/user-data/outputs/<data>/` e `device_commit_files` (arquivo > 28 MB: `SendUserFile` e commit pelo `fileUuid`). `historico.csv`: 1 linha por item `data;horario;exercicio;grupo;tema;arquivo;versao_narracao;creditos` (carrossel: horario = `carrossel HH:MM`, exercicio = título, grupo = tipo) + música usada. `pauta.json` `status: produzida`; `producao: produzida`.
6. Mensagem da manhã:
   ```
   ✅ <data> — <TEMA>, tudo em Videos-Prontos\<data>
   07:00 🎬 <exercício> · 09:30 🖼️ <título> · 12:30 🎬 … · 15:30 🖼️ … · 19:30 🎬 … · 21:30 🖼️ …
   ⚠️ <só se houver: sem narração, falas com aviso, item que falhou e por quê>
   ```
Um item que falha não impede os outros. Nunca altere `template.html` nem `carrossel.html` numa execução agendada.
