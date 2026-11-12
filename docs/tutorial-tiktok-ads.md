# Tutorial: preparar o TikTok para o impulsionamento automático (Spark Ads)

Resumo honesto: o TikTok é mais simples que a Meta em contas e tokens, e mais chato em um ponto: o app de desenvolvedor passa por uma aprovação que leva de um a alguns dias úteis, e cada vídeo impulsionado precisa de uma autorização sua. Ao final você terá dois segredos:

| Segredo | O que é | Onde pegar |
|---|---|---|
| `TIKTOK_ACCESS_TOKEN` | token do app de desenvolvedor, de longa duração | Passo 4 |
| `TIKTOK_ADVERTISER_ID` | id da conta de anúncios, só números | Passo 1 |

Os nomes dos menus mudam; quando não bater, procure o equivalente na mesma tela.

## Passo 1. Conta de anúncios (Ads Manager)

1. Entre em https://ads.tiktok.com e crie uma conta TikTok for Business com o seu e-mail. País Brasil, moeda BRL, fuso América/São Paulo. Escolha o modo **Personalizado** (Custom), não o Simplificado.
2. Em **Faturamento** (Billing), adicione cartão ou Pix.
3. O **ID do anunciante** aparece no canto superior, ao lado do nome da conta, e em Configurações da conta. É um número longo. Esse é o `TIKTOK_ADVERTISER_ID`.
4. Contas novas podem ficar "em análise" por um dia. Não bloqueia os próximos passos.

## Passo 2. Business Center com as suas contas do TikTok

1. Entre em https://business.tiktok.com e crie um Business Center (se o Ads Manager ainda não criou um).
2. **Ativos → Contas de anúncios**: adicione a conta do Passo 1 (pedir acesso ou vincular como proprietário).
3. **Ativos → Contas TikTok** (ou "Identidades"): clique em adicionar e autorize cada um dos três perfis (@chefaodostreinos, @spoff.line, @eseacontecessse). A autorização é feita escaneando um QR code com o app do TikTok logado naquele perfil. Isso vincula o perfil ao Business Center e permite usar os vídeos dele em Spark Ads.
4. Confira que o seu usuário tem papel de **Administrador** no Business Center e acesso de **Operador** na conta de anúncios.

## Passo 3. App de desenvolvedor (TikTok for Business Developers)

1. Entre em https://business-api.tiktok.com/portal com a mesma conta e registre-se como desenvolvedor (nome, empresa, finalidade: "gerenciar anúncios das minhas próprias contas").
2. **Meus apps → Criar app**. Nome `impulsionamento-videos`. Descrição curta e verdadeira: "cria e pausa Spark Ads a partir de vídeos publicados nos meus perfis, com orçamento por regras".
3. **Advertiser redirect URL**: qualquer endereço seu; pode ser `https://localhost/callback`. Você vai só copiar um código dessa URL depois.
4. **Escopos de permissão** (Scopes of permission): marque
   - Ad Account Management
   - Ads Management (campanhas, grupos, anúncios)
   - Creative Management
   - Reporting
   - TikTok Account Management / Identity, se aparecer (é o que liga aos perfis do Passo 2)
5. Envie para aprovação. O portal mostra o status; costuma levar de 1 a 3 dias úteis. Até lá, o resto pode ficar pronto.

## Passo 4. Autorizar o app e pegar o token

Depois de aprovado:

1. Na página do app, copie a **URL de autorização** (Authorization URL). Abra no navegador logado na conta do Ads Manager.
2. Selecione a conta de anúncios e confirme. O navegador é redirecionado para a sua redirect URL com `auth_code=...` na barra de endereço. Copie o `auth_code` (vale 1 hora).
3. No PC, troque o código pelo token. Substitua `APP_ID`, `SECRET` (os dois estão na página do app) e o código:
   ```
   curl -X POST "https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/" \
     -H "Content-Type: application/json" \
     -d '{"app_id":"APP_ID","secret":"SECRET","auth_code":"CODIGO"}'
   ```
4. A resposta traz `access_token` e a lista `advertiser_ids`. O token da Marketing API é de longa duração: não expira por tempo, só se você revogar a autorização ou apagar o app. Esse é o `TIKTOK_ACCESS_TOKEN`.

## Passo 5. Conferir

```
curl "https://business-api.tiktok.com/open_api/v1.3/advertiser/info/?advertiser_ids=[\"SEU_ADVERTISER_ID\"]" \
  -H "Access-Token: SEU_TOKEN"
```

Deve devolver `"code":0` e o nome da conta. `code 40105` ou "permission" significa que a conta de anúncios não foi incluída na autorização do Passo 4.2; refaça a autorização marcando a conta.

## Passo 6. Segredos no ambiente

Menu do ambiente na barra de título → Editar → variáveis/segredos: `TIKTOK_ACCESS_TOKEN` e `TIKTOK_ADVERTISER_ID`. `business-api.tiktok.com` já está liberado na rede. Vale para sessões novas.

## Passo 7. Autorizar cada vídeo para Spark Ads (a parte que depende de você)

O TikTok não deixa um app anunciar com um vídeo orgânico sem autorização do dono do perfil. Há dois jeitos:

**A. Código por vídeo (o que o script usa hoje).** No app do TikTok, logado no perfil: abra o vídeo → **…** → **Configurações de anúncio** (Ad settings) → ative **Autorização de anúncio** → escolha a validade (use **365 dias**) → **Gerar código** → copie. Esse código entra no campo `auth_code` do post em `metricas.json`; sem ele, a decisão fica pendente e aparece na mensagem diária. Dá para deixar a autorização ligada por padrão em **Configurações e privacidade → Privacidade → Autorização de anúncio**, mas o código ainda é gerado por vídeo.

**B. Perfil vinculado no Business Center (sem código por vídeo).** Com os perfis autorizados no Passo 2.3, a API permite listar os vídeos do perfil e usá-los direto, pela identidade do Business Center, sem código. O script ainda não implementa essa rota; é a próxima melhoria quando o piloto estiver rodando. Mesmo assim, faça o Passo 2.3 agora: é pré-requisito dos dois caminhos.

## Passo 8. Primeiro teste, sem gastar

```
python3 scripts/impulsionar.py decidir tests/fixtures/metricas_exemplo.json tests/fixtures/historico_exemplo.json
python3 scripts/impulsionar.py executar decisoes.json --plataforma tiktok
```

Simulação: imprime os pedidos exatos sem chamar a rede. Criar de verdade exige `--executar --confirmo`, e tudo nasce **desativado** no Ads Manager para você revisar.

## Problemas comuns

- **App "em análise" por mais de 5 dias úteis**: abra um chamado no portal de desenvolvedores; às vezes pedem um texto melhor na descrição do app.
- **`auth_code` expirado**: vale 1 hora. Repita o Passo 4.1 e 4.2.
- **Vídeo recusado no Spark Ads**: o código de autorização expirou ou foi gerado em outro perfil. Gere de novo no vídeo certo.
- **"Promover" do app do TikTok**: é um atalho manual, sem API. Serve para impulsionar na mão quando quiser; o automático é só por Spark Ads.
- **Orçamento mínimo**: o TikTok exige um mínimo diário por grupo de anúncios (hoje na faixa de R$ 20 a R$ 100 dependendo do objetivo). Se recusar, suba `orcamento_por_post.min` em `config/ads.json`.
