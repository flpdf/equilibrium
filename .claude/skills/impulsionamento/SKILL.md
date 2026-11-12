---
name: impulsionamento
description: Gerenciador diário de impulsionamento (ads) dos vídeos publicados no TikTok e no Instagram: lê o desempenho das últimas 24 h, decide por regras o que impulsionar e com quanto, executa pela API da Meta e do TikTok (Spark Ads), e para o que não rende. Use na tarefa agendada ou quando o Felipe pedir para impulsionar, pausar ou revisar anúncios.
---

# Impulsionamento

Metas: visualizações, seguidores e retorno financeiro, com orçamento fixo e regras em `config/ads.json`. A decisão é código (`scripts/impulsionar.py`); o modelo só coleta métricas, executa e relata. Detalhes de contas, chaves e limites em `docs/impulsionamento.md`.

## Pré-checagem
- Segredos do ambiente: `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID` (Página e Instagram por canal em `config/ads.json`), `TIKTOK_ACCESS_TOKEN`, `TIKTOK_ADVERTISER_ID`. Faltando um par: a plataforma correspondente roda só em `--dry-run` e você avisa.
- Rede: `graph.facebook.com` e `business-api.tiktok.com` liberados.
- `config/ads.json` existe e `orcamento_diario_total` > 0. Com 0, a tarefa só relata.

## Execução (duas vezes por dia)
1. **Métricas** das últimas `janela_horas` nas 6 contas: `vidiq_social_post_list` + `vidiq_social_post_status` para os posts agendados pela skill `publicacao`; complemento de views, likes, comentários, compartilhamentos e salvos pelo Metricool (`getAnalyticsDataByMetrics`) quando o vidIQ não trouxer. Grave `run/metricas.json` no formato que o script espera (lista de posts com `id, canal, plataforma, url, publicado_em, views, likes, comentarios, compartilhamentos, salvos, seguidores_ganhos, tags`). Tags: `venda` para posts de venda, `suplemento` para produto.
2. **Ativos**: traga `historico_ads.json` do Drive (`Videos-Claude\_ads\historico_ads.json`; crie se não existir) e, para cada impulsionamento ativo, o gasto, impressões e seguidores ganhos pela API (Meta Insights, TikTok report). Grave em `run/ativos.json`.
3. **Parar**: `python3 scripts/impulsionar.py avaliar historico_ads.json` lista os ativos que estouraram `cpm_max` ou `custo_por_seguidor_max`. A pausa pela API ainda não está implementada: pause pelo Gerenciador de Anúncios e liste na mensagem ao Felipe os que devem parar.
4. **Decidir**: `python3 scripts/impulsionar.py decidir run/metricas.json historico_ads.json` → `decisoes.json`. Leia a tabela. Só intervenha se um post decidido violar as regras de conteúdo do canal (então remova-o do `decisoes.json` e registre o motivo).
5. **Executar**: `python3 scripts/impulsionar.py executar decisoes.json --executar --confirmo` (sem as duas flags é dry-run e só imprime os payloads). Tudo nasce pausado na plataforma; ative no Gerenciador depois de conferir. Instagram exige o `midia_id` do reel; TikTok exige o `auth_code` do Spark Ads gerado no app. Sem um deles, a decisão fica pendente e entra na mensagem ao Felipe.
6. **Registrar**: grave `historico_ads.json` atualizado no Drive e uma linha por ação em `Videos-Claude\_ads\log.csv` (`data;plataforma;canal;post;acao;orcamento;motivo`).
7. **Mensagem** curta: impulsionados (post, plataforma, R$, motivo), pausados (motivo), pendentes de código Spark, gasto do dia e da semana contra o teto.

## Regras fixas
- Nunca impulsione post com tag em `nunca_impulsionar`, nem vídeo de venda sem "ok" explícito do Felipe.
- Nunca ultrapasse `orcamento_diario_total` nem `orcamento_semanal_total`. Em dúvida sobre o gasto já feito, não crie nada e avise.
- Nunca marque anúncio como conteúdo de IA. Nunca edite o post original.
- Sem métricas confiáveis (vidIQ e Metricool fora), a execução só relata.
