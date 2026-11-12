---
name: chefao-academia-video
description: Fluxo diário do perfil "Chefão dos Treinos" (academia, boneco 3D Mixamo, estética de videogame) — PAUTA da véspera para o Felipe aprovar, ÁUDIO das narrações e PRODUÇÃO de madrugada de 3 vídeos + 3 carrosséis no Drive. Use nas execuções agendadas ou quando ele pedir pauta, vídeo ou carrossel do perfil.
---

# Chefão dos Treinos — fluxo diário (pauta → áudio → produção)

Cada dia publica **3 vídeos** (37 s, 1080×1920) e **3 carrosséis** (5 imagens 1080×1920), todos do MESMO tema do dia.
O fluxo tem 3 etapas, cada uma numa tarefa agendada diferente. Toda tarefa diz qual etapa rodar; rode só a sua.

| Etapa | Quando | O que faz |
|---|---|---|
| A. PAUTA | 18h da véspera | Escolhe tudo do dia seguinte, escreve os arquivos e manda a pauta ao Felipe. Aplica os ajustes que ele responder. |
| B. ÁUDIO | 23h da véspera | Gera as narrações fala por fala, confere cada fala, refaz só as ruins e monta (separado da produção: o PC do Felipe é fraco). Espera a pauta estar pronta. |
| C. PRODUÇÃO | 1h | Faz os 3 carrosséis, espera o áudio ficar pronto, renderiza os 3 vídeos, entrega no Drive e manda o resumo da manhã. |

**Regra de aprovação (decisão do Felipe):** se ele não responder à pauta, a produção segue a pauta como proposta. Vendas estão desligadas até o perfil aquecer (`grade.json` → `vendas.ativo`); quando ligarem, vídeo de venda NUNCA sai sem "ok" explícito dele.

## Caminhos fixos (computador do Felipe, Windows)
- `DRIVE` = `G:\Meu Drive\Área de Trabalho\Mixamo-Academia` (sincronizada com o Google Drive)
  - `DRIVE\_processo\` → `SKILL.md` (este arquivo — é a versão que manda), `grade.json`, `template.html`, `carrossel.html`, `carrossel.js`, `stills.js`, `render.js`, `render_all.sh`, `audio_falas.py` (falas: dividir/checar/tratar/montar), `perfil_voz_chefao.json` (alvo da equalização da voz), `mix_musica.py` (música de fundo), `sync_audio.py` (antigo, narração inteira), `package.json`, `catalogo.csv`, `historico.csv`, `exemplos\*.json`
  - `DRIVE\_processo\pautas\AAAA-MM-DD\` → a pauta do dia (ver formato abaixo)
  - `DRIVE\_processo\musicas\` → faixas de batida eletrônica LIVRES DE DIREITOS (mp3/wav/m4a) que o Felipe coloca lá; a PRODUÇÃO mixa uma em cada vídeo (ver **Música**)
  - `DRIVE\<Pasta>\<arquivo>.fbx` → animações (pasta e arquivo vêm do `catalogo.csv`); `DRIVE\Objetos\*.glb` + `CREDITOS.txt`
  - `DRIVE\Videos-Prontos\` → saída
- `DL` = `C:\Users\amori\Downloads` (onde o navegador do app salva o áudio)
- O terminal do computador NÃO acessa a pasta G: nem a internet do ElevenLabs. Use só `device_stage_files`, `device_commit_files`, `device_list_dir` e o navegador embutido (`Claude_Browser__*`). Todo o processamento roda no container.
- Pré-checagem de toda etapa: `get_device_info`. Sem resposta → pare e termine com "Computador offline às HH:MM — etapa <X> do dia <data> não rodou." (A etapa seguinte verifica o que faltou.)

## Formato da pauta — `pautas\AAAA-MM-DD\`
```
pauta.json            resumo (abaixo)
v1\ v2\ v3\           vídeos manhã / almoço / noite: episode.json, narration.json, legenda.txt
                       (+ depois do ÁUDIO: narracao_sync.wav, audio.json, falas\01..10.mp3, falas\qa.json)
estado.json           em que pé está cada etapa (ver Portões)
c1\ c2\ c3\           carrosséis: carrossel.json, legenda.txt
```
`pauta.json`:
```json
{"data":"2026-11-06","dia":"sex","tema":"DIA DE CORE","status":"proposta",
 "videos":[{"id":"v1","slot":"manha","postar":"07:00","nivel":"base","exercicio":"Prancha","arquivo":"Plank.fbx","pasta":"Core",
            "erros":["quadril caindo","quadril alto","cabeça caindo"],"gancho":"Sua prancha tá te enganando?"}],
 "carrosseis":[{"id":"c1","postar":"09:30","tipo":"erros","titulo":"4 ERROS QUE TRAVAM SEU ABDÔMEN","itens":["…","…","…","…"]}],
 "vendas":0,"ajustes":[]}
```
`status`: `proposta` → `aprovada` (Felipe respondeu ok/ajustes) ou `padrao` (sem resposta até o ÁUDIO). `ajustes` = o que ele pediu, em palavras curtas.

---

## A. PAUTA (véspera, 18h)
1. Pré-checagem. Data alvo = amanhã (America/Sao_Paulo). Dia da semana → tema em `grade.json` → `dias`.
2. `device_stage_files` de `DRIVE\_processo\` (`grade.json`, `catalogo.csv`, `historico.csv`, `exemplos\*.json`, `SKILL.md`) e das pautas dos últimos 7 dias, se existirem (`device_list_dir` em `pautas\`).
   **Item reservado:** se `pautas\<amanhã>\` já existir com `reservado.json`, traga a pasta inteira. Cada vídeo listado ali já está escrito (pedido do Felipe): mantenha o slot, o exercício e os textos; só ajuste `outro.next`, a fala 10 e os `cta.cards` pela regra normal, se precisar. Escolha os outros vídeos e os carrosséis normalmente (sem repetir o exercício reservado) e inclua o reservado no `pauta.json` e na mensagem da pauta.
3. **Vídeos (3)** — dentro dos grupos (e `pasta`, se houver) do tema, siga a `trilha` do `grade.json`:
   - manhã = o mais básico da trilha que não saiu nos últimos 7 dias; almoço = o seguinte; noite = o mais desafiador disponível (avançado só à noite, foco em controle).
   - Sem repetir exercício no mesmo dia. Se o grupo tiver menos de 3 exercícios livres, repita o menos recente com um ÂNGULO novo ("3 ajustes de iniciante", "erros de quem já treina").
   - 3 erros por vídeo que ainda não saíram para aquele exercício no `historico.csv`. Use `catalogo.csv` (não use linhas "não usar"; natação só em item reservado ou quando o tema do dia no `grade.json` incluir o grupo `natacao` — ver **Natação**).
   - `outro.next` de cada vídeo = o exercício do vídeo seguinte; o da noite = o 1º exercício do tema de depois de amanhã.
4. **Carrosséis (3)** — 3 tipos diferentes de `grade.json` → `carrosseis.tipos`, sempre do tema do dia. Um deles de preferência "erros" (pode reaproveitar erros dos vídeos do dia + 1 inédito).
5. Escreva os arquivos de cada item na pasta de trabalho, seguindo as seções **Vídeo** e **Carrossel** abaixo (episode.json, narration.json, legenda.txt; carrossel.json, legenda.txt). Valide todo JSON com `python3 -m json.tool`. As falas/textos ficam prontos aqui: o ÁUDIO e a PRODUÇÃO não reescrevem texto.
6. Grave tudo em `DRIVE\_processo\pautas\AAAA-MM-DD\` com `device_commit_files` (`pauta.json` com `status:"proposta"` e `estado.json` = `{"pauta":"proposta","audio":"pendente","producao":"pendente"}`).
7. Mande a pauta ao Felipe com `SendUserMessage`, curta e escaneável:
   ```
   📋 Pauta de <dia>, <data> — <TEMA>
   🎬 07:00 · <exercício> — <erro1>, <erro2>, <erro3>
   🎬 12:30 · …
   🎬 19:30 · …
   🖼️ 09:30 · <título do carrossel 1> (<tipo>)
   🖼️ 15:30 · …   🖼️ 21:30 · …
   Responda "ok" ou o que mudar (ex.: "troca o 2 por rosca", "carrossel 3 de mitos"). Sem resposta até as 23h, produzo assim.
   ```
8. Encerre o turno e espere. **Se o Felipe responder** (mesmo depois): grave `estado.pauta:"em_ajuste"` ANTES de mexer (segura o ÁUDIO no portão), aplique os ajustes (reescreva só os itens afetados, nas mesmas regras), grave de novo com `device_commit_files`, `status:"aprovada"` (e `estado.pauta:"aprovada"`), registre em `ajustes`, e confirme em 1 linha. Se a resposta chegar depois que o ÁUDIO já gerou a narração de um vídeo alterado, apague `vN\audio.json` dele (renomeie para `audio_antigo.json`) — a PRODUÇÃO então renderiza esse vídeo sem narração e avisa.

## Portões entre etapas (está pronto? se não, espere)
Cada etapa só começa quando a anterior terminou. Se o portão não abre: não faça nada, agende `send_later` (`delay_minutes: 15`) para ESTA sessão com "Repita a checagem do portão da etapa <X> e siga se abrir." e encerre o turno. Prazos-limite abaixo evitam esperar para sempre.
- Arquivo de estado: `pautas\AAAA-MM-DD\estado.json` = `{"pauta":"proposta|em_ajuste|aprovada|padrao","audio":"pendente|em_andamento|pronto|pronto_com_avisos|falhou","producao":"pendente|em_andamento|produzida","atualizado":"<hora>"}`. Cada etapa atualiza só o seu campo (traga a versão atual antes de gravar).
- **Portão do ÁUDIO:** pauta existe, todos os `vN\narration.json` existem e `pauta` ≠ `em_ajuste`. Prazo: 00:30 — depois disso, siga com o que houver e avise.
- **Portão da PRODUÇÃO (vídeos):** `audio` = `pronto` ou `pronto_com_avisos`. Enquanto espera, produza os carrosséis (não dependem de áudio). Prazo: 05:15 — depois disso, renderize sem narração os vídeos que não têm `audio.json` (o das 07:00 precisa sair a tempo) e avise.

## B. ÁUDIO (véspera, 23h) — narração com UMA voz só, conferida, tratada e equalizada

### VOZ — sempre sotaque BRASILEIRO e SEMPRE a mesma voz (decisões do Felipe, 06/11 e 09/11/2026)
- A narração tem que soar brasileira nativa ("céu" é /sɛw/, nunca /seu/). Reprovados: 06/11 (sotaque gringo) e 08–09/11 (voz mecânica/robótica, "várias vozes intercaladas", sotaque que vai e volta, uma fala com som de rádio/"torre de comando").
- Causas medidas em 09/11 (falas de 08/11, voz `79c4cf5c`): o TOM mudava de 125 a 318 Hz entre falas do mesmo vídeo (cada fala gerada separada, sem semente fixa, fala 9 com estilo "excited") e o BRILHO (agudos acima de 4 kHz) variava 40x entre falas (umas abafadas como rádio, outras normais). As referências das vozes "AlertaSP … BR" foram criadas a partir das vozes desenhadas (mesmo texto para várias vozes), então carregam o sotaque e os artefatos delas.
- **Nunca use voz desenhada** (`kind: design`, inclusive `37415022`) **nem `79c4cf5c`** para o Chefão.
- **Voz do Chefão (padrão desde 09/11/2026, escolha do Felipe): `"Chefão - Narrador BR v2"` = id `326eb164`** (VoiceStudio, `kind: clone`, `language: "pt"`, com `ref_text`). Referência: `vozes\Audio1.mp3` (9,3 s, gravação de amigos do Felipe, que autorizaram o uso). `ref_text` exato: "Você não precisa mais procurar por uma voz para mídias sociais. Esta é a ideal para Shorts, Reels, TikTok, Instagram. Sim, você acaba de encontrar." Todo vídeo do Chefão usa essa voz. Não use a `9fc027c1` (mesma referência, salva sem transcrição: cada geração retranscreve e passa do tempo). Se `326eb164` sumir de `voicestudio__list_voices`, recrie com `voicestudio__clone_voice` (`name` "Chefão - Narrador BR v2", `ref_audio_path` `vozes\Audio1.mp3` — relativo ao OMNIVOICE_MCP_BASE_PATH = pasta Mixamo-Academia —, `language` "pt", `ref_text` acima). Geração direta pelo MCP no PC do Felipe é cancelada em 3 min: gere pela fila `_fila_voz` (sem esse limite). Se nada der certo até 00:30, use a reserva (ElevenLabs) e avise.
- **Parâmetros fixos de geração** (todo pedido da fila, toda fala, toda refação): `profile_id` = id da "Chefão - Narrador BR", `language: "pt"` (o motor do VoiceStudio NÃO reconhece "pt-BR" nem "Portuguese (Brazil)": cai no modo sem idioma e sai com sotaque estrangeiro — visto no log em 09/11; "pt" já é português do Brasil), `steps: 32` (menos que isso soa robótico), `speed: 1.0` (só suba para 1.1–1.2 numa fala que não cabe na cena — nunca acelere depois com atempo acima de 1,15x), `seed: 1909` (fixa), `instruct` vazio (nada de "excited"/"energetic": muda o tom e parece outra pessoa; a energia vem do texto e da pontuação).
- **Gravação única:** peça as 10 falas NUMA geração só (`"modo": "inteira"`, texto = as 10 falas separadas por linha em branco), para a voz ser a mesma do começo ao fim; depois `python3 audio_falas.py dividir inteira.wav run/vN/falas` corta nas 9 maiores pausas. Se o Iniciador devolver as falas separadas (pedido antigo), siga com elas: a checagem de consistência pega a fala que destoar.
- **Reserva: ElevenLabs** `voice_id` `7ete3BaGPf3vlbnyJnJK` (Fernando Nowvaro), `model_id` `eleven_multilingual_v2`, SEM marcações `[...]`. Use se o VoiceStudio não responder até 00:30 ou se o vídeo for reprovado por sotaque/consistência depois de 2 rodadas. Nunca misture motores no mesmo vídeo: se trocar, troque as 10 falas.
- Na checagem, palavras deformadas de sotaque estrangeiro na transcrição (ex.: "Errum", "Juelos", "Deça", "dondado", "glúcio", "estera") em 2 ou mais falas do vídeo = vídeo reprovado.
- Baixar áudio do ElevenLabs: o container não acessa `elevenlabsusercontent.com`; baixe pelo navegador do app para `Downloads` (passo 2.2).

1. Pré-checagem e **portão do ÁUDIO**. Traga `pauta.json`, `estado.json` e cada `vN\narration.json`. Se `pauta` = `proposta`, grave `padrao`. Grave `audio:"em_andamento"`. Traga também `audio_falas.py` e `perfil_voz_chefao.json` de `_processo\` e instale as dependências (`pip install librosa pyloudnorm noisereduce --break-system-packages`).
2. Para cada vídeo sem `vN\audio.json`:
   1. **Gerar (VoiceStudio):** grave o pedido em `_processo\_fila_voz\<data>_chefao_vN.json` com os parâmetros fixos da VOZ (`modo: "inteira"`). Espere o resultado em `_fila_voz\feitos\` (cheque a cada 3 min; espera longa = `send_later` de 10 min). Traga o áudio; se veio inteiro, `dividir`. **(Reserva ElevenLabs:** `creative_create_flow` (um por vídeo); `creative_generate_speech` por fala no mesmo `flow_id`, `generations_count: 1`, `prompt` = a fala.)
   2. Baixar (só ElevenLabs): `Claude_Browser__preview_start` com a `content_url` da fala 1; na aba, `Claude_Browser__javascript_tool` baixando todas de uma vez: `const U=[<as 10 content_urls>];const out=[];for(let i=0;i<U.length;i++){const b=await (await fetch(U[i])).blob();const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='vN_'+String(i+1).padStart(2,'0')+'.mp3';document.body.appendChild(a);a.click();out.push(b.size);await new Promise(r=>setTimeout(r,400));}out`. `device_list_dir` em `DL` até os 10 arquivos aparecerem; `device_stage_files`; copie para `run/vN/falas/01.mp3 … 10.mp3`. Feche a aba.
   3. Ouça o que foi dito: transcreva cada fala (Whisper do Iniciador, ou `creative_transcribe_audio` `eleven_scribe_v1`) e monte `run/vN/transcricoes.json` = `{"01":"texto ouvido",…}`.
   4. **Checar:** `python3 audio_falas.py checar run/vN/falas run/vN/narration.json run/vN/transcricoes.json`. Reprova: sem voz, longa demais (> 1,15x), curta, falou diferente, **tom destoa** (> ±25% do tom do vídeo; fala 9 até +40%), **timbre destoa**, **voz abafada** (sem agudos) e **ruído de fundo** acima de -40 dB.
   5. **Refazer só as reprovadas** (pedido com `"refazer": [...]` e `"rodada": N`, mesmos parâmetros e mesma semente; fala longa demais: `speed` 1.1–1.2 só nela). Até 2 rodadas. Fala aprovada nunca é refeita. Se depois de 2 rodadas o vídeo ainda tiver 3+ falas reprovadas por tom/timbre/sotaque, troque o vídeo inteiro para a reserva.
   6. **Tratar e EQUALIZAR entre as vozes** (obrigatório, depois da checagem): `python3 audio_falas.py tratar run/vN/falas run/vN/falas_tratadas perfil_voz_chefao.json`. Faz em todas as falas: corte de grave sujo (75 Hz), limpeza de ruído só onde há ruído (moderada, para não robotizar), **equalização de cada fala para a mesma curva de frequências** (alvo = narração brasileira aprovada, correção até ±9 dB por banda — tira o som de rádio/"torre de comando" e faz as falas soarem gravadas no mesmo microfone), de-esser, compressão leve e todas a -18 LUFS. Rode o `checar` de novo em `falas_tratadas` (só para conferir brilho e ruído).
   7. **Montar:** `python3 audio_falas.py montar run/vN/falas_tratadas run/vN/narration.json run/vN/narracao_sync.wav` (cada fala no início da sua cena, aceleração máx. 1,15x, 37 s, -14 LUFS por ganho linear — sem `loudnorm` dinâmico, que "bombeia").
   8. Grave em `pautas\<amanhã>\vN\`: `narracao_sync.wav`, `falas\01..10.wav` (tratadas), `falas\brutas\01..10.*`, `falas\qa.json`, `falas\tratamento.json` e `audio.json` = `{"motor":"voicestudio","voz":"<id> (Chefão - Narrador BR)","seed":1909,"steps":32,"modo":"inteira","tratamento":"eq perfil_voz_chefao","refeitas":["03"],"avisos":[…]}`.
3. Grave `audio:"pronto"` (ou `"pronto_com_avisos"` se algum vídeo ficou com aviso; `"falhou"` se nenhum vídeo tem narração).
4. Mensagem final curta: por vídeo, OK / quais falas foram refeitas / avisos; motor e voz usados.
Trocar de motor só muda os passos 2.1–2.3; checar, tratar e montar são sempre iguais.

## C. PRODUÇÃO (1h)
1. Pré-checagem. Data alvo = hoje. `device_stage_files` de `DRIVE\_processo\` inteiro (inclusive `carrossel.html`, `carrossel.js`, `grade.json`, `mix_musica.py` e a pasta `musicas\`) e de `pautas\<hoje>\` inteiro. Sem pauta → termine com "Sem pauta para hoje: nada foi produzido. Rode a PAUTA." Copie para `run/`; `npm install --no-audit --no-fund`; `nohup python3 -m http.server 8790 >/dev/null 2>&1 &`. Grave `producao:"em_andamento"`.
2. Traga os `.fbx` de todos os itens (e `.glb` se houver props) para `run/anims/` e `run/objetos/`.
3. **Carrosséis primeiro** (c1 → c3, não dependem do áudio): `node carrossel.js pautas/<data>/cN/carrossel.json out/cN cN`; olhe uma folha de contato das 5 imagens (PIL, 5 lado a lado). Corrija avisos "texto estourando" encurtando o texto (mantendo o sentido) e erro pouco visível (aumente o ângulo, troque a vista). Máx. 3 rodadas por carrossel. Entregue-os (seção Entrega).
4. **Portão da PRODUÇÃO** (ver Portões). Se o áudio não está pronto, agende a nova checagem e encerre o turno; ao voltar, retome daqui (não refaça os carrosséis já entregues).
5. **Vídeos** (um por vez, v1 → v3): copie `vN\episode.json` para `run/episode.json`, confira os stills (seção Vídeo › Conferir), renderize (`bash render_all.sh video.mp4 narracao_sync.wav`, ou sem o wav se não houver `audio.json`), **ponha a música** (`python3 mix_musica.py video.mp4 musicas final.mp4 --n <dia_do_ano*3 + k>`, k = 0/1/2 para v1/v2/v3 — ver **Música**), confira e entregue `final.mp4` (seção Entrega). Pode ajustar ângulo/vista/zoom/deform do episode.json; NÃO mude texto nem narração.
6. Grave `producao:"produzida"`. Mensagem final da manhã (vai como notificação), uma linha por item em ordem de horário:
   ```
   ✅ <data> — <TEMA>, tudo em Videos-Prontos\<data>
   07:00 🎬 <exercício> · 09:30 🖼️ <título> · 12:30 🎬 … · 15:30 🖼️ … · 19:30 🎬 … · 21:30 🖼️ …
   ⚠️ <só se houver: vídeo sem narração, falas com aviso, item que falhou e por quê>
   ```

---

## Vídeo — formato e regras (usado na PAUTA e na PRODUÇÃO)
Formato fixo de 37 s, 30 fps: gancho → cartão "Seleção de desafio" → 3 erros (boneco vermelho errado → corte → boneco branco certo) → "desbloqueado" → "Chefão carregando…" → tela de comentário (sem voz).

### Regras de conteúdo (obrigatórias — orientação sobre o corpo de quem assiste; valem também para carrosséis)
- Só dicas de técnica amplamente aceitas por educadores físicos (alinhamento, amplitude, controle, respiração, posição de pés/joelhos/coluna/ombros/cotovelos/pescoço).
- Proibido: promessa de resultado, números de carga/séries/repetições/calorias/velocidade, diagnóstico, dor/lesão como garantia, conselho médico, suplemento.
- Linguagem: "pode sobrecarregar", "tira a tensão do músculo", "perde eficiência". Tom de jogo, nunca de alarme.
- Exercício avançado (pistol, snatch, clean and jerk, jump push up, aú, armada, meia-lua de compasso): foque em controle/postura, sem incentivar iniciante a tentar.
- Equipamento que não aparece (barra, halter, caixa, corda): fale do movimento. Esteira, bicicleta ergométrica e saco de pancada APARECEM (objetos 3D).
- Lutas: técnica de golpe/base/guarda e postura; nada de luta contra outra pessoa, nocaute ou violência. Capoeira pode valorizar a cultura brasileira.
- Cardio em máquina: postura, passada, cadência, ajuste do selim, não se apoiar no corrimão.
- Curiosidades/mitos: só fatos consagrados e verificáveis (fisiologia básica); na dúvida, deixe de fora.

### episode.json
Use `exemplos\*.episode.json` como molde. PT-BR, MAIÚSCULAS nos textos de tela.
- `anim`, `peak` `{"bone","metric"}` do catálogo. `watermark`, `topbar.left` (ex: `VOCÊ · "SÓ UMA SÉRIE"`), `topbar.right` (ex: `CHEFÃO DO OMBRO`).
- `card.name` (1–2 linhas, ≤ 12 caracteres cada), `card.rows` = 3 linhas `[rótulo, valor, "r" opcional]`: MÚSCULOS, NÍVEL (★☆), RISCO.
- `captions`: EXATAMENTE 11 itens: gancho A, gancho B, cartão A, cartão B, erro1, correção1, erro2, correção2, erro3, correção3, desbloqueado. Cada item = lista de `[palavra(s), cor]` (`""`, `"r"`, `"g"`). Máx. ~4 blocos e ~24 caracteres.
- `errors`: 3 itens `{label, check, view, zone, deform, [always], [static], [lift], [zoom], [arrows]}` — `label` curto (rodapé); `check` = jeito certo ≤ 20 caracteres; `view` ∈ front, front_low, high_front, top_front, threequarter, side, side_left, low_side, back; `zone` = ossos sem prefixo `mixamorig` (Hips, Spine, Spine1, Spine2, Neck, Head, Left/Right Arm, ForeArm, Hand, UpLeg, Leg, Foot, ToeBase); `deform` = `{bone, axis, angle (rad), mirror}`; `always` = erro o tempo todo; `static` = isométrico; `lift` cm; `zoom` < 1 aproxima (deitados 0.8); `arrows:"out"`.
- Cenas com objeto: copie o `exemplos\<cena>.config.json` validado (`props`, `modelOffset`, `lockRoot`, `baseDeform`, `pedal`); crédito do `CREDITOS.txt` na legenda.
- **Saco de pancada (boxe) tem física** (pedido do Felipe, 10/11): o prop leva `"pend":{}` (já está no `exemplos\boxe.config.json`). O `template.html` pendura o saco pela corrente (40 cm do chão), posiciona sozinho na frente do soco mais longo e simula: cada soco que encosta dá um impulso proporcional à velocidade do punho (mão da frente mais leve que a de trás), o saco balança, gira um pouco em golpe de lado e afunda onde o punho entra. Não ponha `pos` z na mão. Ajustes opcionais em `pend`: `hang`, `reach` (cm que o soco mais longo afunda, padrão 6), `mass`, `zeta`. Como o saco fica NA FRENTE do boneco, nunca use vista `front`/`front_low`/`high_front`/`top_front` em cena com saco: use `back` (para pés/cotovelos), `side` ou `threequarter`; e ponha `"cardView":"side","outView":"side"`.
- `hookView`/`hookZoom` opcionais (deitados 0.8; capoeira 0.75). `outro.next` (ver PAUTA 3). `outro.percent` 20–80. `cta.cards` = 3 exercícios sugeridos `[nome com \n, "GRUPO · ★★★☆☆"]` — de preferência os próximos da trilha.

Deformações já validadas (reaproveite):
| erro | deform |
|---|---|
| joelho para dentro (valgo) | LeftUpLeg z −0.17 mirror; LeftUpLeg y +0.22 mirror; LeftLeg z +0.16 mirror (view front, arrows out) |
| calcanhar subindo | Left/RightFoot x −0.55; Left/RightToeBase x +0.44; Left/RightLeg x +0.18; lift 9 (view side) |
| coluna arredondada (em pé) | Spine/Spine1/Spine2 x +0.26; Neck x −0.25; Hips x −0.15 (view side) |
| quadril caindo (flexão/prancha) | Spine x +0.30; Spine1 x +0.22; Hips x −0.26; always (view side, zoom 0.8) |
| cotovelo aberto (flexão) | LeftArm z +0.45 mirror (view front_low, zoom 0.85) |
| cabeça caindo (deitado) | Neck x +0.45; Head x +0.35; always (view side, zoom 0.8) |
Erro novo: comece com 0.2–0.4 rad, confira no still, inverta o sinal se ficar ao contrário.

### narration.json
`{"lines":[10 falas]}`: gancho (0–3,4 s), cartão (3,4–7,2), erro1, correção1, erro2, correção2, erro3, correção3, "Pronto. <Exercício> desbloqueado!", "Segue aí, que o próximo chefão é <outro.next>." Até ~45 caracteres por fala (2 e 10 até ~55). Números por extenso. Toda fala termina com . ! ou ?. Ritmo aprovado: gancho em pergunta curta, "Erro um/dois/três: <problema>.", correções no imperativo.

### legenda.txt (vídeo)
1 linha de gancho + pergunta para comentar + 6–8 hashtags (#academia #treino #musculacao #dicasdetreino #fitness + 1–3 do exercício) + "⚠️ Ao postar: marque 'Conteúdo gerado por IA'. Postar às <hora>."

### Conferir (PRODUÇÃO)
`node stills.js "[1.5,5,8.6,12,15,18.2,21.4,24.6,28,31,35]" c1` → folha de contato (PIL, 6×2, 270×480) e OLHE: erro visível no vermelho e certo no branco; deformação no sentido certo, sem membro atravessando; boneco inteiro, sem cobrir legenda/checklist; legendas sem estourar. Ajuste e repita (máx. 4 rodadas; se um erro não ficar legível, troque o deform/vista — não o texto).
Depois do render: duração 37 s; `ffmpeg -i video.mp4 -vf "fps=1/3,scale=216:-1,tile=7x2" -frames:v 1 check.jpg` e olhe; áudio presente (`ffprobe`).

## Música (decisão do Felipe, 06/11/2026) — todo vídeo leva música
- Narração a **100%**, música a **10%** (o `mix_musica.py` iguala o volume da música ao da narração e baixa para 10%).
- Batida eletrônica, encaixada na narração: a música começa num tempo forte, no ponto em que ela "entra" (depois da introdução calma), junto com o gancho em 0 s; fade-out nos 1,5 s finais.
- Fonte: só faixas livres de direitos em `_processo\musicas\` (traga a pasta inteira para `run/musicas/` no passo C.1). Músicas da aba "Para você" do TikTok NÃO podem ser baixadas nem mixadas fora do app.
- As faixas `chefao_NN_<estilo>_150bpm_sync.mp3` são originais, geradas por `gerar_musicas.py` (chiptune/electro/house, 150 BPM: 2 compassos = 3,2 s = intervalo dos cortes de cena; começam com meio compasso de pickup, então os tempos fortes caem nos cortes 7,2 / 10,4 / 13,6 …). O `mix_musica.py` usa essas do início (sem procurar batida). Para variar, gere mais com outro `seed`/tom no script. Faixas de terceiros (Pixabay, YouTube Audio Library) também podem ir na pasta: o script acha a batida sozinho.
- Pasta vazia → o script entrega só com a narração e imprime AVISO: inclua "⚠️ sem música: coloque faixas em _processo\musicas" na mensagem da manhã.
- Registre a faixa usada (linha `MUSICA …` do script) em `historico.csv`, no campo `versao_narracao` (ex.: `voicestudio-chefaoBR+musica:neon_run.mp3`).
- Conferir: `ffprobe` com áudio presente e 37 s; a fala tem que ficar claramente acima da música.
- Carrosséis: a postagem (etapa D) liga `autoAddMusic: true` no TikTok (o TikTok põe uma música; carrossel não tem narração).

## Carrossel — formato (usado na PAUTA e na PRODUÇÃO)
5 imagens: slides 1–4 = os 4 itens (o slide 1 também leva o título do carrossel), slide 5 = pedido de comentário com o boneco. Gerado por `carrossel.js` + `carrossel.html` (mesmo motor 3D dos vídeos, sem créditos). Molde: `exemplos\erros.carrossel.json`.

`carrossel.json`:
- `id` (`c1`…), `cor` = cor de destaque: `"r"` (erros), `"y"` (curiosidades/cultura), `"g"` (treino/mito).
- `titulo` = linhas; cada linha é texto simples ou lista `[texto, cor]` (`""`,`"r"`,`"g"`,`"y"`). Até 2 linhas, ~22 caracteres cada.
- `slides` = EXATAMENTE 4 itens:
  - tipo **erro**: `{"tipo":"erro","kicker":"CHEFÃO DA PERNA","nome":"AGACHAMENTO","anim":"Air Squat.fbx","peak":{…},"erro":{view, zone, deform, always, static, lift, zoom},"errado":"JOELHO PRA DENTRO","certo":"JOELHOS NA LINHA DOS PÉS"}` (+ `cfg` com props/modelOffset/lockRoot se a cena precisar). `nome` ≤ 14 caracteres; `errado`/`certo` ≤ 28.
  - tipo **info**: `{"tipo":"info","tag":"CURIOSIDADE #1","titulo":[linhas],"anim":"…fbx","view":"threequarter","zoom":1,"pose":"pico|repouso","texto":"frase com **destaque**","tagcor":"r|g|y"}` (`tagcor` opcional: em mito/verdade use `"r"` para MITO e `"g"` para VERDADE). `titulo` até 2 linhas de ~18 caracteres; `texto` ≤ 140 caracteres.
- `cta` (opcional): `{"pergunta":[linhas],"sub":"COMENTA AÍ","botao":"SEGUE P/ DESBLOQUEAR","anim":"Fitness Idle.fbx"}`.
- `arrasta` (opcional): texto do rodapé.
Animação "parada" para slides de curiosidade: `Fitness Idle.fbx` (pasta Base-Aquecimento).

`legenda.txt` (carrossel): "TÍTULO: …" + 2–3 frases convidando a arrastar e comentar + 6–10 hashtags + "⚠️ Ao postar: ative 'Conteúdo gerado por IA'. Postar às <hora>."

## Entrega e histórico (PRODUÇÃO)
1. Pasta do dia: `DRIVE\Videos-Prontos\AAAA-MM-DD\` com nomes que ordenam pelo horário:
   `0700_video_<exercicio-sem-acento>.mp4` + `.txt`; `0930_carrossel_<slug>_1.jpg … _5.jpg` + `0930_carrossel_<slug>.txt`; etc. Vídeo sem narração ganha sufixo `_sem-narracao`.
   Copie para `/mnt/user-data/outputs/<data>/` e grave com `device_commit_files`.
2. `historico.csv`: traga a versão atual, acrescente 1 linha por item `data;horario;exercicio;grupo;tema;arquivo_video;versao_narracao;creditos` (carrossel: horario = `carrossel 09:30`, exercicio = título, grupo = tipo) e grave com `expectedMtimeMs`.
3. Atualize `pauta.json` com `"status":"produzida"`.

## Natação (cenário de piscina)
- Leia `DRIVE\_processo\PISCINA.md` e use `exemplos\natacao_crawl.episode.json` como molde.
- No `episode.json`: `"ambiente":"piscina"` + `"swim":{"stroke":"crawl|costas|borboleta|peito|flutuacao"}`; `anim` = `Swimming.fbx` (flutuação: `Treading Water.fbx`), da pasta `Natacao`.
- Erros de nado vão em `errors[i].swim` (parâmetros do boneco vermelho); `deform` continua valendo. Use primeiro os erros marcados como validados no PISCINA.md; os outros só depois de conferir no still.
- Vistas: `top`, `side_under`, `under_*`, `split*`; nadador deitado precisa de `zoom` 0.7–0.8 nas laterais. Cenas fixas: `hookView`/`cardView`/`winView`/`outView` (ex.: `split_threequarter`, `split_front`).
- Regras de conteúdo valem igual: só técnica consagrada (cabeça, alinhamento, entrada da mão, cotovelo alto, pernada do quadril, respiração), sem promessa de resultado nem números. Borboleta = avançado, foco em técnica.
- Render em piscina leva ~13 min (5 partes em paralelo). `Swimming Breaststroke.fbx` não serve (o boneco fica em pé no fim do ciclo).

## Animações que NÃO funcionam bem em vídeo (o boneco se desloca e o vermelho deforma)
- `Pike Walk.fbx` (inchworm): use só em carrossel (slide erro "joelhos dobrando" ficou bom); não use em vídeo.

## Se algo quebrar
- PAGE ERROR no `stills.js`/`carrossel.js`: quase sempre JSON inválido ou nome de osso errado.
- Boneco fora de quadro: aumente `zoom` (>1 afasta) ou troque a vista.
- Render parou no meio: rode só a parte que faltou (`node render.js <ini> <fim> parts/pN`) e refaça a junção do `render_all.sh`.
- Nunca altere `template.html` nem `carrossel.html` numa execução agendada; entregue como der e descreva o problema na mensagem final.
- Um item que falhou não impede os outros: entregue o resto e diga qual faltou e por quê.
