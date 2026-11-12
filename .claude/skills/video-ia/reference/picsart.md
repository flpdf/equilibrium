# Picsart e Voice Studio: modelos, custos e técnica (medido em 06/11/2026)

## Estilo → modelo
- Fotorrealista, pessoas e animais: Seedance 2.0 (melhor realismo), Veo 3.1 Lite (custo/seg baixo), Kling V3 Turbo.
- Animação infantil 3D pré-escolar: Seedance 2.0 Mini / Kling 4.0 Flash; referência do personagem com Nano Banana 2 ou Seedream.
- Anime, 2D, estilizado: Seedance, Hailuo 2.3, Kling 4.0.
- Rascunho rápido e barato: Seedance 2.0 Mini em 480p, MiniMax H3 Lite.

## Créditos (confirme sempre com `picsart_preflight`)
| Modelo | Config | Créditos |
|---|---|---|
| Seedance 2.0 Mini | 5 s, 480p | 10 |
| Veo 3.1 Lite | 8 s, 720p | 16 |
| Seedance 2.0 Mini / Kling V3 Turbo | 5 s, 720p | 20 |
| Seedance 2.0 | 5 s, 720p | 25 |
| Grok Imagine 1.5 Lite | 6 s, 720p | 30 |
| Veo 3.1 completo | 8 s, 720p | 96 (evitar) |
| Seedance 2.0, 2 clipes (5 + 6 s), 720p, sem áudio | 1 chamada `items` | 55 |
| Imagem (Seedream 5.0 Lite / Nano Banana 2) | 1 imagem | 2–3 |

## Gerar e baixar
- `picsart_generate` (assíncrono; vários clipes = `items`) → `picsart_job_status` com `model` e `batch` até `COMPLETED` → `url`. ~3–5 min para 2 clipes Seedance.
- Nada sobe para o Picsart por comando (403 no proxy, no container e no `device_bash`). Entrada só por `picsart_drive_upload_ask` (o Felipe arrasta o arquivo) ou se já estiver no Picsart Drive (`picsart_drive_list`). Prefira rotas que não precisem subir nada.
- Baixar clipes: Downloads liberada (`device_request_folder_access` `C:\Users\amori\Downloads`, 1x por sessão) + navegador embutido com `gcdn.picsart.com` permitido. `fetch` falha (CORS); funciona `Claude_Browser__navigate` para `<url do mp4>?download=true&download_file_name=<nome>.mp4` (a ferramenta diz "denied or failed", mas o arquivo aparece em Downloads como `<uuid>.tmp`). Um clipe por vez; `device_list_dir`; `device_stage_files`; `ffprobe`.

## Voz (Voice Studio, no PC, lento)
- `generate_speech` só com `text`, `profile_id` e `steps` 12–16. `instruct` e `language` dão 400; o tom vem do perfil.
- Frases curtas (≤ ~8 palavras, ~3 s): longas passam de 60 s e a chamada expira (repetir é grátis). Uma chamada por vez.
- Resultado em `tool-results/…generate_speech-<ts>.txt`: `json.loads(json.load(f)['result'])['wav_base64']` → decodifique, corte silêncio das pontas (`silenceremove` + `areverse`), 48 kHz. Números por extenso.
- Vozes: `list_voices`. Nunca use voz desenhada (`kind: design`) para sotaque brasileiro; só clone BR.

## Montagem (container, ffmpeg)
- Normalize: `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30`, áudio 48 kHz.
- Emende com `xfade` 0,2–0,3 s ou corte seco; narração com a cena de cada fala começando junto (`adelay` + `amix normalize=0`); trilha −18 dB sob a voz (sem trilha, pad de senoides com `tremolo` + `lowpass`); `loudnorm=I=-14:TP=-1.5`.
- Legendas: `.ass` queimado ou texto desenhado (fonte grande, contorno, 2–4 palavras por vez, fora da interface do TikTok/Reels). Fontes: Anton (raw.githubusercontent.com/google/fonts/main/ofl/anton/) e Poppins Bold.
- Misto com o Chefão: renderize o trecho 3D pelo fluxo dele e emende aqui.
