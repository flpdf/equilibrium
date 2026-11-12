# Narração (ÁUDIO)

Regra do Felipe (06/11): sotaque brasileiro nativo. A voz desenhada "Chefão - Narrador" (37415022) foi reprovada; nunca use voz `kind: design` do Voice Studio.

## Motor principal: Voice Studio no PC, pela fila do AlertaSP Iniciador
O que existe (lido do Drive em 12/11): `_fila_voz/LEIA-ME.txt` diz "pedidos `AAAA-MM-DD_*.json` para o `engine/falas.py` (Voice Studio); quem atende é o AlertaSP Iniciador". Os pedidos são consumidos depois de atendidos, então o formato do pedido só está em `C:\AlertaSP\engine\falas.py` no PC. O resultado fica em `_fila_voz/feitos/<id>.result.json` = `{"id","inicio","ok","codigo","saida","fim"}`; a `saida` traz, por fala, versão, nota de transcrição, duração e o texto ouvido, com refação automática até a versão 2 e "falas prontas: N/10" no fim (exemplos em `canais/chefao/_processo/_fila_voz/exemplos/`). Ou seja, o Iniciador já gera, transcreve, pontua e refaz; a etapa ÁUDIO só pede, espera, confere o resultado e monta.
Depois das falas prontas: `python3 audio_falas.py tratar <falas> <tratadas> perfil_voz_chefao.json` (equaliza para o perfil aprovado) e então `montar`.
1. Voz clonada BR (`kind: clone`, nome com "BR"): `Chefão - Narrador BR` se existir (`voicestudio__list_voices`); senão `79c4cf5c` ("AlertaSP - Extra homem jovem BR").
2. Um pedido por vídeo em `DRIVE\_processo\_fila_voz\<AAAA-MM-DD>_chefao_vN.json`, no mesmo formato dos pedidos anteriores da pasta, só trocando a voz. O Iniciador gera as 10 falas, confere e grava em `pautas\<amanhã>\vN\falas\`.
3. Resultado em `_fila_voz\feitos\`. Na execução das 23:07, cheque a cada 3 min por até 20 min; depois encerre o turno. Na execução das 00:07, o que ainda não tiver `falas\` vai direto para a reserva, sem esperar.
4. Refação: pedido com `"refazer": ["03"]` e `"rodada": N`, máximo 2 rodadas.

## Reserva: ElevenLabs (Voice Studio sem resposta na execução das 00:07, ou sotaque reprovado)
- Voz Fernando Nowvaro `7ete3BaGPf3vlbnyJnJK`, modelo `eleven_multilingual_v2`, sem marcações de entonação, `generations_count: 1`, um `creative_create_flow` por vídeo, as 10 falas no mesmo `flow_id`.
- Download pelo navegador embutido para Downloads (pasta conectada) e `device_stage_files`. Script de download em lote: abra a `content_url` da fala 1 com `preview_start` e rode no JS da aba um loop de `fetch` → `blob` → `a.download = 'vN_NN.mp3'`.
- Registre `creditos` no `audio.json`.

## Candidato a teste: edge-tts (gratuito, no container, sem navegador)
`edge-tts --voice pt-BR-AntonioNeural --text "<fala>" --write-media 01.mp3`. Só entra no fluxo depois que o Felipe aprovar a voz em um vídeo de teste.

## Checagem (sempre, qualquer motor)
`python3 scripts/checar_audio.py <pasta_falas> narration.json --saida qa.json`: sem voz, arquivo ausente ou inválido, longa ou curta demais para a cena, ou falou diferente do roteiro = REFAZER. Se o `qa.json` disser `transcricao_pulada: true`, a comparação com o roteiro não rodou: registre o aviso no `audio.json`. Palavras deformadas típicas de sotaque estrangeiro em várias falas = vídeo reprovado, use a reserva.
