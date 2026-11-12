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
  - `DRIVE\_processo\` → `SKILL.md` (este arquivo — é a versão que manda), `grade.json`, `template.html`, `carrossel.html`, `carrossel.js`, `stills.js`, `render.js`, `render_all.sh`, `audio_falas.py`, `sync_audio.py` (antigo, narração inteira), `package.json`, `catalogo.csv`, `historico.csv`, `exemplos\*.json`
  - `DRIVE\_processo\pautas\AAAA-MM-DD\` → a pauta do dia (ver formato abaixo)
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
3. **Vídeos (3)** — dentro dos grupos (e `pasta`, se houver) do tema, siga a `trilha` do `grade.json`:
   - manhã = o mais básico da trilha que não saiu nos últimos 7 dias; almoço = o seguinte; noite = o mais desafiador disponível (avançado só à noite, foco em controle).
   - Sem repetir exercício no mesmo dia. Se o grupo tiver menos de 3 exercícios livres, repita o menos recente com um ÂNGULO novo ("3 ajustes de iniciante", "erros de quem já treina").
   - 3 erros por vídeo que ainda não saíram para aquele exercício no `historico.csv`. Use `catalogo.csv` (não use linhas "não usar" nem natação).
   - `outro.next` de cada vídeo = o exercício do vídeo seguinte; o da noite = o 1º*exercício do tema de depois de amanhã.
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

## B. ÁUDIO (véspera, 23h) — fala por fala, com checagem e refação
1. Pré-checagem e **portão do ÁUDIO**. Traga `pauta.json`, `estado.json` e cada `vN\narration.json`. Se `pauta` = `proposta`, grave `padrao`. Grave `audio:"em_andamento"`. Traga também `audio_falas.py` de `_processo\`.
2. Para cada vídeo sem `vN\audio.json`, **gere as 10 falas separadas** (arquivos curtos: mais rápido, e só a fala ruim é refeita):
   1. `creative_create_flow` (um por vídeo). Para cada fala, `creative_generate_speech` no mesmo `flow_id`: `model_id` `eleven_v4`, `voice_id` `7ete3BaGPf3vlbnyJnJK` (Fernando Nowvaro), `generations_count: 1`, `prompt` = `[energetic] ` + a fala (fala 9: `[excited] ` + a fala). Nunca troque voz, modelo ou marcações (entonação aprovada). Pode disparar as 10 e depois fazer o poll de todas com `creative_get_flow_run_status`.
   2. Baixar: `Claude_Browser__preview_start` com a `content_url` da fala 1; na aba, `Claude_Browser__javascript_tool` baixando todas de uma vez: `const U=[<as 10 content_urls>];const out=[];for(let i=0;i<U.length;i++){const b=await (await fetch(U[i])).blob();const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='vN_'+String(i+1).padStart(2,'0')+'.mp3';document.body.appendChild(a);a.click();out.push(b.size);await new Promise(r=>setTimeout(r,400));}out` (se algum fetch falhar, abra essa URL sozinha com `preview_start` e rode `const r=await fetch(location.href);const b=await r.blob();const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='vN_NN.mp3';document.body.appendChild(a);a.click();({size:b.size})`). `device_list_dir` em `DL` até os 10 arquivos aparecerem com esses tamanhos; `device_stage_files`; copie para `run/vN/falas/01.mp3 … 10.mp3`. Feche a aba.
   3. Ouça o que foi dito: para cada fala, `creative_add_flow_asset_node` (audio, `generation_id`) → `creative_transcribe_audio` (`eleven_scribe_v1`) → poll; monte `run/vN/transcricoes.json` = `{"01":"texto ouvido",…}`. Se o Scribe estiver ocupado, siga sem transcrição (a checagem usa só duração e volume) e registre o aviso.
   4. **Checar:** `python3 audio_falas.py checar run/vN/falas run/vN/narration.json run/vN/transcricoes.json`. Cada fala sai OK ou REFAZER (sem voz, longa demais para a cena mesmo acelerando 1,25×, curta demais, ou falou diferente do roteiro).
   5. **Refazer só as falas reprovadas:** gere de novo apenas essas falas (mesmos parâmetros), baixe, transcreva e cheque de novo. Até **2 refações por fala** (máx. 3 versões). Fala aprovada nunca é refeita. Se depois de 3 versões ainda reprovar, fique com a versão de menos problemas e registre o aviso. Se o ElevenLabs responder "ocupado"/erro sem gerar nada, espere 2 min e tente a mesma chamada de novo (até 3 vezes) — isso não é refação.
   6. **Montar:** `python3 audio_falas.py montar run/vN/falas run/vN/narration.json run/vN/narracao_sync.wav` (cada fala no início da sua cena, sem silêncio nas pontas, acelerada até 1,25× se precisar, 37 s, volume normalizado).
   7. Grave em `pautas\<amanhã>\vN\`: `narracao_sync.wav`, `falas\01..10.mp3`, `falas\qa.json` e `audio.json` = `{"motor":"elevenlabs","creditos":N,"refeitas":["03"],"avisos":[…]}`.
3. Grave `audio:"pronto"` (ou `"pronto_com_avisos"` se algum vídeo ficou com aviso; `"falhou"` se nenhum vídeo tem narração).
4. Mensagem final curta: por vídeo, OK / quais falas foram refeitas / avisos; créditos gastos.
O motor é o ElevenLabs até o Felipe aprovar uma voz do VoiceStudio; quando trocar, só os passos 2.1–2.3 mudam (checar e montar continuam iguais).
