# Tarefas agendadas (estado em 11/11/2026)

Princípio: prompt de uma linha apontando para a skill do repositório; modelo da etapa, não da conta; horários repetidos no lugar de `send_later`. Todas ficam **desativadas** até os kits estarem acessíveis sem o PC ou até o Felipe reativar.

| Tarefa | Horário (BRT) | Modelo | Prompt |
|---|---|---|---|
| Chefão – pauta da véspera | 17:47 | Sonnet | Etapa A (PAUTA) da skill `chefao`, para AMANHÃ. |
| Chefão – áudio das narrações | 23:07 e 00:07 | Sonnet (Haiku depois de uma semana limpa) | Etapa B (ÁUDIO) da skill `chefao`, para AMANHÃ. |
| Chefão – produção da madrugada | 01:07, 03:07 e 05:07 | Sonnet | Etapa C (PRODUÇÃO) da skill `chefao`, para HOJE. |
| Se Acontecesse – pauta da véspera | 18:23 | Sonnet | Etapa A (PAUTA) da skill `se-acontecesse`, para AMANHÃ. |
| Se Acontecesse – produção da noite | 22:41 e 23:41 | Sonnet | Etapa B (PRODUÇÃO) da skill `se-acontecesse`, para AMANHÃ. |
| Alerta SP – episódio do dia | 17:47 | Sonnet | Etapa A da skill `alerta-sp` para HOJE; no fim, `send_later` às 02:30 com "Etapa B (PRODUÇÃO) da skill `alerta-sp`". |
| Publicações do dia (vidIQ) | 08:49 e 10:49 | Sonnet | Skill `publicacao`, para HOJE. |
| Resumo matinal | 07:46, seg–sex | Sonnet | inalterado (`/morning`, engenharia civil) |
| Impulsionamento (ads) | 12:17 e 20:17 | Sonnet | Skill `impulsionamento`, para HOJE. Criada em 12/11, desativada. Ficou SEM conectores: esta conta não aceita conectores em tarefas criadas por sessão. Antes de ativar, adicione vidIQ, Metricool e Google Drive à tarefa na tela de tarefas agendadas do claude.ai. |

Lembretes de story do Alerta SP (Dia 0, 1 e 2; 11–13/11, 20:55): desativados pelo Felipe; ficam até ele decidir se posta os stories.

## O que já foi aplicado e o que depende do Felipe
As sete tarefas de vídeo estão vinculadas ao computador "Administrator". Por isso:
- **Horários**: aplicados em 11/11 (áudio 23:07 e 00:07; produção 01:07, 03:07 e 05:07; Se Acontecesse produção 22:41 e 23:41; publicação 08:49 e 10:49).
- **Prompts e modelo**: só mudam com aprovação do Felipe em uma conversa ligada a esse computador, ou editando a tarefa no app do Claude no PC. Os prompts da tabela acima estão prontos para colar; o modelo deve ir para Sonnet.
- **Resumo matinal**: não é vinculada ao PC; já está em Sonnet.

## Por que o prompt é de uma linha
O prompt antigo repetia a skill inteira e empilhava "ajustes do Felipe" por cima, com três fontes de verdade (skill sincronizada, `SKILL.md` no Drive, prompt da tarefa) que se contradiziam. Agora a skill no repositório manda, e a tarefa só diz qual etapa rodar.

## Conectores
`update_trigger` não altera conectores; só uma tarefa nova. Quando as tarefas forem recriadas (ao reativar a linha), cada uma leva só o que usa:

| Tarefa | Conectores |
|---|---|
| Chefão pauta / produção, Se Acontecesse pauta / produção, Alerta SP | Google_Drive |
| Chefão áudio | Google_Drive, ElevenLabs |
| Publicações do dia | Google_Drive, vidIQ |
| Resumo matinal | Gmail, Google_Calendar, Google_Drive |

Fora de todas: Metricool (não é mais usado), CargoosCorp (exige autenticação e não tem relação), Openart, Windsor, Exa, Claude_Docs (não usados por nenhuma etapa).

## Para reativar a linha
0. Compartilhar a pasta `Videos-Claude` do Drive como "qualquer pessoa com o link" (leitor). Testado em 12/11: um arquivo assim compartilhado baixa do container com bytes exatos (`scripts/drive_baixar.py`); um arquivo privado devolve a página de login. Isso completa o espelho do Chefão (6 arquivos pendentes, listados no fim de `canais/chefao/DRIVE.md`: `python3 scripts/drive_baixar.py manifesto canais/chefao/DRIVE.md --destino canais/chefao --secao Pendentes`) e permite à produção baixar `.fbx`, `.glb` e músicas sem o PC.
1. Dar merge deste trabalho na `main` (as tarefas clonam a `main`).
2. Colocar os dois comandos de setup de `docs/mecanica-producao-video.md` § 5 no script do ambiente.
2b. Na configuração de rede do ambiente (menu do ambiente na barra de título, Editar, Network access), adicionar aos domínios permitidos: `drive.google.com`, `drive.usercontent.google.com`, `www.googleapis.com`, `lh3.googleusercontent.com`, `huggingface.co`, `cdn-lfs.hf.co`, `cdn-lfs-us-1.hf.co`, `cas-bridge.xethub.hf.co`, `cas-server.xethub.hf.co` (modelo do whisper), `trends.google.com` (Google Trends), `graph.facebook.com` e `business-api.tiktok.com` (ads), mantendo marcada a opção de gerenciadores de pacotes. Testado em 12/11: Drive e `huggingface.co` já abrem; os hosts `hf.co`, Trends e ads ainda não. Os arquivos de texto dos kits já estão em `canais/`; os pesados (`.fbx`, `.glb`, `.mp3`, músicas) continuam no Drive e precisam desse acesso para a produção rodar sem o PC.
3. Reativar uma tarefa por vez, começando pela pauta do Chefão, e ler a sessão resultante.
