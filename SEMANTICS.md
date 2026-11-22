# Semântica lexical e interpretação contextual

## Separação de responsabilidades

1. **Vocabulário de comandos** (`lume/vocabulario.py`): associa expressões explícitas a intenções executáveis.
2. **LUME Lexicon** (`lume/lexicon.py`): armazena lemas, classes gramaticais, flexões, sentidos, glossas, relações e procedência.
3. **Desambiguador contextual** (`lume/desambiguacao.py`): gera e pontua candidatos com evidências locais, sem transformar palavras em comandos.

Uma palavra presente no Lexicon não se torna automaticamente uma instrução válida. A execução continua dependendo da gramática e das regras semânticas explícitas.

## Integração

`Interpretador` recebe uma instância opcional e compartilhável de `Lexicon`. `InterpretadorSemantico` usa essa instância ou aceita outra explicitamente, oferecendo `analisar_lexico(texto)`.

O resultado contém token, candidatos, pontuação, evidências, seleção e indicador de ambiguidade. A análise não reescreve a fonte, AST ou IR e não executa conteúdo lexical.

## Estratégia atual

- Tokenização Unicode preservando a forma normalizada.
- Consulta por lema e formas registradas.
- Pistas locais simples de classe gramatical (artigos, alguns advérbios e preposições).
- Pontuação adicional por contextos textuais registrados.
- Ordenação determinística por pontuação, lema e identificador.
- Seleção apenas quando há candidato único ou margem mínima suficiente.
- Ambiguidade preservada quando a evidência é insuficiente.

As pistas gramaticais são heurísticas locais, não um parser de dependências. Não confundir o resultado com uma solução geral de Word Sense Disambiguation.

## Exemplo

Em “o canto”, o artigo pode favorecer uma entrada substantiva em relação a uma entrada verbal. Em “canto”, sem contexto, as duas leituras devem permanecer candidatas.

## Evolução

Para uma compreensão contextual mais ampla, a próxima camada deve integrar:
1. análise morfológica que relacione flexões a lemas;
2. análise sintática e papéis dos argumentos;
3. relações de synset e contexto discursivo;
4. pontuação com corpus licenciado e avaliação anotada;
5. limiares calibrados em dados de teste;
6. esclarecimento quando a ambiguidade alterar a execução.

Não usar substituição de palavras como interpretação. A mesma entrada, contexto e versão lexical devem produzir os mesmos candidatos.
