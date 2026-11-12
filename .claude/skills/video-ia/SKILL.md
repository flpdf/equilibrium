---
name: video-ia
description: Vídeo avulso com IA generativa (Picsart para imagem e vídeo, Voice Studio para voz), em qualquer estilo: realista, animação infantil, anime, produto a partir de foto, misto com o boneco 3D do Chefão, ou correção de um vídeo existente. Use quando o Felipe pedir um vídeo que não é de nenhum canal diário.
---

# Vídeo com IA (Picsart + Voice Studio)

Entregar o melhor vídeo para o pedido com o menor gasto de créditos. Seja honesto na rota: se IA de vídeo não for o melhor caminho (texto na tela, gráfico exato, personagem idêntico por 1 min, orçamento curto), diga e proponha a alternativa (motor 3D do Chefão, montagem com imagens, misto).

## Pré-checagem
1. `get_device_info`: `localMcpServers` precisa listar `picsart` e `voicestudio` como `announced`. PC offline: "Computador offline. O Picsart e o Voice Studio rodam pelo app do Claude no seu PC."
2. `picsart_credits`: anote o saldo (~247/mês no plano atual).
3. Ferramentas: `mcp__remote-devices__picsart__*` e `mcp__remote-devices__voicestudio__*` (ToolSearch, uma chamada).

## Rota (explique em 2–3 linhas qual e por quê)
| Rota | Quando | Como |
|---|---|---|
| A. Picsart só | Clipe curto com fala sincronizada com a boca; cena única | Seedance 2.0 / Veo 3.1 Lite / Kling V3 Turbo com `generateAudio: true`, fala em PT-BR no prompt |
| B. Picsart + Voice Studio em off (padrão para narração) | Vídeo narrado, voz igual em todos os episódios | Cenas sem fala + narração no Voice Studio + montagem no container |
| C. Lip-sync com voz do Voice Studio | Personagem falando para a câmera com voz fixa | Seedance 2.0/2.5, MiniMax H3, Wan 2.7/3.0, LTX 2.3 (`audioUrl`); exige subir áudio |
| D. Misto | Gancho realista + corpo em 3D, ou clipe de IA numa cena do Chefão | Gere só os trechos de IA e encaixe na montagem |
| E. Correção de vídeo existente | Trocar objeto/estilo, reenquadrar, estender, refazer uma cena | FLUX Video Edit (até 15 s), Kling 4.0 Omni, Wan 2.7 Ref-to-Video, `picsart_media_reframe_video` |
| F. Produto a partir de foto | Produto real com rótulo intacto | Recorte + vetor locais + cenários IA vazios + composição (`reference/produto.md`) |

Estilo → modelo, custos e parte técnica em `reference/picsart.md`. Antes de usar um modelo pela primeira vez: `picsart_model_params`.

## Orçamento (regra dura)
`picsart_preflight` antes de toda geração. Mostre o total estimado se passar de 40 créditos ou 25% do saldo; em execução agendada, não passe disso sem ok prévio. Fluxo econômico: imagem de referência → 1 clipe de teste em 480p → clipes finais. Vários clipes = uma chamada com `items` (até 10). Geração que "travou" provavelmente rodou e cobrou: `picsart_job_status`, nunca reenviar.

## Fluxo
1. Roteiro em cenas (nº, duração 5–8 s, o que se vê, câmera, fala, rota). Vertical 9:16, entrega 1080×1920.
2. Consistência: folha do personagem (frente/perfil, fundo neutro) com modelo de imagem, salva no Picsart Drive em `Videos-IA/<projeto>` (`folderUid` em toda geração), URL em `imageUrls` de todas as cenas. Personagens sempre originais, nunca de marcas conhecidas.
3. Prompt em inglês, falas em PT-BR entre aspas: sujeito + uma ação + cenário + câmera + luz + estilo + duração. `negativePrompt` para texto embutido, marca d'água, mãos deformadas. Sem texto escrito dentro do vídeo de IA.
4. Montagem no container (`reference/picsart.md` § Montagem).
5. Conferência: `ffmpeg -i final.mp4 -vf "fps=1/2,scale=216:-1,tile=6x3" -frames:v 1 check.jpg` e olhe (rosto e mãos, personagem mudando, texto na imagem, produto flutuando, corte brusco); `ffprobe` (duração, 1080×1920, áudio). Cena ruim: refaça só ela, no máx. 2 vezes.
6. Entrega: pasta do projeto no PC (sugestão `G:\Meu Drive\Área de Trabalho\Videos-Claude\Videos-IA\<projeto>\`; sem acesso, `C:\Users\amori\Downloads\<projeto>\`): `final.mp4`, `legenda.txt` (gancho + chamada para comentar + hashtags; sem aviso de IA), `projeto.json` (roteiro, modelos, prompts, URLs, voz, créditos). `SendUserFile` do vídeo. Mensagem final: o que foi feito, rota, créditos gastos e saldo, avisos.

## Conteúdo
Nada de personagens, logos ou visual de terceiros (exceção: produto que o Felipe revende, foto real sem alterar rótulo); nada de pessoas reais; voz clonada só com consentimento. Infantil: sem sustos, violência ou comportamento perigoso imitável. Academia, saúde e suplemento: sem promessa de resultado, números de carga, conselho médico ou alegação terapêutica.
