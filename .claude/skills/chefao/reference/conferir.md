# Conferência visual (PRODUÇÃO)

Quem olha é o agente `conferente` (Sonnet). Máx. 4 rodadas por vídeo, 3 por carrossel. Se um erro não ficar legível, troque deform ou vista, nunca o texto.

## Stills do vídeo
`node stills.js "[1.5,5,8.6,12,15,18.2,21.4,24.6,28,31,35]" c1` → folha de contato (PIL, 6×2, 270×480). Olhe:
- erro visível no boneco vermelho e certo no branco; deformação no sentido certo; nenhum membro atravessando outro;
- boneco inteiro no quadro, sem cobrir legenda ou checklist;
- legendas sem estourar.
Boneco fora do quadro: aumente `zoom` (> 1 afasta) ou troque a vista.

## Vídeo final
Duração 37 s; `ffmpeg -i video.mp4 -vf "fps=1/3,scale=216:-1,tile=7x2" -frames:v 1 check.jpg` e olhe; `ffprobe` confirma áudio presente.

## Carrossel
Folha de contato das 5 imagens lado a lado. Avisos "texto estourando": encurte mantendo o sentido. Erro pouco visível: aumente o ângulo ou troque a vista.

## Se algo quebrar
- PAGE ERROR em `stills.js` ou `carrossel.js`: quase sempre JSON inválido ou nome de osso errado.
- Render parou no meio: `node render.js <ini> <fim> parts/pN` só da parte que faltou e refaça a junção do `render_all.sh`.
- Render em piscina leva ~13 min (5 partes em paralelo).
