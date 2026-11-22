# Arquitetura técnica

A implementação de referência está dividida em módulos pequenos, sem dependências de terceiros.

## Fluxo de execução

1. `lexer.py` lê caracteres Unicode e produz tokens com posição de linha e coluna.
2. `tokens.py` define a estrutura de cada token.
3. `parser.py` valida a gramática e constrói os nós definidos em `nos.py`.
4. `interpretador.py` avalia expressões e executa instruções.
5. `ambiente.py` mantém variáveis em ambientes encadeados, permitindo escopo local em chamadas de função.
6. `cli.py` conecta leitura de arquivos, mensagens de erro e execução no terminal.

## Decisões de projeto

- A análise sintática é independente da execução. `--verificar` pode validar um programa sem executá-lo.
- A AST usa classes de dados explícitas; não há tradução da fonte para Python.
- A avaliação não usa `eval`, `exec` ou compilação de texto para código Python.
- Funções definidas em Lume guardam o ambiente em que foram declaradas (fechamento léxico).
- Nomes são normalizados em Unicode NFC e comparados sem distinção de caixa.
- O interpretador possui limite configurável de etapas para reduzir o risco de laços intermináveis.
- Coleções e alguns resultados numéricos possuem limites defensivos.
- A biblioteca padrão inicial é intencionalmente pequena e implementada no interpretador.

## Estrutura

```text
lume/
  ambiente.py       ambientes e variáveis
  cli.py            interface de terminal
  erros.py          erros e sinais de controle
  interpretador.py  avaliação da AST e biblioteca inicial
  lexer.py           análise de caracteres e tokens
  nos.py             nós da AST
  parser.py          análise gramatical
  tokens.py          estrutura dos tokens
  __main__.py        execução por python -m lume
  __init__.py        versão e API pública mínima
```

## Limitações conhecidas

O projeto ainda não possui um validador semântico em etapa separada, sistema de módulos, depurador, rastreamento completo da origem dos erros durante a execução, coletor de lixo próprio, bytecode ou compilador nativo. O ambiente de execução usa a memória e o coletor de lixo do Python. Essas limitações devem ser consideradas antes de avaliar desempenho ou segurança em cenários de produção.
