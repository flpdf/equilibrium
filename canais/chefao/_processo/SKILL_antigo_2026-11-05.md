---
name: chefao-academia-video
description: Produz 1 vídeo vertical "Chefão" de dicas de academia (boneco 3D Mixamo, narração ElevenLabs, estética de videogame) e salva no Drive do Felipe para postar. Use nas execuções agendadas ou quando ele pedir um vídeo novo do perfil.
---

# Vídeo "Chefão" de academia — 1 episódio por execução

Formato fixo de 37 s (1080×1920, 30 fps), para musculação, cardio em máquina (esteira, bicicleta) e lutas (boxe, capoeira): gancho → cartão "Seleção de desafio" → 3 erros (boneco vermelho errado → corte → boneco branco certo) → "desbloqueado" → "Chefão carregando…" → tela de comentário (sem voz).
O Felipe não aprova tema: escolha você, siga as regras e entregue o arquivo. Execução normalmente sem ninguém olhando: não pergunte nada; decida, registre e siga.

## Caminhos fixos (computador do Felipe, Windows)
- `DRIVE` = `G:\Meu Drive\Área de Trabalho\Mixamo-Academia` (pasta sincronizada com o Google Drive)
  - `DRIVE\_processo\` → `template.html`, `stills.js`, `render.js`, `render_all.sh`, `sync_audio.py`, `package.json`, `catalogo.csv`, `historico.csv`, `exemplos\*.json`
  - `DRIVE\<Pasta>\<arquivo>.fbx` → animações (pasta e arquivo vêm do `catalogo.csv`)
  - `DRIVE\Objetos\*.glb` → objetos 3D (esteira, bicicleta ergométrica, saco de pancada) + `CREDITOS.txt` (licença CC BY: crédito obrigatório)
  - `DRIVE\Videos-Prontos\` → saída
- `DL` = `C:\Users\amori\Downloads` (onde o navegador do app salva o áudio)
- O terminal do computador NÃO acessa a pasta G: nem a internet do ElevenLabs. Use só: `device_stage_files` (trazer arquivos), `device_commit_files` (gravar), `device_list_dir` (listar) e o navegador embutido (`Claude_Browser__*`) para baixar o áudio. Todo o processamento roda no container.

## 0. Pré-checagem (para em caso de falha)
1. `get_device_info`. Sem resposta / computador offline → pare. Mensagem final: "Computador offline às HH:MM — vídeo do horário <slot> não foi gerado."
2. Descubra o slot pelo horário local (America/Sao_Paulo): antes das 9h = `manha` (postar 7h); 9h–15h = `almoco` (postar 12h30); depois = `noite` (postar 19h30).

## 1. Trazer o processo e escolher o tema
1. `device_stage_files` de todo `DRIVE\_processo\` (arquivos listados acima, inclusive `exemplos\`). Copie para uma pasta de trabalho nova no scratchpad (`run/`).
2. Leia `catalogo.csv` e `historico.csv`.
3. Grupo do slot:
   - `manha` → `inferiores`
   - `almoco` → `superiores`
   - `noite` → alterna `core` → `cardio` → `lutas` → `corpo_inteiro` → `cardio_maquinas` (o seguinte ao último grupo usado à noite no histórico)
   - Nunca use o grupo `natacao` (ainda sem cenário de água) nem linhas do catálogo marcadas "não usar".
4. Dentro do grupo, o exercício usado há mais tempo (ou nunca). Nunca o mesmo exercício duas vezes no mesmo dia.
5. Escolha 3 erros desse exercício que ainda não apareceram no histórico para ele. Se todos já saíram, mude o ângulo do tema (ex.: "3 ajustes", erros de iniciante x avançado), sem repetir as mesmas 3 falas.
6. `device_stage_files` do `.fbx` escolhido → `run/anims/<arquivo>.fbx`. Se o episódio usar objeto (coluna observação do catálogo), traga também `DRIVE\Objetos\<arquivo>.glb` → `run/objetos/<arquivo>.glb` e os `exemplos\*.config.json`.

### Regras de conteúdo (obrigatórias — é orientação sobre o corpo de quem assiste)
- Só dicas de técnica amplamente aceitas por educadores físicos (alinhamento, amplitude, controle, respiração, posição de pés/joelhos/coluna/ombros/cotovelos/pescoço).
- Proibido: promessa de resultado ("seca barriga em 7 dias"), números de carga/séries/calorias, diagnóstico, dor/lesão como garantia ("vai destruir seu joelho"), conselho médico, suplemento.
- Linguagem: "pode sobrecarregar", "tira a tensão do músculo", "perde eficiência". Tom de jogo, nunca de alarme.
- Exercício avançado (pistol, snatch, clean and jerk, jump push up): foque em controle/postura, sem incentivar iniciante a tentar.
- Equipamento que não aparece (barra, halter, caixa, corda): fale do movimento, não do objeto. Esteira, bicicleta ergométrica e saco de pancada APARECEM (objetos 3D).
- Lutas (boxe, capoeira): técnica de golpe/base/guarda e postura; nada de luta contra outra pessoa, nocaute ou violência. Capoeira: pode valorizar a cultura brasileira (nomes dos golpes em português).
- Cardio em máquina: postura, passada, cadência, ajuste do selim (joelho levemente flexionado embaixo), não se apoiar no corrimão — sem números de velocidade/calorias.
- Na dúvida sobre um erro, escolha outro mais consagrado.

## 2. Escrever os arquivos do episódio
Use `exemplos\*.episode.json` e `*.narration.json` como molde. Tudo em PT-BR, MAIÚSCULAS nos textos de tela.

`run/episode.json`:
- `anim`: nome do arquivo em `anims/`. `peak`: `{"bone","metric"}` do catálogo (ponto alto/baixo da repetição).
- `watermark`, `topbar.left` (ex: `VOCÊ · "SÓ UMA SÉRIE"`), `topbar.right` (ex: `CHEFÃO DO OMBRO`).
- `card.name` (1–2 linhas, ≤ 12 caracteres cada), `card.rows` = 3 linhas `[rótulo, valor, "r" opcional p/ vermelho]`: MÚSCULOS, NÍVEL (★☆), RISCO.
- `captions`: EXATAMENTE 11 itens, na ordem: gancho A, gancho B, cartão A, cartão B, erro1, correção1, erro2, correção2, erro3, correção3, desbloqueado. Cada item = lista de `[palavra(s), cor]` com cor `""`, `"r"` (erro) ou `"g"` (certo). Máx. ~4 blocos e ~24 caracteres por item.
- `errors`: 3 itens `{label, check, view, zone, deform, [always], [static], [lift], [zoom], [arrows]}`
  - `label` = texto curto do erro (rodapé); `check` = item do checklist (o jeito certo, ≤ 20 caracteres).
  - `view`: `front`, `front_low`, `high_front`, `top_front`, `threequarter`, `side`, `side_left`, `low_side`, `back`. Escolha a vista em que o erro aparece melhor (joelho para dentro → front; coluna/quadril/calcanhar/cabeça → side).
  - `zone`: ossos onde desenhar a "zona de perigo" (nomes sem o prefixo `mixamorig`: Hips, Spine, Spine1, Spine2, Neck, Head, LeftArm, LeftForeArm, LeftHand, LeftUpLeg, LeftLeg, LeftFoot, LeftToeBase e os Right*).
  - `deform`: lista `{bone, axis:"x|y|z", angle (radianos), mirror}`. `mirror:true` em osso Left* aplica o espelho no Right* (sinal invertido em y/z). Por padrão o erro cresce com a profundidade da repetição; `always:true` = erro o tempo todo (bom para postura em flexão/prancha); `static:true` = exercício isométrico.
  - `lift`: cm para levantar o boneco (calcanhar subindo ≈ 9). `zoom` < 1 aproxima a câmera (deitados: 0.8). `arrows:"out"` = setas verdes "para fora" nos 2 ossos de `zone`.
- Cena com objeto/ajustes (copie o `exemplos\<cena>.config.json` validado e não mexa nos números sem conferir no still):
  - `props`: lista `{file, fit:{axis,cm}, pos:[x,y,z], rotY}` (objeto em `objetos/`, escalado para `cm` no eixo `axis`, base no chão).
  - `modelOffset` `[x,y,z]` (cm) desloca o boneco (ex.: em cima da esteira, sentado no selim); `lockRoot:true` trava o boneco no lugar (capoeira); `baseDeform` = deformação aplicada a TODOS os bonecos (pose base, ex.: braços no guidão); `pedal:{rps}` = pedalada procedural.
  - `peak.metric` aceita `minY|maxY|minZ|maxZ|minX|maxX` (ex.: soco = mão da frente `maxZ`).
  - Configs validadas: `esteira.config.json` (Treadmill Running/Jogging/Runs + esteira), `bicicleta.config.json` (Sitting Still Chair + bicicleta + pedal), `boxe.config.json` (golpes + saco, vista lateral), `capoeira.config.json` (lockRoot + hookZoom 0.75).
  - Usou objeto do Sketchfab → ponha o crédito do `CREDITOS.txt` na legenda ("Modelo 3D: <nome> por <autor> (Sketchfab, CC BY 4.0)").
- `hookView` (opcional) e `hookZoom` (opcional, deitados: 0.8; capoeira: 0.75). `outro.next` = próximo exercício anunciado (pegue do próximo slot). `outro.percent` 20–80. `cta.cards` = 3 exercícios sugeridos `[nome com \n, "GRUPO · ★★★☆☆"]`.

Deformações já validadas visualmente (reaproveite):
| erro | deform |
|---|---|
| joelho para dentro (valgo) | LeftUpLeg z −0.17 mirror; LeftUpLeg y +0.22 mirror; LeftLeg z +0.16 mirror (view front, arrows out) |
| calcanhar subindo | Left/RightFoot x −0.55; Left/RightToeBase x +0.44; Left/RightLeg x +0.18; lift 9 (view side) |
| coluna arredondada (em pé) | Spine/Spine1/Spine2 x +0.26; Neck x −0.25; Hips x −0.15 (view side) |
| quadril caindo (flexão/prancha) | Spine x +0.30; Spine1 x +0.22; Hips x −0.26; always (view side, zoom 0.8) |
| cotovelo aberto (flexão) | LeftArm z +0.45 mirror (view front_low, zoom 0.85) |
| cabeça caindo (deitado) | Neck x +0.45; Head x +0.35; always (view side, zoom 0.8) |
Para um erro novo, comece com 0.2–0.4 rad, confira no still e inverta o sinal se ficar ao contrário.

`run/narration.json` → `{"lines":[10 falas]}`, uma por cena, na ordem: gancho (0–3,4 s), cartão (3,4–7,2), erro1, correção1, erro2, correção2, erro3, correção3, "Pronto. <Exercício> desbloqueado!", "Segue aí, que o próximo chefão é <outro.next>." Cada fala cabe em ~3 s: até ~45 caracteres (falas 2 e 10 até ~55). Escreva números por extenso ("quarenta e cinco graus"). Toda fala termina com . ! ou ?; reticências só no meio.

`run/legenda.txt`: 1 linha de gancho + pergunta para comentar + 6–8 hashtags (#academia #treino #musculacao #dicasdetreino #fitness + 1–3 do exercício/músculo) + a linha "⚠️ Ao postar: marque 'Conteúdo gerado por IA'. Postar às <hora do slot>."

## 3. Conferir a imagem antes de gastar créditos
1. Em `run/`: `npm install --no-audit --no-fund`; suba o servidor: `nohup python3 -m http.server 8790 >/dev/null 2>&1 &`.
2. `node stills.js "[1.5,5,8.6,12,15,18.2,21.4,24.6,28,31,35]" c1` → abra uma folha de contato (PIL, 6×2, 270×480) e OLHE:
   - erro visível no boneco vermelho e certo no branco; deformação no sentido certo, sem membro atravessando o corpo;
   - boneco inteiro na tela, sem cobrir legenda ou checklist; legendas sem estourar a largura.
3. Ajuste o `episode.json` (ângulo, sinal, vista, zoom) e repita. Máx. 4 rodadas; se um erro não ficar legível, troque esse erro por outro.

## 4. Narração (ElevenLabs — gasta créditos, nunca repetir chamada)
> **Regra atual (decisão do Felipe em 05/11/2026): UMA versão por vídeo.** Se o texto da tarefa agendada disser "2 versões", está desatualizado — siga esta skill e use `generations_count: 1`.

1. `creative_generate_speech`: `model_id` `eleven_v4`, `voice_id` `7ete3BaGPf3vlbnyJnJK` (Fernando Nowvaro), **`generations_count: 1`** (uma versão só — decisão do Felipe, metade dos créditos), `prompt` = `[energetic] ` + as 10 falas separadas por linha em branco, com `[excited] ` antes da fala 9.
   - Entonação consistente entre vídeos (o Felipe aprovou a dos primeiros): nunca troque voz, modelo ou marcações; use SÓ `[energetic]` no início e `[excited]` antes da fala 9, nenhuma outra tag. Mantenha o mesmo ritmo de roteiro: gancho em pergunta curta, "Erro um/dois/três: <problema>." e correções no imperativo, frases curtas com ponto final.
2. Faça poll com `creative_get_flow_run_status` até `all_completed` e use essa única versão (o `sync_audio.py` acelera até 1,25× uma fala que não caiba na cena; não gere outra).
3. Se a geração falhar ou disser que está ocupada: NÃO tente de novo. Renderize sem narração (passo 5 sem wav), salve com sufixo `_sem-narracao` e registre no histórico.
4. Baixar o áudio (o container não acessa o domínio do ElevenLabs):
   - `Claude_Browser__preview_start` com a `content_url` da versão gerada (site já liberado; se pedir permissão, `request_access` com escopo "site").
   - `Claude_Browser__javascript_tool` na aba: `const r=await fetch(location.href);const b=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='narracao.mp3';document.body.appendChild(a);a.click();({size:b.size})`
   - `device_list_dir` em `DL` até aparecer um arquivo novo (`.tmp` ou `.mp3`) com exatamente esse tamanho (até ~30 s); `device_stage_files` dele → copie para `run/narracao.mp3`. Feche a aba (`tabs_close`).
5. Tempos das palavras: `creative_add_flow_asset_node` (modality `audio`, `generation_id` da versão gerada, mesmo `flow_id`) → `creative_transcribe_audio` (`eleven_scribe_v1`, `connect_from` = node retornado, mesmo `flow_id`) → poll → salve `transcripts[0].words` como `run/words.json` (lista de `{text,start,end}`).
6. `python3 sync_audio.py narracao.mp3 words.json narracao_sync.wav`. Se acusar erro de contagem de falas, confira se o texto da transcrição bate com `narration.json` (pontuação) e ajuste `narration.json` para o que foi falado de fato (sem gerar de novo).

## 5. Renderizar e conferir
1. `bash render_all.sh video.mp4 narracao_sync.wav` (~7–10 min; renderiza 5 partes em paralelo). Precisa do servidor da etapa 3 no ar.
2. Confira: duração 37 s; folha de contato `ffmpeg -i video.mp4 -vf "fps=1/3,scale=216:-1,tile=7x2" -frames:v 1 check.jpg` e olhe; áudio presente (`ffprobe`).

## 6. Entregar no Drive e registrar
1. Nome: `AAAA-MM-DD_<slot>_<exercicio-sem-acento>.mp4` (+ `.txt` com a legenda). Copie para `/mnt/user-data/outputs/run/` e grave com `device_commit_files` em `DRIVE\Videos-Prontos\`.
2. Histórico: `device_stage_files` de `DRIVE\_processo\historico.csv` (versão atual), acrescente a linha `data;horario;exercicio;grupo;tema;arquivo_video;versao_narracao;creditos` (créditos = soma dos `credit_costs` da geração) e grave de volta com `device_commit_files` usando `expectedMtimeMs`.
3. Mensagem final curta (vai como notificação): exercício, os 3 erros, nome do arquivo, horário de postar, créditos gastos — ou o motivo da falha.

## Se algo quebrar
- Erro de página no `stills.js` (PAGE ERROR): quase sempre JSON inválido ou nome de osso errado no `episode.json`.
- Boneco fora de quadro: aumente `zoom` (>1 afasta) ou troque a vista.
- Render parou no meio: rode só a parte que faltou (`node render.js <ini> <fim> parts/pN`) e refaça a junção do `render_all.sh`.
- Nunca altere `template.html` durante uma execução agendada; se achar um bug, entregue o vídeo como der e descreva o problema na mensagem final.