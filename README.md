# equilibrium
Mastering advanced concepts in concrete and steel structures.

## Agentes de IA

O repositório traz uma hierarquia de agentes para o Claude Code em `.claude/agents/`: dois orquestradores (Fable e Opus) que raciocinam e decidem, e três workers baratos (Haiku para busca, Sonnet para implementação e revisão). A política de delegação está em `CLAUDE.md`.

```
claude --agent arquiteto-opus    # padrão
claude --agent arquiteto-fable   # raciocínio profundo
```
