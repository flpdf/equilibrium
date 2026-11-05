# Alerta SP: tutorial para rodar no seu computador

Tempo total: cerca de 40 minutos, quase todo esperando download. Você faz isso uma vez só.

---

## 0. O que você precisa

- **Windows 10 ou 11**, com uns **5 GB livres** no disco C:.
- **O app Claude para desktop** (o mesmo onde você usa o Cowork), logado na sua conta Pro ou Max.
- **O Google Drive para desktop**, já instalado (é o seu `G:\Meu Drive`).
- **Uma placa de vídeo** (opcional). Com ela a render leva minutos; sem ela, cerca de 1 hora.

### Onde guardar o projeto

Recomendo **o projeto no disco C:** e **só os vídeos prontos no Drive**:

- **Projeto:** `C:\AlertaSP`
- **Vídeos prontos:** `G:\Meu Drive\Área de Trabalho\Alerta-SP\Episodios`

Por que não colocar tudo no Drive:

- A render cria cerca de 2.300 imagens temporárias por episódio. O Drive tentaria sincronizar todas, uma por uma.
- O modelo de voz (350 MB) ocuparia espaço no Drive sem necessidade.
- Caminhos com acento ("Área de Trabalho") às vezes causam erro em ferramentas de áudio e vídeo.

---

## 1. Baixar o projeto

1. Abra este link no navegador (você precisa estar logado no GitHub com a conta que vê o repositório):
   `https://github.com/flpdf/equilibrium/archive/refs/heads/claude/story-video-studio-setup-h7ylnd.zip`
2. Extraia o ZIP. Ele cria uma pasta com um nome comprido.
3. Renomeie essa pasta para `AlertaSP` e mova para `C:\`. O resultado deve ser:
   ```
   C:\AlertaSP\CLAUDE.md
   C:\AlertaSP\engine\...
   C:\AlertaSP\part1\...
   ```
4. Crie a pasta dos vídeos prontos: `G:\Meu Drive\Área de Trabalho\Alerta-SP\Episodios`.

---

## 2. Instalar o Python

1. Abra o **PowerShell**: tecla Windows, digite "PowerShell" e dê Enter.
2. Cole e dê Enter:
   ```
   winget install -e --id Python.Python.3.12
   ```
3. **Feche e abra o PowerShell de novo** e confira:
   ```
   python --version
   ```
   Tem que aparecer `Python 3.12.x`. Se aparecer "não encontrado", reinicie o computador e tente de novo.

---

## 3. Preparar o projeto

Ainda no PowerShell, cole uma linha por vez:

```
cd C:\AlertaSP
python -m pip install playwright kokoro-onnx soundfile faster-whisper edge-tts numpy pillow imageio-ffmpeg
python engine/fetch_vendor.py
```

O que cada linha faz:

- **Primeira:** entra na pasta do projeto.
- **Segunda:** instala as ferramentas, em uns 3 minutos.
- **Terceira:** confere as peças do 3D. Elas já vêm no ZIP, então ela só diz "vendor ready".

Se você **não** tem o Google Chrome instalado, rode também:

```
python -m playwright install chromium
```

---

## 4. Testar (antes de agendar qualquer coisa)

### 4.1 Teste da voz

Ele baixa uma vez o modelo de voz (350 MB) e o de sincronia das legendas (cerca de 145 MB).

```
mkdir teste
```

Crie o arquivo `C:\AlertaSP\teste\lines.json` no Bloco de Notas, com este conteúdo, e salve com codificação **UTF-8**:

```json
{"voice": "pm_alex", "speed": 1.1, "lang": "pt-br", "lines": [
 {"text": "Imagina que são 23:58, e São Paulo inteira apaga.", "say": "Imagina que são vinte e três e cinquenta e oito, e São Paulo inteira apaga."}]}
```

Depois rode:

```
python engine/voice.py teste
```

**Deu certo se** aparecer `caption check: OK` e **não** aparecer "word timing fell back to an estimate". Essa frase só aparece quando o modelo de legendas não baixou. Aqui na nuvem ele não baixava; no seu PC deve baixar.

Para ouvir, abra `C:\AlertaSP\teste\narration.wav`.

### 4.2 Teste da imagem

```
python engine/render.py part1/film.html part1/stills --at 13.6 --gpu
```

Abra `C:\AlertaSP\part1\stills\at_13.60.jpg`. Tem que aparecer o monitor vermelho com o selo "2017".

- **Imagem preta ou erro com `--gpu`:** rode de novo sem o `--gpu`. Vai funcionar, só que mais devagar.

### 4.3 Teste do som com efeitos reais

Crie o arquivo `C:\AlertaSP\teste\sfx.json` com este conteúdo:

```json
{"sfx": [{"at": "apaga@0", "type": "knock"}]}
```

Depois rode:

```
python engine/sound.py teste 7
```

**Deu certo se** **não** aparecer "Mixkit ... not available". Isso mostra que os efeitos reais (batidas, tranca, sirene) baixaram. Para ouvir, abra `C:\AlertaSP\teste\mix.wav`.

Depois apague a pasta `teste`.

---

## 5. (Opcional) Refazer o Dia 1 com som e legendas melhores

Se quiser repostar o Dia 1 com os efeitos reais e as legendas exatas, abra o Cowork com a pasta `C:\AlertaSP` e peça:

```
Refaça o Dia 1 (part1) neste computador seguindo o CLAUDE.md: voice.py, confira os stills, sound.py com o TOTAL novo (voice_end + 3,5), render completa com --gpu e encode. Copie part1.mp4 para G:\Meu Drive\Área de Trabalho\Alerta-SP\Episodios\Dia1\ junto com cover.jpg e post.md.
```

---

## 6. Criar a tarefa agendada no app Claude

1. Abra o **app Claude** no computador e vá em **Cowork**.
2. Inicie uma conversa com a pasta `C:\AlertaSP` liberada para o Claude.
3. Cole a mensagem abaixo:

```
Crie uma tarefa agendada diária às 10:38 (horário de Brasília), com notificação, que rode neste computador na pasta C:\AlertaSP, com esta instrução:

"Rotina diária da série Alerta SP. Fale em português do Brasil. Pasta do projeto: C:\AlertaSP. Leia o CLAUDE.md inteiro, que manda em tudo.
(1) Confira o ambiente (CLAUDE.md, seção 0) e descubra o último episódio (a pasta partN de maior número): história, regras, personagens e a escolha do final.
(2) Peça ao Felipe: o resultado da votação (A ou B) e os comentários de destaque, um briefing de como a história segue, e mudanças de duração, voz ou cenário. Se ele não responder em 2 horas, trate todos os portões do CLAUDE.md como 'você escolhe': escolha a opção que rende a melhor continuação e diga qual escolheu e por quê.
(3) Produza partN+1 seguindo o CLAUDE.md à risca (seção Part 2). Renderize com --gpu (se der erro, sem --gpu), em 3 faixas em paralelo.
(4) Copie partN+1.mp4, cover.jpg e post.md para G:\Meu Drive\Área de Trabalho\Alerta-SP\Episodios\DiaN+1\ e cole o kit de post completo na resposta (título, descrições de TikTok, Reels e Shorts, hashtags, comentário fixado). Apague frames, vo e stills."

Se a tarefa não conseguir esperar 2 horas pela minha resposta, divida em duas: uma às 10:38 que só me pergunta, e outra às 12:38 que produz se eu não tiver respondido. No fim, me mostre a(s) tarefa(s) criada(s).
```

4. Confira na aba de tarefas agendadas do app se ela apareceu.

### Para a tarefa funcionar todo dia

- **Computador ligado às 10:38**, com o app Claude aberto (pode ficar minimizado).
- **Suspensão desligada nesse horário:** em Configurações > Sistema > Energia, ponha "Suspender" em "Nunca" quando estiver na tomada, ou pelo menos num tempo maior que 2 horas.
- **O Drive para desktop rodando**, para os vídeos subirem.

---

## 7. Desligar a rotina da nuvem

Hoje existe também a rotina **"Alerta SP – episódio do dia"** na nuvem, às 10:38. Quando a local estiver criada e testada, **desligue a da nuvem** para não sair episódio em dobro. Você pode:

- apagar a rotina na aba de tarefas agendadas do claude.ai; ou
- me pedir aqui: "desliga a rotina da nuvem".

---

## 8. Como fica o dia a dia

| Hora | O que acontece |
|---|---|
| 10:38 | Chega a notificação: o Claude pede o resultado da votação e o briefing. |
| Você responde | Ele produz na hora: roteiro, voz, cenas, som e vídeo. Com placa de vídeo, deve levar uns 20 a 40 minutos. |
| Sem resposta até 12:38 | Ele decide sozinho e produz. |
| Pronto | O vídeo, a capa e o `post.md` aparecem em `Episodios\DiaN` no Drive, e o kit de post vem colado na conversa. |

Para postar, pegue o vídeo e a capa no app do Drive no celular e copie a descrição da plataforma certa.

---

## 9. Se algo der errado

| Problema | Solução |
|---|---|
| `python` não é reconhecido | Feche e abra o PowerShell. Se continuar, reinicie o PC. |
| "word timing fell back to an estimate" | O modelo de legendas não baixou. Confira a internet e rode `voice.py` de novo. |
| "Mixkit ... not available" | Os efeitos não baixaram. O vídeo sai com os sons feitos em código. Rode `sound.py` de novo depois. |
| Imagem preta com `--gpu` | Rode sem `--gpu`. |
| A render parou no meio | Rode de novo com `--from N`, onde N é o número do último quadro em `frames\` mais 1. |
| "CAPTION CHUNK FAIL" | Uma legenda terminou em palavra como "de" ou "que". O Claude corrige o roteiro e roda de novo. |
| A tarefa não rodou | O PC estava desligado ou suspenso, ou o app estava fechado. Rode manualmente pela aba de tarefas. |
| O vídeo veio sem som no celular | Toque no ícone de som do player, ou tire o celular do modo silencioso. |

---

## 10. E o GitHub?

Ele vira só um backup. A partir de agora o projeto "de verdade" fica em `C:\AlertaSP`. Se quiser manter o GitHub atualizado, instale o Git (`winget install -e --id Git.Git`) e peça ao Claude para fazer commit e push no fim de cada episódio. Se não quiser, ele simplesmente fica parado na versão de hoje.
