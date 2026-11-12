# Linha de produção de vídeo: mecânica barata

Proposta para os canais Chefão dos Treinos (3 vídeos + 3 carrosséis/dia), Se Acontecesse (1 episódio/dia) e vídeos avulsos com IA (Picsart + Voice Studio). Objetivo: a mesma entrega diária gastando uma fração do limite semanal.

## 1. Diagnóstico: por que tudo no Opus estourava o limite

Lendo as três skills atuais, o gasto não vem de raciocínio. Vem de volume de contexto caro repetido muitas vezes por dia:

- **Toda etapa roda uma sessão inteira no Opus**, inclusive as puramente mecânicas: esperar o ElevenLabs, baixar arquivos pelo navegador, rodar `node stills.js`, validar JSON, copiar para o Drive, atualizar CSV.
- **A skill do Chefão tem 23 KB** e entra no contexto em todas as etapas, mesmo quando a etapa usa 10% dela. Multiplique por 3 etapas e 3 canais.
- **Os portões com `send_later` a cada 15 min** acordam a mesma sessão repetidas vezes. Cada despertar reprocessa o contexto acumulado. Uma noite de espera pode custar mais que a produção.
- **Conferência visual no modelo caro.** Folhas de contato de stills e do vídeo final são imagens; até 4 rodadas por item, no Opus, por 6 itens/dia.
- **Arquivos do PC entram no contexto** via `device_stage_files`: kit, pautas dos últimos 7 dias, catálogos, exemplos. Tudo lido pelo modelo caro, toda vez.
- **Retentativas** (áudio refeito, render parcial, upload que falha) repetem os passos acima.

Em resumo: o Opus foi usado como operador de linha de montagem. Ele deveria ser o gerente que aparece só quando algo sai do trilho.

## 2. Princípio

1. **Código faz o mecânico.** Tudo que é determinístico vira script com entrada e saída em arquivo: validar pauta, gerar e checar áudio, renderizar, montar, entregar, atualizar histórico. Script não gasta token.
2. **Modelo barato opera.** Haiku dispara os scripts, lê os resultados e segue o roteiro. Sonnet escreve textos e julga imagens.
3. **Modelo caro só decide.** Opus (ou Fable) entra apenas quando um script ou o Sonnet reporta um problema que não cabe no procedimento: cenário novo, erro de deformação que não corrige em 2 rodadas, ajuste do Felipe que muda a estrutura.

## 3. Roteamento por etapa

| Etapa | O que é | Natureza | Quem faz | Modelo |
|---|---|---|---|---|
| Escolha do tema e dos exercícios | Seguir trilha do `grade.json`, evitar repetição | Determinístico | script `escolher_pauta.py` (a criar) | nenhum |
| Pesquisa de números (Se Acontecesse) | Buscar fonte confiável por número | Leitura e síntese | agente `pesquisador` | Haiku com busca; Sonnet se a fonte for ambígua |
| Roteiro, falas, legendas, carrossel | Texto criativo dentro de molde rígido | Criativo guiado | agente `roteirista` | Sonnet |
| Validação da pauta | 11 captions, 10 falas, limites de caracteres, palavras proibidas | Determinístico | script `validar_pauta.py` | nenhum |
| Pauta para o Felipe e ajustes | Mensagem curta; reescrever só o item afetado | Texto | `roteirista` | Sonnet |
| Geração de narração | Chamar TTS fala por fala | Mecânico | script `gerar_audio.py` (a criar) | Haiku dispara |
| Checagem de narração | Transcrever e comparar com o roteiro | Determinístico | faster-whisper local + script | nenhum |
| Stills e folha de contato | Renderizar quadros | Mecânico | script | nenhum |
| Conferência visual | Erro visível? boneco inteiro? texto estourando? | Julgamento visual | agente `conferente` | Sonnet (Haiku como primeira triagem) |
| Correção de deform ou vista | Ajustar parâmetros do `episode.json` | Julgamento técnico | `conferente` até 4 rodadas por vídeo (3 por carrossel); depois escala | Sonnet, escala para Opus |
| Render, montagem, loudnorm, capa | ffmpeg e render.js | Mecânico | script `producao.py` (a criar) | nenhum |
| Entrega no Drive, histórico, mensagem | Copiar, CSV, resumo | Mecânico | script + Haiku para a mensagem | Haiku |
| Portões entre etapas | "Está pronto?" | Determinístico | a mesma tarefa agendada, em horários fixos, sessão nova e curta | o da etapa |

Resultado esperado: Opus some do dia a dia. Sonnet escreve e olha. Haiku opera. Scripts fazem o resto.

## 4. Mudanças estruturais

1. **Modelo por tarefa agendada.** Cada tarefa agendada (PAUTA, ÁUDIO, PRODUÇÃO) passa a nascer com o modelo da etapa, não com o da conta. É a maior alavanca e não exige mudar nenhum script.
2. **Skill curta, referência em arquivos.** A skill vira uma página: qual etapa, qual script rodar, o que fazer com a saída. Tabelas de deform, esquemas de JSON e regras de conteúdo vão para `reference/` dentro da skill e entram no contexto só quando o passo precisa.
3. **Portões sem acumular contexto.** Em vez de `send_later` na mesma sessão, a etapa termina quando o portão está fechado, e a própria tarefa agendada roda de novo em horários fixos (ex.: áudio às 23:07 e 00:07; produção às 01:07, 03:07 e 05:07). Cada execução é uma sessão nova e curta que lê o `estado.json` e retoma ou termina em uma linha.
4. **Validador antes de qualquer modelo olhar.** `validar_pauta.py` reprova JSON inválido, contagem errada, texto longo e palavra proibida. O Sonnet só recebe pauta válida; o conferente só recebe stills de pauta válida.
5. **Kits e pautas em git, não no PC.** Hoje a sessão depende do computador do Felipe estar ligado e de `device_stage_files`. Com o kit em repositório, a sessão clona e trabalha sozinha. O Drive fica só para a saída final.
6. **Áudio sem navegador.** Dois caminhos: (a) `edge-tts`, gratuito e local, com voz pt-BR, elimina créditos e o download via navegador; (b) manter ElevenLabs, mas operado por Haiku. Vale testar (a) em um vídeo e comparar a voz.
7. **Transcrição local.** faster-whisper no container substitui o Scribe do ElevenLabs na checagem de falas. Grátis, sem fila.

## 4b. Pauta por tendência e impulsionamento (12/11)
- **Tema do dia** vem da skill `tendencias`: o `pesquisador` consulta o vidIQ (vídeos fora da curva no Instagram e TikTok em português, buscas em alta) e grava `tendencias.json`; a trilha fixa vira reserva. Teste de 12/11 no nicho do Chefão trouxe 10 outliers brasileiros com gancho e formato; o modo de busca em alta em português veio fraco, por isso é secundário. Google Trends entra quando a rede liberar `trends.google.com`.
- **Criação sem aprovação**: a pauta nasce final e segue para áudio e produção; o Felipe recebe um aviso e só intervém se quiser. Publicação continua com aprovação por padrão (`config/publicacao.json`), porque o agendamento no vidIQ é irreversível.
- **Impulsionamento** pela skill `impulsionamento`: regras em `config/ads.json`, decisão em `scripts/impulsionar.py` (função pura testada), execução pela Marketing API da Meta e Spark Ads do TikTok, sempre em dry-run até existirem as chaves. Documento: `docs/impulsionamento.md`.

## 5. Ferramentas

Verificado neste ambiente de nuvem em 2026-11-11. Para valer em toda sessão nova, os comandos de instalação precisam ir no script de setup do ambiente (menu do ambiente na barra de título da sessão, depois Editar).

| Ferramenta | Situação | Para quê |
|---|---|---|
| ffmpeg / ffprobe 6.1 | instalado | Render, montagem, loudnorm, folhas de contato |
| ImageMagick 6 (`convert`) | instalado | Composição de imagens, carrosséis |
| Node 22, npm, Playwright + Chromium | instalado | Motor three.js do kit, hyperframes |
| Python 3.13, uv, Pillow | instalado | Scripts da linha |
| yt-dlp | instala com `uv pip` | Baixar vídeos de referência e os próprios publicados para análise |
| faster-whisper | instala com `uv pip` | Transcrever narração para checagem; legendas com tempo por palavra |
| edge-tts | instala com `uv pip` | Narração gratuita em pt-BR, candidata a substituir o ElevenLabs |
| hyperframes (HeyGen) | instala com `npx` | Vídeo a partir de HTML, feito para agentes. Candidato para formatos novos (shorts de texto, carrosséis animados), não para reescrever o motor do Chefão |
| GPU | não há | Whisper roda em CPU; modelo `small` dá conta de falas de 3 s |

Sugestões além das quatro pedidas:

- **rembg + vtracer**: já usados no fluxo de produto. Instalar de uma vez no setup.
- **pysubs2**: gerar legendas `.ass` a partir da transcrição do whisper, para queimar no vídeo com ffmpeg.
- **piper-tts**: segunda opção de voz local, offline, caso a do edge-tts não agrade.
- **jsonschema**: validar `episode.json`, `narration.json` e `carrossel.json` contra um esquema. Base do `validar_pauta.py`.
- **ffmpeg-normalize**: opcional; o `loudnorm` do ffmpeg já resolve.

Script de setup sugerido:

```
uv pip install --system yt-dlp faster-whisper edge-tts rembg onnxruntime vtracer pysubs2 jsonschema
npm install -g hyperframes
```

## 6. Organização dos repositórios

- **Este repositório (`equilibrium`)**: a linha de produção compartilhada. Agentes, scripts genéricos (validar, gerar áudio, transcrever, montar, entregar), documentação e o script de setup.
- **Um repositório por canal** (`chefao-academia`, `se-acontecesse`, `videos-ia`): o kit do motor, os moldes, o catálogo, as pautas do dia e a skill curta daquele canal. Cada um depende deste.

## 7. Próximos passos, em ordem (1, 2, 4 e 7 feitos em 11/11)

1. Trocar o modelo das tarefas agendadas existentes para Sonnet. Ganho imediato, sem mexer em script.
2. Escrever `validar_pauta.py` e `checar_audio.py` (whisper) aqui, com testes.
3. Testar `edge-tts` em um vídeo do Chefão e comparar com a voz atual.
4. Cortar a skill do Chefão para uma página e mover o restante para arquivos de referência.
5. Trazer o kit do Chefão para um repositório próprio e fazer a PRODUÇÃO rodar sem o PC ligado.
6. Repetir 4 e 5 para o Se Acontecesse.
7. Adicionar os agentes `roteirista`, `conferente` e `pesquisador` em `.claude/agents/`.
