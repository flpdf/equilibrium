---
name: tendencias
description: Passo zero da PAUTA de qualquer canal. Consulta o vidIQ (vídeos fora da curva no Instagram e TikTok, buscas em alta) e, se disponível, o Google Trends, e grava tendencias.json com o tema escolhido para o dia. Use dentro da etapa PAUTA ou quando o Felipe perguntar o que está em alta no nicho.
---

# Tendências: o tema do dia vem do que está crescendo

Meta: visualizações, seguidores e retorno. A trilha fixa (`grade.json`, `temas.csv`) vira reserva; o tema do dia sai do que está performando no nicho nos últimos 30 dias. Quem executa é o agente `pesquisador` (Haiku). Configuração em `config/tendencias.json`.

## Fontes, em ordem
1. `vidiq_instagram_tiktok_outlier_search` com cada consulta do canal (`consultas`) e o `publico` do canal como `audienceQuery`, `descriptionLanguage: ["pt"]`, `resultsPerPlatform: 5`. Fonte principal: traz gancho, formato, views e múltiplo da mediana de cada criador. 5 créditos por chamada.
2. `vidiq_keyword_research` em `mode: rising`, `language: pt`, `period: week`, com `nicho_rising`. Pode voltar vazio em português; não insista. 5 créditos.
3. Google Trends (`pytrends`, `geo: BR`, `now 7-d`) só se a rede permitir (`trends.google.com`); grátis. Falhou: ignore.
Respeite `creditos_vidiq_max_por_canal_dia`. Nunca repita uma chamada que falhou.

## Como virar pauta
1. De cada outlier, extraia: tema (em uma frase), grupo ou categoria do canal, gancho (texto dos 3 primeiros segundos), formato (ex.: errado × certo lado a lado), views e múltiplo da mediana.
2. Agrupe por tema. Pontuação = `pesos.outliers` × (nº de outliers do tema / máximo) + `pesos.multiplo_mediana` × (maior múltiplo / máximo) + `pesos.crescimento_busca` × (crescimento da busca normalizado, 0 se não houver).
3. Só é elegível o tema que: cabe no catálogo do canal (Chefão: um exercício do `catalogo.csv` sem "não usar"; Se Acontecesse: um "E se…" verificável com fonte), passa nas regras de conteúdo do canal, e não saiu nos últimos 7 dias do `historico.csv`.
4. Escolha o maior. Sem tema elegível com pelo menos `minimo_outliers_para_escolher` outliers e `multiplo_mediana_min`: use a reserva (`fallback`) e registre o motivo.
5. Ganchos e formatos são inspiração de estrutura, nunca cópia de texto, personagem ou identidade visual.

## Saída: `tendencias.json` na pasta da pauta
```json
{"data":"2026-11-13","canal":"chefao","creditos_vidiq":10,"fontes":["outliers_ig_tiktok","rising"],
 "candidatos":[{"tema":"elevação lateral: 3 erros que travam o ombro","grupo":"ombro","exercicio":"Lateral Raise.fbx",
   "sinais":{"outliers":2,"views_max":1000000,"multiplo_mediana":10.7,"crescimento_busca":null},
   "pontuacao":0.82,"ganchos":["TEU OMBRO não alarga porque…"],"formato":"errado × certo, boneco animado","urls":["…"]}],
 "escolhido":"elevação lateral: 3 erros que travam o ombro","origem":"tendencia|reserva","motivo":"2 outliers no IG acima de 10× a mediana; não saiu em 7 dias"}
```
Também acrescente ao `tendencias.json` uma lista `ganchos_do_dia` com até 3 ganchos reescritos no tom do canal, para o `roteirista` usar.
