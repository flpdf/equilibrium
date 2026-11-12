# Impulsionamento de vídeos (ads)

Objetivo: pegar os posts que já deram sinal orgânico nas últimas 24 h e colocar um orçamento pequeno neles, buscando visualizações, seguidores e retorno. A decisão é por regras (`scripts/impulsionar.py`, testável e sem rede); a execução é por API, em modo seguro.

## Como a decisão funciona

1. Só entram posts publicados dentro de `janela_horas` (24 h).
2. Taxa de engajamento = (curtidas + comentários + compartilhamentos + salvos) / views. O post precisa de `views_min` (1000) e `taxa_engajamento_min` (4%).
3. O post precisa estar no percentil 80 de views entre os posts do mesmo canal e plataforma na janela. Com menos de 3 posts no grupo, só valem os mínimos.
4. Ficam de fora: tag em `nunca_impulsionar`, plataforma ou canal inativo, e post que já foi impulsionado (consta em `ativos`, `criados` ou `gasto_por_post`).
5. Pontuação = z-score de views no grupo x peso do canal + taxa de engajamento x 10.
6. Limites: `max_posts_por_dia` (descontando o que já foi criado hoje) e o que sobra dos orçamentos diário e semanal (o menor dos dois). O dia é o de Brasília.
7. O que sobra é dividido entre os melhores proporcionalmente à pontuação, em múltiplos de R$ 5, entre o mínimo e o máximo por post. Se alguém ficar abaixo do mínimo, sai o de menor pontuação e a conta é refeita.

O `orcamento` de cada decisão é o total do post na duração toda (`duracao_dias`). Nas plataformas vira orçamento diário (total / dias) e conta no gasto do dia da criação.

Parada: `avaliar` (função `avaliar_ativos`) lista os ativos com CPM acima de `parar_se.cpm_max` ou, no Instagram (objetivo seguidores), custo por seguidor acima de `custo_por_seguidor_max` (gasto acima do limite sem nenhum seguidor também conta). A parada em si é manual por enquanto.

Os valores ficam em `config/ads.json`. Ajuste lá; comece conservador.

## Uso

```
python3 scripts/impulsionar.py decidir metricas.json historico_ads.json [--agora ISO]   # tabela + decisoes.json
python3 scripts/impulsionar.py executar decisoes.json                                    # dry-run (padrão): imprime os payloads
python3 scripts/impulsionar.py executar decisoes.json --plataforma tiktok --executar --confirmo   # cria de verdade
python3 scripts/impulsionar.py avaliar historico_ads.json                                # quem deveria parar
```

Sem `--executar --confirmo` nada é enviado. Mesmo com confirmação, campanha, conjunto e anúncio nascem PAUSADOS: você revisa e ativa no Ads Manager.

Em `metricas.json`, cada post pode ter `midia_id` (ID da mídia do reel no Instagram, necessário para a Meta) e `auth_code` (código Spark Ads, necessário para o TikTok). A decisão carrega esses campos em `extra`.

## O que o Felipe cria uma única vez

### Meta (Instagram)
1. Conta Meta Business (business.facebook.com) com a Página e o perfil do Instagram profissional ligados a ela.
2. Conta de anúncios com método de pagamento. O ID tem formato `act_123...`.
3. App em developers.facebook.com, tipo Business, com o produto Marketing API. Permissões: `ads_management`, `pages_read_engagement`, `instagram_basic`. Para uso só na própria conta basta o modo de desenvolvimento.
4. Token de longa duração: gere um usuário do sistema no Business Manager, atribua a conta de anúncios, a Página e o Instagram a ele e gere o token com essas permissões (token de usuário do sistema não expira). Token de usuário comum dura cerca de 60 dias.

### TikTok
1. Conta TikTok for Business / Ads Manager, com método de pagamento.
2. App em business-api.tiktok.com (TikTok for Developers) com a permissão `ads.manage`; gere o `access_token` da conta de anúncios e anote o `advertiser_id`.
3. Código de autorização Spark Ads, em cada vídeo: no app do TikTok, abra o vídeo, toque nos três pontinhos, depois em configurações de anúncio, ative "Autorização de anúncio" e gere o código (ele tem validade que você escolhe, por exemplo 30 dias). Copie o código para o campo `auth_code` do post em `metricas.json`. Sem o código o TikTok não executa.

## Variáveis de ambiente (segredos do ambiente)

| Variável | Para quê |
|---|---|
| `META_ACCESS_TOKEN` | token de longa duração |
| `META_AD_ACCOUNT_ID` | `act_123...` |
| `META_PAGE_ID` | ID da Página |
| `META_IG_USER_ID` | ID da conta profissional do Instagram |
| `TIKTOK_ACCESS_TOKEN` | token da Marketing API |
| `TIKTOK_ADVERTISER_ID` | ID do anunciante |

Libere na rede do ambiente: `graph.facebook.com` e `business-api.tiktok.com`.

## Como ler `historico_ads.json`

```
{"gasto_por_dia":  {"2026-11-12": 25.0},   # soma dos orçamentos criados naquele dia (R$)
 "gasto_por_post": {"ch-ig-4": 15.0},      # impede impulsionar o mesmo post duas vezes
 "criados": [...],                          # diário: um registro por criação, com ids da plataforma
 "ativos":  [...]}                          # o que o `avaliar` vigia
```

Cada registro tem `post_id`, `plataforma`, `canal`, `orcamento`, `duracao_dias`, `criado_em` e `ids` (campanha, conjunto, criativo e anúncio na Meta; item, campanha, grupo e anúncio no TikTok). Os ativos também têm `gasto`, `impressoes` e `seguidores_ganhos`, que precisam ser atualizados com os números reais antes de rodar `avaliar`. Isso ainda é manual (ver limitações). `gasto_por_dia` registra o orçamento comprometido, não o gasto medido.

## Limitações (honestamente)

- O botão "Promover" do app do TikTok não tem API. O caminho automatizável é Spark Ads, que exige o código de autorização por vídeo, gerado por você. Não dá para impulsionar um vídeo sem ele.
- Os payloads seguem as documentações das Marketing APIs (Meta v21.0, TikTok v1.3), mas foram escritos sem acesso às contas. Valide no primeiro uso com `--executar --confirmo` num post só, tudo pausado, e confira no Ads Manager. Pontos mais prováveis de ajuste: `optimization_goal` da Meta para seguidores (`PROFILE_VISIT`) e para views (`THRUPLAY`), o formato de `creative` com reel existente, e `optimization_goal`/`billing_event` do TikTok.
- Os orçamentos diários resultantes (por exemplo R$ 5 por dia) podem ficar abaixo do mínimo diário que a plataforma aceita; nesse caso a API devolve erro e o script mostra a mensagem.
- Nada coleta métricas de anúncios nem para campanhas sozinho: `metricas.json` e os números dos `ativos` vêm de fora (vidIQ, Windsor, exportação).
- "Retorno financeiro" não é medido aqui: os vídeos não vendem direto, então a regra otimiza views e seguidores e limita o custo (CPM, custo por seguidor).


Tutorial passo a passo da Meta (Instagram), com telas, ids e testes: `docs/tutorial-meta-ads.md`.
