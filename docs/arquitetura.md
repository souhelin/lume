# Arquitetura técnica

A Lume usa componentes próprios e não depende de bibliotecas externas para interpretar programas. O front-end semântico e o front-end estruturado convergem para operações internas executadas pelo mesmo interpretador.

## Fluxo tradicional

1. lexer.py lê caracteres Unicode e produz tokens com posição de linha e coluna.
2. tokens.py define a estrutura de cada token.
3. parser.py valida a gramática e constrói os nós definidos em nos.py.
4. interpretador.py avalia expressões e executa instruções.
5. ambiente.py mantém variáveis em ambientes encadeados.
6. cli.py conecta leitura de arquivos, diagnósticos e execução no terminal.

## Fluxo semântico

~~~text
Texto de entrada
  → análise léxica
  → dicionário e reconhecimento de padrões
  → tradução para formas canônicas
  → parser e AST
  → representação intermediária (IR)
  → validador semântico
  → conversão da IR para nós executáveis
  → interpretador comum
~~~

Os módulos responsáveis são:

- vocabulario.py: registro expansível de expressões, significado, categoria, intenção, operações associadas, relações, regras e ambiguidades.
- semantica.py: padrões naturais documentados, contexto, compilação, análise de ambiguidades e validador estático.
- representacao.py: IR independente da frase original e adaptadores entre IR e AST.
- erros.py: categorias de erro semântico e ambiguidade, além dos erros léxicos, sintáticos e de execução.

A camada semântica não cria código Python e não chama eval ou exec. O vocabulário não executa palavras isoladamente: os padrões reconhecidos viram instruções canônicas; estas são transformadas em IR e validadas antes de alcançar o executor existente.

## Decisões de projeto

- A validação é separada da execução. --verificar não executa o programa.
- A AST usa classes de dados explícitas.
- A IR representa operações estáveis, como declarar, atribuir, exibir, condicional e enquanto.
- A semântica é determinística: somente padrões declarados são aceitos. Ambiguidades não são resolvidas por suposição.
- A análise de tipos é parcial e conservadora; o executor ainda verifica condições dependentes de valores de execução.
- Nomes são normalizados em Unicode NFC e comparados sem distinção de caixa.
- O interpretador possui limite configurável de etapas; coleções e alguns resultados numéricos possuem limites defensivos.
- A gramática anterior permanece disponível e compartilha o mesmo núcleo de execução.

## Estrutura

~~~text
lume/
  ambiente.py       ambientes e variáveis
  biblioteca.py     funções nativas e biblioteca padrão
  cli.py            interface de terminal e seleção do front-end
  erros.py          erros e sinais de controle
  interpretador.py  execução da AST e biblioteca padrão
  lexer.py          análise léxica
  nos.py            nós da AST
  parser.py         gramática estruturada
  formatador.py     normalização determinística de recuo
  representacao.py  representação intermediária
  semantica.py      compilador, contexto e validador semântico
  tokens.py         estrutura dos tokens
  vocabulario.py    dicionário semântico expansível
  __main__.py       execução por python -m lume
  __init__.py       API pública
~~~

## Limites conhecidos

O front-end natural é um conjunto explícito de padrões, não um analisador de português irrestrito. A inferência de tipos é parcial. Ainda não existem sistema de módulos, manipulação de arquivos na linguagem, exceções definidas pelo usuário, depurador, bytecode ou compilador nativo. O runtime de referência usa a memória e o coletor de lixo do Python. Essas limitações devem ser consideradas antes de avaliar desempenho ou segurança em produção.


## Diagnósticos e posição de origem

O parser associa a posição inicial de cada instrução à AST. A conversão para IR preserva a posição, e o executor anexa essa posição a erros de execução que ainda não possuem uma localização mais específica. Erros semânticos são associados à instrução validada. A CLI apresenta arquivo, linha, coluna e uma indicação visual do ponto de origem.


## Biblioteca padrão

As funções nativas ficam registradas em biblioteca.py e recebem explicitamente a instância do interpretador. O interpretador mantém a avaliação de expressões e o controle de execução; o módulo da biblioteca concentra conversões, coleções, textos, entrada/saída e operações de arquivos. Essa separação evita acoplar a implementação das funções nativas ao parser ou à gramática.


O modo --verificar usa o mesmo contexto semântico nos front-ends tradicional e natural. Importações iniciais são resolvidas recursivamente em modo de análise, sem executar os módulos; seus símbolos são adicionados ao contexto antes de validar o corpo do programa.
