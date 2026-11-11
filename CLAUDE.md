# Equilibrium

## Agentes e delegação por custo

Este repositório usa uma hierarquia de agentes em `.claude/agents/`. O princípio: o modelo caro raciocina e decide; os modelos baratos leem, digitam e verificam.

| Agente | Modelo | Esforço | Papel | Edita? |
|---|---|---|---|---|
| `arquiteto-fable` | Fable | high | Orquestrador: entende, decide, especifica, integra | Sim |
| `arquiteto-opus` | Opus | high | Mesmo papel, mais barato. Padrão para a maioria das tarefas | Sim |
| `explorador` | Haiku | low | Busca, leitura, levantamento factual | Não |
| `implementador` | Sonnet | medium | Implementa tarefas fechadas e roda testes | Sim |
| `revisor` | Sonnet | high | Revisa diff contra a especificação, roda testes | Não |

### Como usar

Sessão principal já como orquestrador:

```
claude --agent arquiteto-opus
claude --agent arquiteto-fable
```

Em qualquer sessão normal, o Claude lê este arquivo e delega pelos mesmos critérios. Para forçar, basta pedir: "use o explorador para mapear X" ou "delegue a implementação ao implementador".

### Regras de roteamento

- Pergunta factual sobre o código, leitura de muitos arquivos, levantamento: `explorador`. Vários em paralelo quando as perguntas forem independentes.
- Decisão de arquitetura, requisito ambíguo, trade-off: o orquestrador resolve. Não delega.
- Tarefa com especificação fechada (o que, onde, critério de pronto): `implementador`.
- Antes de commitar algo não trivial: `revisor` com a especificação e o diff.
- Trivial (edição de poucas linhas, um grep, um comando conhecido): o orquestrador faz direto. Delegar custaria mais do que fazer.

### Quando escolher Fable ou Opus como orquestrador

- Opus: padrão. Engenharia do dia a dia, refatorações, features bem delimitadas.
- Fable: problemas de raciocínio profundo, horizonte longo, depuração difícil, decisões com muitas partes móveis.
- Antes de subir de modelo, tente subir o esforço do Opus para `xhigh`. Costuma ser mais barato e suficiente.

### Custo por tarefa, não por chamada

Um worker barato que erra e gera retrabalho sai mais caro que o orquestrador acertando de primeira. Se um implementador devolver dúvidas repetidas na mesma tarefa, a especificação estava fraca ou a tarefa não era para ele. Ajuste o brief ou faça direto.

## Convenções de git

- Commits pequenos e descritivos. Subagentes não fazem commit; o orquestrador faz.
- Rode as verificações rápidas do projeto antes de qualquer push.
