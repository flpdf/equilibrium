---
name: alerta-sp
description: Rotina diária da série "Alerta SP" (SP OFFLINE), história em capítulos com vozes do Voice Studio, renderizada no PC do Felipe pelo "AlertaSP Iniciador". Etapa A (briefing, roteiro, plano de fotos) e etapa B (produção pela fila). Use na tarefa agendada ou quando o Felipe pedir um episódio.
---

# Alerta SP

O processo detalhado ainda mora no PC: `C:\AlertaSP\ROTINA.md` (o QUANDO e o QUE: etapas, vozes, qualidade, fotos) e `C:\AlertaSP\CLAUDE.md` (o COMO). Traga os dois com `device_stage_files` e siga; onde divergirem, vale a ROTINA.md. Esta skill só fixa a mecânica da fila, que é o que mais erra. Fale em português do Brasil; siga sem travar.

## Onde fica
- Projeto: `C:\AlertaSP`. `device_bash` enxerga em `$HOME/mnt/<pasta>`; `device_list_dir`, `device_stage_files` e `device_commit_files` usam o caminho do Windows.
- O terminal do `device_bash` é um Linux separado: sem GPU, Chrome, Voice Studio ou internet do Windows. Nunca rode `voice.py`, `render.py`, `sound.py` ou `encode.py` nele. Quem roda é o Iniciador, pela fila.
- Episódios prontos: `G:\Meu Drive\Área de Trabalho\videos-claude\AlertaSP\Episodios\DiaN` (o Iniciador copia).

## A fila (como pedir uma etapa ao Windows)
1. Iniciador vivo? `C:\AlertaSP\_fila\runner_vivo.json`, campo `now` com menos de 2 min sem pedido em andamento. Parado há mais de 5 min: avise o Felipe ("rode a tarefa 'AlertaSP Iniciador' no Agendador de Tarefas") e encerre o turno.
2. Pedido: grave `C:\AlertaSP\_fila\<id>.json.tmp` e renomeie para `<id>.json` (`mv` no `device_bash`). O `<id>` começa com a data (`AAAA-MM-DD_partN_<nome>`), senão o Iniciador ignora.
   ```json
   {"id": "<AAAA-MM-DD>_partN_<nome>", "part": "partN", "steps": [{"do": "voice"}, {"do": "stills", "at": [...], "out": "stills"}, {"do": "sound"}, {"do": "render"}, {"do": "encode"}, {"do": "cover"}, {"do": "fotos"}, {"do": "deliver"}, {"do": "clean"}]}
   ```
   `{"do":"voice","engine":"kokoro"}` força a voz de reserva. As etapas rodam em ordem e param na primeira que falhar.
3. Resultado em `C:\AlertaSP\_fila\feitos\<id>.result.json` (log em `<id>.log`). Leia sempre a saída. Cheque a cada 1 a 3 min; espera longa: `send_later` de 10 min. Este canal ainda não foi migrado para horários fixos porque o processo roda no PC; `send_later` é permitido aqui.

## Etapas
- **A (17:47)**: briefing com o Felipe (votação, comentários, rumo da história, pedidos para as fotos); espera de até 2 h; `story.md`, `lines.json` (uma voz por personagem do `vozes.json`), `fotos.md`; `estado.json` `roteiro: pronto`; resumo curto.
- **B (02:30, via `send_later` da etapa A)**: portões (Chefão terminou, roteiro pronto, Iniciador vivo). Portão fechado: `send_later` de 60 min, no máximo até 06:00; depois disso produza sem esperar o Chefão e avise. Então voz, `film.html`, stills, som, render, encode, capa, fotos, entrega; mensagem final com vídeo, capa, 5 fotos, kit de post e legendas das fotos.
Se algo der errado e não resolver: diga em qual etapa parou e o que falta.
