---
name: publicacao
description: Etapa D diária, aprovação e agendamento das publicações do dia no TikTok e no Instagram pelo conector vidIQ, para Chefão dos Treinos, Alerta SP e Se Acontecesse. Use na tarefa agendada da manhã ou quando o Felipe pedir para agendar posts.
---

# Publicação do dia (vidIQ)

Regras do Felipe, sempre:
- Nada é agendado sem "ok" dele nesta conversa. Sem resposta, nada é agendado.
- Nunca marcar como conteúdo de IA (TikTok `isAiGenerated: false`; Instagram sem selo).
- Legenda completa e hashtags do kit. Remova só linhas que comecem com "⚠️" ou "TÍTULO:" ou contenham "Postar às" ou "gerado por IA".
- Vídeos já saem com música mixada (`autoAddMusic: false`). Carrosséis do TikTok: `autoAddMusic: true`.
- TikTok: `privacyLevel PUBLIC_TO_EVERYONE`, `allowComment true`, `musicUsageConfirmed true` (aceito em 10/11), `brandContent false`, `brandOrganic false`; carrossel com `title` ≤ 90 caracteres.
- Depois de agendado no vidIQ não dá para cancelar nem editar. Por isso a aprovação antes.
- Contas em `reference/contas.md`; confirme com `vidiq_social_account_list` (`canPublish false`: avise e ofereça reconectar).

## 1. Material de hoje (Google Drive para ids e links; PC para ler e processar)
- Chefão: `G:\Meu Drive\Área de Trabalho\videos-claude\Chefao\Videos-Prontos\<hoje>\`: `HHMM_video_<x>.mp4` + `.txt`; `HHMM_carrossel_<slug>_1..5.jpg` + `.txt`. Sufixo `_sem-narracao`: avise.
- Alerta SP: o `DiaN` mais recente ainda não agendado em `G:\Meu Drive\Área de Trabalho\videos-claude\AlertaSP\Episodios`: `partN.mp4`, `post.md` (Descrição TikTok / Instagram Reels), `fotos.md` (carrossel 1 = `foto_c1_*`, carrossel 2 = `foto_c2_*`, cada um com legenda, hashtags e horário sugerido; story = `foto_story.jpg`).
- Se Acontecesse: o `NNN_slug` mais recente ainda não agendado em `G:\Meu Drive\Área de Trabalho\videos-claude\SeAcontecesse\Episodios`: o `.mp4` final (não `_previa`; prefira `_ig.mp4` para o Instagram se existir) + `post.md`.
- Material ausente ou incompleto na execução das 08:49: encerre o turno; a das 10:49 repete a busca e segue com o que existir, dizendo o que faltou. Pedido de aprovação já enviado e sem resposta: não envie outro; encerre.

## 2. Não repetir
`vidiq_social_post_list` (últimos 30 dias e próximos 70) nas 6 contas. Legenda já agendada ou publicada naquela conta não entra de novo.

## 3. Horários (proposta)
- Chefão, TikTok: 1º item = agora + 20 min (múltiplo de 5); cada seguinte no horário da pauta se ficar ≥ 60 min depois do anterior, senão anterior + 60; nada depois das 23:00. Instagram: mesmo horário, a ≥ 30 min de qualquer post já agendado no Instagram do Chefão (colidiu: + 30).
- Alerta SP, TikTok: vídeo 10:00, carrosséis no horário do `fotos.md` (padrão 12:30 e 18:00), story 21:00. Instagram: o episódio vai para o primeiro dia (hoje ou depois) sem post do Alerta SP agendado, mesmos horários.
- Se Acontecesse: 19:00 nos dois.
- Horário passado ou a < 10 min: agora + 15, mantendo os espaçamentos.

## 4. Aprovação (SendUserMessage, um bloco por projeto, numeração única)
```
📲 Publicações de hoje — <data>
💪 Chefão
1. 🎬 <exercício> · TT 09:10 · IG 09:40 (link)
2. 🖼️ <título> · TT … · IG …
📡 Alerta SP — Dia N (IG em <data>)
7. 🎬 <título> · TT 10:00 · IG …   8. 🖼️ …   10. 📱 story (você posta) TT 21:00 · IG …
🧪 Se Acontecesse
11. 🎬 <título> · TT 19:00 · IG 19:00
Responda "ok", "ok menos 3 e 8", "só tiktok no 5", "não", ou mude horários ("o 2 às 14h").
```
Encerre o turno e espere.

## 5. Quando ele responder: só o aprovado, horários refeitos a partir da hora da resposta
a) Mídia no vidIQ, uma vez por arquivo (guarde os ids). Vídeo: `vidiq_video_upload` com `https://drive.usercontent.google.com/download?id=<ID>&export=download&confirm=t` (erro de Content-Length = arquivo privado ou link recém-liberado: `get_file_permissions`; sem "anyone", não mude permissões, peça; com "anyone", espere 30 s e tente de novo). Imagem: `vidiq_upload_image` com `https://lh3.googleusercontent.com/d/<ID>=s0`.
   - Instagram recusa vídeo > 100 MB: `device_stage_files`, `ffmpeg -c:v libx264 -preset veryfast -b:v <para ~90 MB> -c:a aac -b:a 192k -movflags +faststart`, `SendUserFile` + `device_commit_files` como `<nome>_ig.mp4` ao lado do original; espere aparecer no Drive. TikTok usa o original.
   - Instagram recusa imagem 9:16 em carrossel: converta para 1080×1350 (PIL: fundo = a própria imagem em cover com GaussianBlur 40 e brilho 0,35; a imagem inteira centralizada por cima). Grave como `<nome>_ig45.jpg` na pasta `_instagram-4x5` do projeto e suba pelo lh3. TikTok usa as originais.
b) `vidiq_social_post_draft_create`: um rascunho por post com os destinos aprovados, cada um com `publishAt` (ISO com `-03:00`) e a sua mídia. Legenda: Chefão = `.txt`; Alerta SP vídeo = Descrição TikTok (TT) e Instagram Reels (IG); Alerta SP carrossel = Legenda + Hashtags do `fotos.md`; Se Acontecesse = Legenda TikTok / Instagram do `post.md`. Todo destino precisa de `publishAt` (sem ele publica na hora; confira `scheduledFor`). Destino `refused`: corrija com `vidiq_social_post_draft_update` e só siga com `ready: true`.
c) `vidiq_social_post_publish` com `postId` e a revisão mais recente. A aprovação já cobre isso.
d) Stories (Alerta SP): o vidIQ não publica story. Crie um lembrete (`send_later`) 5 min antes de cada horário com o link do `foto_story.jpg`, o texto opcional do `fotos.md` e "sem selo de IA".

## 6. Fim
Mensagem curta: por item, `TT <hora> · IG <hora>` ou "não agendado: motivo", e os avisos.
