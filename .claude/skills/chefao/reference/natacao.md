# Natação (cenário de piscina)

- Leia `DRIVE\_processo\PISCINA.md`; molde `exemplos\natacao_crawl.episode.json`.
- `episode.json`: `"ambiente":"piscina"` + `"swim":{"stroke":"crawl|costas|borboleta|peito|flutuacao"}`; `anim` = `Swimming.fbx` (flutuação: `Treading Water.fbx`), de `DRIVE\Natacao\`.
- Erros de nado em `errors[i].swim` (parâmetros do boneco vermelho); `deform` continua valendo. Primeiro os erros validados no PISCINA.md; os outros só depois de conferir no still.
- Vistas: `top`, `side_under`, `under_*`, `split*`; nadador deitado pede `zoom` 0.7–0.8 nas laterais. Ajuste `hookView`, `cardView`, `winView`, `outView` (ex.: `split_threequarter`, `split_front`).
- Conteúdo: só técnica consagrada (cabeça, alinhamento, entrada da mão, cotovelo alto, pernada do quadril, respiração). Borboleta = avançado.
