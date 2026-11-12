# equilibrium

Linha de produção de vídeos curtos (Instagram, TikTok, YouTube Shorts) operada por agentes de IA, com custo controlado: scripts fazem o mecânico, modelos baratos operam, o modelo caro só decide.

- Mecânica proposta: [`docs/mecanica-producao-video.md`](docs/mecanica-producao-video.md)
- Agentes e política de delegação: [`CLAUDE.md`](CLAUDE.md) e [`.claude/agents/`](.claude/agents/)
- O propósito original deste repositório, um SaaS de engenharia estrutural, está preservado em [`README-engenharia-estrutural.md`](README-engenharia-estrutural.md).

## Agentes de IA

Dois orquestradores (Fable e Opus) que raciocinam e decidem, e três workers baratos (Haiku para busca, Sonnet para implementação e revisão).

```
claude --agent arquiteto-opus    # padrão
claude --agent arquiteto-fable   # raciocínio profundo
```
