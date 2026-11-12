# Formato da pauta (`DRIVE\_processo\pautas\AAAA-MM-DD\`)

```
pauta.json            resumo do dia
estado.json           portões
v1\ v2\ v3\           episode.json, narration.json, legenda.txt (+ depois do ÁUDIO: narracao_sync.wav, audio.json, falas\)
c1\ c2\ c3\           carrossel.json, legenda.txt
```
Valide sempre com `python3 scripts/validar_pauta.py <pasta>`.

## pauta.json
```json
{"data":"2026-11-06","dia":"sex","tema":"DIA DE CORE","status":"proposta",
 "videos":[{"id":"v1","slot":"manha","postar":"07:00","nivel":"base","exercicio":"Prancha","arquivo":"Plank.fbx","pasta":"Core",
            "erros":["quadril caindo","quadril alto","cabeça caindo"],"gancho":"Sua prancha tá te enganando?"}],
 "carrosseis":[{"id":"c1","postar":"09:30","tipo":"erros","titulo":"4 ERROS QUE TRAVAM SEU ABDÔMEN","itens":["…","…","…","…"]}],
 "vendas":0,"ajustes":[]}
```
`status`: proposta → aprovada (Felipe respondeu) ou padrao (sem resposta) → produzida. Vendas desligadas: vídeo de venda nunca sai sem "ok" explícito.

## Vídeo: formato fixo de 37 s, 30 fps
gancho → cartão "Seleção de desafio" → 3 erros (boneco vermelho errado → corte → boneco branco certo) → "desbloqueado" → "Chefão carregando…" → tela de comentário (sem voz).

### episode.json (molde: `exemplos\*.episode.json`; PT-BR; textos de tela em MAIÚSCULAS)
- `anim`, `peak` `{"bone","metric"}` do catálogo; `watermark`; `topbar.left` (ex: `VOCÊ · "SÓ UMA SÉRIE"`), `topbar.right` (ex: `CHEFÃO DO OMBRO`).
- `card.name`: 1–2 linhas ≤ 12 caracteres. `card.rows`: 3 linhas `[rótulo, valor, "r" opcional]`: MÚSCULOS, NÍVEL (★☆), RISCO.
- `captions`: EXATAMENTE 11: gancho A, gancho B, cartão A, cartão B, erro1, correção1, erro2, correção2, erro3, correção3, desbloqueado. Cada item = lista de `[palavras, cor]` com cor `""`, `"r"`, `"g"`. Máx. ~4 blocos e ~24 caracteres.
- `errors`: 3 itens `{label, check, view, zone, deform, [always], [static], [lift], [zoom], [arrows]}`. `label` curto; `check` ≤ 20 caracteres; `view` ∈ front, front_low, high_front, top_front, threequarter, side, side_left, low_side, back; `zone` = ossos sem `mixamorig` (Hips, Spine, Spine1, Spine2, Neck, Head, Left/Right Arm, ForeArm, Hand, UpLeg, Leg, Foot, ToeBase); `deform` = `{bone, axis, angle (rad), mirror}`; `always` = erro o tempo todo; `static` = isométrico; `lift` cm; `zoom` < 1 aproxima (deitados 0.8); `arrows: "out"`.
- Cenas com objeto (esteira, bicicleta, saco de pancada): copie o `exemplos\<cena>.config.json` validado (`props`, `modelOffset`, `lockRoot`, `baseDeform`, `pedal`); crédito do `CREDITOS.txt` na legenda.
- `hookView`/`hookZoom` opcionais (deitados 0.8; capoeira 0.75). `outro.next` = exercício do vídeo seguinte (o da noite = 1º do tema de depois de amanhã). `outro.percent` 20–80. `cta.cards` = 3 sugestões `[nome com \n, "GRUPO · ★★★☆☆"]`, de preferência os próximos da trilha.

### narration.json
`{"lines":[10 falas]}`: gancho (0–3,4 s), cartão (3,4–7,2 s), erro1, correção1, erro2, correção2, erro3, correção3, "Pronto. <Exercício> desbloqueado!", "Segue aí, que o próximo chefão é <outro.next>." Até 45 caracteres (falas 2 e 10 até 55). Números por extenso. Termina com `.` `!` `?`. Ritmo: gancho em pergunta curta; "Erro um/dois/três: <problema>."; correções no imperativo.

### legenda.txt (vídeo)
1 linha de gancho + pergunta para comentar + 6–8 hashtags (#academia #treino #musculacao #dicasdetreino #fitness + 1–3 do exercício). Só o texto que vai ao ar: sem "⚠️", sem "Postar às", sem "gerado por IA". O horário fica no `pauta.json` e no nome do arquivo.

## Carrossel: 5 imagens (molde: `exemplos\erros.carrossel.json`)
Slides 1–4 = os 4 itens (o 1 leva o título), slide 5 = pedido de comentário com o boneco.

### carrossel.json
- `id`, `cor` de destaque: `r` (erros), `y` (curiosidades/cultura), `g` (treino/mito).
- `titulo`: até 2 linhas de ~22 caracteres; cada linha é texto ou `[texto, cor]`.
- `slides`: EXATAMENTE 4.
  - `erro`: `{"tipo":"erro","kicker":"CHEFÃO DA PERNA","nome":"AGACHAMENTO","anim":"Air Squat.fbx","peak":{…},"erro":{view, zone, deform, always, static, lift, zoom},"errado":"JOELHO PRA DENTRO","certo":"JOELHOS NA LINHA DOS PÉS"}` (+ `cfg` se a cena tiver objeto). `nome` ≤ 14; `errado`/`certo` ≤ 28.
  - `info`: `{"tipo":"info","tag":"CURIOSIDADE #1","titulo":[linhas],"anim":"…fbx","view":"threequarter","zoom":1,"pose":"pico|repouso","texto":"frase com **destaque**","tagcor":"r|g|y"}`. `titulo` até 2 linhas de ~18; `texto` ≤ 140. Mito/verdade: `tagcor` `r` para MITO, `g` para VERDADE. Pose parada: `Fitness Idle.fbx` (Base-Aquecimento).
- `cta` opcional: `{"pergunta":[linhas],"sub":"COMENTA AÍ","botao":"SEGUE P/ DESBLOQUEAR","anim":"Fitness Idle.fbx"}`. `arrasta` opcional: rodapé.

### legenda.txt (carrossel)
2–3 frases convidando a arrastar e comentar + 6–10 hashtags. Sem linha "TÍTULO:", sem "⚠️", sem "Postar às".

## Animações que não funcionam em vídeo
- `Pike Walk.fbx`: só em carrossel.
- `Swimming Breaststroke.fbx`: não use; nado peito sai de `Swimming.fbx` com `"stroke":"peito"`.
