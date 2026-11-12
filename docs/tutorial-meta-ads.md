# Tutorial: preparar a Meta (Instagram) para o impulsionamento automático

Objetivo: ao final, você terá quatro valores para colocar nos segredos do ambiente, e o script `scripts/impulsionar.py` conseguirá criar anúncios pausados a partir de reels já publicados no @chefaodostreinos, @spoff.line e @eseacontecessse.

| Segredo | O que é | Onde pegar |
|---|---|---|
| `META_ACCESS_TOKEN` | token de usuário do sistema, não expira | Passo 5 |
| `META_AD_ACCOUNT_ID` | conta de anúncios, formato `act_123456789` | Passo 2 |
| `META_PAGE_ID` | id da Página do Facebook ligada ao Instagram | Passo 6 (opcional: já gravado em `config/ads.json`) |
| `META_IG_USER_ID` | id do perfil profissional do Instagram | Passo 6 (opcional: já gravado em `config/ads.json`) |

Os nomes dos menus da Meta mudam com frequência. Quando o nome não bater, procure a opção equivalente na mesma tela.

## Passo 1. Portfólio empresarial (Business Manager) com Página e Instagram

1. Entre em https://business.facebook.com com a sua conta pessoal do Facebook. Se não tiver um portfólio empresarial, crie um ("Criar conta" ou "Criar portfólio empresarial"): nome do negócio, seu nome, e-mail.
2. Em **Configurações do negócio** (ícone de engrenagem), menu **Contas → Páginas**: clique em **Adicionar** e escolha "Adicionar uma Página" (se ela já é sua) ou "Criar uma nova Página". Cada perfil do Instagram precisa de uma Página do Facebook ligada, mesmo que você nunca poste nela.
3. Menu **Contas → Contas do Instagram**: **Adicionar**, faça login no perfil. O perfil precisa ser **profissional** (Criador ou Empresa). Se for pessoal, no app do Instagram: Configurações → Tipo de conta e ferramentas → Mudar para conta profissional.
4. Ligue cada Instagram à sua Página: no app do Instagram, Configurações → Central de contas → Contas → adicionar a Página; ou na Página do Facebook, Configurações → Contas vinculadas → Instagram.
5. Repita para os três perfis. Anote qual Página vai com qual Instagram.

## Passo 2. Conta de anúncios com pagamento

1. Em **Configurações do negócio → Contas → Contas de anúncios**: **Adicionar → Criar uma nova conta de anúncios**. Nome, fuso América/São Paulo, moeda BRL.
2. Abra o **Gerenciador de Anúncios** (https://adsmanager.facebook.com), menu **Faturamento e pagamentos**, adicione um cartão ou Pix como método de pagamento principal.
3. Copie o **ID da conta de anúncios** (aparece no topo do Gerenciador de Anúncios e em Configurações do negócio). O segredo é `act_` seguido do número: `META_AD_ACCOUNT_ID=act_123456789`.
4. Uma conta nova pode pedir verificação do negócio ou ficar com limite de gasto baixo nos primeiros dias. Isso é normal e não bloqueia a criação de anúncios pausados.

## Passo 3. App de desenvolvedor com a Marketing API

1. Entre em https://developers.facebook.com com a mesma conta. Se for a primeira vez, aceite os termos de desenvolvedor.
2. **Meus apps → Criar app**. Caso de uso: escolha a opção de **anúncios/Marketing** (em versões antigas: tipo **Business**). Nome: `impulsionamento-videos`. Vincule ao portfólio empresarial do Passo 1 quando perguntar.
3. No painel do app, em **Adicionar produtos**, adicione **Marketing API**. Se oferecer um assistente de configuração, pode pular.
4. Em **Configurações do app → Básico**, confirme que o app está no modo **Desenvolvimento**. Para anunciar apenas nas suas próprias contas não precisa publicar o app nem passar por Revisão de app.

## Passo 4. Ligar os ativos ao app

1. Volte a **business.facebook.com → Configurações do negócio**.
2. Menu **Contas → Apps**: se o app não aparecer, **Adicionar → Conectar um ID de app** e cole o ID do app (está em Configurações do app → Básico).
3. Ainda em Configurações do negócio, abra **Contas → Contas de anúncios**, selecione a conta, **Atribuir parceiros/apps** ou aba **Apps conectados**, e adicione o app com acesso de gerenciamento. Faça o mesmo em **Páginas** e **Contas do Instagram** se a tela oferecer.

## Passo 5. Usuário do sistema e token que não expira

1. **Configurações do negócio → Usuários → Usuários do sistema → Adicionar**. Nome `claude-ads`, função **Administrador** (Funcionário basta se você der os ativos um a um, mas Administrador evita erro de permissão).
2. Com o usuário criado, clique em **Atribuir ativos**: marque a **conta de anúncios** (controle total / gerenciar campanhas), as três **Páginas** (controle total ou gerenciar) e as três **contas do Instagram**. Salve.
3. Clique em **Gerar novo token**. Escolha o app do Passo 3. Em "validade do token", escolha **Nunca expira**. Marque as permissões:
   - `ads_management`
   - `ads_read`
   - `pages_read_engagement`
   - `pages_show_list`
   - `instagram_basic`
   - `business_management`
4. Gere e **copie o token agora**: ele só aparece uma vez. Esse é o `META_ACCESS_TOKEN`. Guarde em lugar seguro; quem tiver esse token cria anúncios na sua conta.

## Passo 6. Descobrir os ids da Página e do Instagram

Com o token em mãos, use o **Explorador da Graph API** (https://developers.facebook.com/tools/explorer) colando o token no campo de token, ou rode no seu PC:

```
curl "https://graph.facebook.com/v21.0/me/accounts?fields=id,name,instagram_business_account&access_token=SEU_TOKEN"
```

A resposta lista cada Página com `id` (é o `META_PAGE_ID`) e, dentro, `instagram_business_account.id` (é o `META_IG_USER_ID`). Se `instagram_business_account` não aparecer, o Instagram não está ligado à Página (Passo 1.4) ou o usuário do sistema não recebeu esse Instagram (Passo 5.2).

Para começar, use a Página e o Instagram do **Chefão**. Os outros dois perfis ficam para uma segunda rodada: o script hoje lê um par Página/Instagram por vez.

## Passo 7. Conferir o acesso antes de guardar os segredos

Três chamadas que precisam responder sem erro:

```
curl "https://graph.facebook.com/v21.0/me?access_token=SEU_TOKEN"
curl "https://graph.facebook.com/v21.0/act_SEU_ID/campaigns?fields=id,name&limit=3&access_token=SEU_TOKEN"
curl "https://graph.facebook.com/v21.0/SEU_IG_USER_ID/media?fields=id,media_type,permalink&limit=3&access_token=SEU_TOKEN"
```

- A primeira devolve o nome do usuário do sistema.
- A segunda devolve `{"data":[]}` ou campanhas existentes; erro de permissão aqui significa que a conta de anúncios não foi atribuída ao usuário do sistema.
- A terceira lista os últimos reels com `id`: esse `id` é o `midia_id` que o script usa para transformar um reel em anúncio.

## Passo 8. Guardar os segredos no ambiente da nuvem

1. Nesta sessão, menu do ambiente na barra de título → **Editar**.
2. Na seção de variáveis de ambiente ou segredos, adicione quatro entradas: `META_ACCESS_TOKEN`, `META_AD_ACCOUNT_ID`, `META_PAGE_ID`, `META_IG_USER_ID`.
3. Confirme que `graph.facebook.com` está nos domínios permitidos da rede (já foi adicionado em 12/11).
4. Salve. Vale para sessões novas, inclusive a tarefa agendada de impulsionamento.

## Passo 9. Primeiro teste, sem gastar nada

Em uma sessão nova nesta pasta:

```
python3 scripts/impulsionar.py decidir tests/fixtures/metricas_exemplo.json tests/fixtures/historico_exemplo.json
python3 scripts/impulsionar.py executar decisoes.json --plataforma instagram
```

A segunda linha roda em simulação: imprime os pedidos exatos que seriam enviados à Meta e não chama a rede. Quando quiser criar de verdade, acrescente `--executar --confirmo`. Tudo nasce **pausado** no Gerenciador de Anúncios; você revisa e ativa lá.

## Problemas comuns

- **"(#200) permissions error"**: faltou permissão no token (Passo 5.3) ou o ativo não foi atribuído ao usuário do sistema (Passo 5.2). Gere um token novo depois de corrigir.
- **"Unsupported post request" ao criar o criativo**: o `midia_id` não é de um reel do Instagram ligado à Página informada, ou a Página não tem o Instagram vinculado.
- **Conta de anúncios desativada ou "em análise"**: contas novas passam por verificação; espere e tente de novo. Verificação do negócio em Configurações do negócio → Central de segurança.
- **Orçamento mínimo**: a Meta recusa orçamentos diários muito baixos para alguns objetivos. Se recusar R$ 5 por dia, suba `orcamento_por_post.min` em `config/ads.json`.
- **Token "inválido" depois de trocar a senha do Facebook**: tokens de usuário do sistema não caem com troca de senha, mas caem se o usuário do sistema for removido ou o app for apagado.
