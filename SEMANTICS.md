# Semântica lexical e interpretação contextual

## Separação de responsabilidades

O LUME possui dois níveis relacionados, mas distintos:

1. **Vocabulário de comandos** (`lume/vocabulario.py`): reconhece verbos e expressões explicitamente associados a intenções executáveis.
2. **LUME Lexicon** (`lume/lexicon.py`): armazena lemas, classes gramaticais, flexões, sentidos, relações e procedência.

Uma palavra presente no Lexicon não se torna automaticamente uma instrução válida. A execução continua dependendo da gramática e de regras semânticas explícitas.

## Representação

Uma entrada lexical pode conter:
- identificador estável;
- lema;
- classe gramatical;
- definição opcional e licenciada;
- fonte, licença e versão;
- formas flexionadas;
- relações tipadas;
- contextos documentados.

Uma palavra pode corresponder a mais de uma entrada. A API devolve todas as correspondências, em vez de escolher arbitrariamente um sentido.

## Desambiguação contextual

A API atual não implementa desambiguação automática de sentidos. O caminho de evolução recomendado é:

1. tokenizar a frase preservando posições de origem;
2. consultar lemas e flexões;
3. identificar classes gramaticais possíveis;
4. analisar dependências e papéis sintáticos;
5. gerar candidatos de sentido;
6. pontuar candidatos com regras explícitas e evidência local;
7. preservar múltiplas hipóteses quando a evidência não for suficiente;
8. rejeitar ou pedir esclarecimento quando a ambiguidade afetar a execução.

Não usar substituição de palavras como interpretação. Não escolher um significado apenas porque ele aparece primeiro no banco.

## Exemplo

Em “Abra o arquivo e mostre seu conteúdo”, o analisador precisa reconhecer duas ações e seus argumentos. A relação entre “arquivo” e “conteúdo” depende da estrutura sintática e de uma regra que indique a propriedade do objeto. O Lexicon sozinho não executa essa análise.

## Determinismo

A mesma entrada, o mesmo contexto e a mesma versão lexical devem produzir os mesmos candidatos e decisões. O banco lexical não deve alterar AST ou IR por efeitos colaterais. As posições da fonte devem ser preservadas nos diagnósticos.
