# Sistema semântico nativo

**Estado:** implementação inicial determinística e local, com gramática de linguagem natural controlada.

O sistema semântico permite escrever operações selecionadas como instruções em português. Ele não tenta interpretar qualquer frase como código: cada construção precisa corresponder a um padrão documentado e ter argumentos verificáveis. Na ausência de informação suficiente, a compilação falha com um diagnóstico em português.

## Fluxo de compilação e execução

~~~text
Fonte em português
    ↓
Análise lexical e posições
    ↓
Reconhecimento de vocabulário e padrões semânticos
    ↓
Normalização para formas canônicas da gramática
    ↓
Análise sintática e AST
    ↓
Representação intermediária (IR)
    ↓
Validação semântica e do contexto
    ↓
Conversão para nós executáveis
    ↓
Interpretador da Lume
~~~

A gramática estruturada anterior permanece disponível. O modo automático da CLI seleciona o front-end semântico quando encontra construções naturais exclusivas; --semantico e --tradicional permitem escolher explicitamente.

## Dicionário extensível

O módulo lume.vocabulario fornece:

- EntradaSemantica: expressão, significado, categoria, intenção, operações, relações, regras e ambiguidades.
- DicionarioSemantico: registro, consulta, busca por intenção e reconhecimento de expressões.
- DICIONARIO_PADRAO: vocabulário embutido da linguagem.
- criar_dicionario_padrao(): cria uma cópia expansível do dicionário oficial.

Exemplo de extensão:

~~~python
from lume.vocabulario import criar_dicionario_padrao
from lume.semantica import CompiladorSemantico

dicionario = criar_dicionario_padrao()
dicionario.registrar(
    "revele",
    "Apresentar uma informação.",
    categoria="verbo",
    intencao="exibir",
    operacoes=("saída",),
)

compilador = CompiladorSemantico(dicionario)
resultado = compilador.compilar('revele "Olá"')
~~~

O dicionário guarda conhecimento declarativo. Registrar um novo sinônimo não cria uma operação nova por si só: a intenção precisa ter uma regra de tradução implementada. Termos registrados com intenções conflitantes são tratados como ambíguos.

## Construções naturais suportadas

Os padrões abaixo são a gramática semântica inicial. Espaços extras e diferenças de maiúsculas/minúsculas são tolerados; acentos fazem parte da grafia oficial. Textos entre aspas preservam a caixa original.

### Declaração e saída

~~~text
crie uma variável chamada idade com valor 18
mostre idade
exiba idade
apresente idade
~~~

A declaração equivalente também é aceita:

~~~text
declare uma variável idade e atribua a ela o número 18
~~~

mostre, exiba e apresente representam a operação canônica exibir.

### Atribuição e contexto

~~~text
crie uma variável chamada idade com valor 18
atribua 19 à variável idade
atribua 20 a ela
mostre idade
~~~

A referência pronominal ela ou ele depende do último alvo de variável declarado ou atribuído no contexto semântico. Sem um alvo anterior inequívoco, a compilação apresenta ambiguidade. Para código duradouro, prefira nomear o destino explicitamente.

Atribuição só altera variável existente. Para criar, use crie ou declare.

### Operações matemáticas

~~~text
some 2 e 3
subtraia 5 de 10
multiplique 3 por 4
divida 20 por 5

some 2 e 3 e guarde em total
~~~

Sem destino, a operação matemática é exibida. Com guarde em nome, o resultado é declarado se o nome ainda não existir ou atribuído se já existir. Subtração lê a frase na ordem natural: subtraia A de B corresponde a B - A.

### Comparação

~~~text
compare idade maior que 17
compare idade menor ou igual a 18
compare idade com 18 usando igual a
~~~

As relações aceitas são maior que, menor que, maior ou igual a, menor ou igual a, igual a e diferente de. A forma compare A com B sem operador é ambígua e é rejeitada.

### Condições

~~~text
se idade for maior que 17 então
    mostre "maior"
caso contrário
    mostre "menor"
fim
~~~

Os blocos continuam sendo delimitados por fim. caso contrário equivale a senão.

### Repetições contadas

~~~text
crie uma variável chamada contador com valor 0
repita 3 vezes
    atribua contador + 1 a ela
fim da repetição
mostre contador
~~~

A expressão de quantidade deve produzir um inteiro aceito por intervalo. A repetição usa o limite geral de etapas do interpretador. fim da repetição equivale a fim.

### Funções

~~~text
defina uma função chamada dobro com parâmetros numero
    retorne numero * 2
fim da função

mostre dobro(5)
~~~

Parâmetros múltiplos podem ser separados por vírgulas ou por e. A sintaxe de chamada de função continua usando parênteses e argumentos separados por vírgulas.

### Listas

~~~text
crie uma variável chamada itens com valor [1, 2]
adicione 3 à lista itens
remova o último item da lista itens
mostre itens
~~~

Também é aceita a remoção pelo índice: remova o índice 0 da lista itens.

## Contexto e validação

ContextoSemantico mantém nomes de variáveis, funções, tipos conhecidos e o último alvo de variável. CompiladorSemantico analisa e valida a unidade antes da execução. InterpretadorSemantico conserva o contexto entre chamadas e reconcilia símbolos existentes no ambiente de execução para permitir mistura com comandos legados.

A validação atual verifica, entre outros pontos:

- referências e alvos de atribuição inexistentes;
- chamadas de função e quantidade de argumentos;
- operações aritméticas e comparações com tipos evidentemente incompatíveis;
- tipo de coleção e índice quando conhecidos;
- uso de retornar, interromper e continuar fora do contexto permitido;
- expressões sem padrão reconhecido e ambiguidades semânticas.

A inferência de tipos é deliberadamente conservadora e parcial. Quando o tipo de uma expressão depende de dados disponíveis apenas em execução, o validador pode não conseguir decidir; o interpretador continua responsável pelas verificações dinâmicas.

## API de programação

~~~python
from lume import InterpretadorSemantico

interpretador = InterpretadorSemantico()
resultado = interpretador.verificar(
    "crie uma variável chamada idade com valor 18\nmostre idade"
)
# resultado.programa contém a IR validada.

interpretador.executar(
    "crie uma variável chamada idade com valor 18\nmostre idade"
)
~~~

CompiladorSemantico.compilar(fonte) retorna um ResultadoCompilacao com a IR, a fonte canônica e o contexto resultante. ProgramaIR.para_dicionario() disponibiliza uma representação serializável da estrutura intermediária.

## CLI e REPL

~~~bash
lume programa.lume
lume --semantico programa.lume
lume --tradicional programa.lume
lume --semantico --verificar programa.lume
~~~

Sem --semantico ou --tradicional, a CLI identifica algumas formas naturais exclusivas e seleciona automaticamente o front-end semântico. O REPL compartilha o ambiente de execução e aceita blocos encerrados por fim.

## Garantias e limites

- O mecanismo é local, determinístico e não depende de IA, rede, APIs ou serviços externos.
- A execução não transforma a fonte em Python e não usa eval ou exec.
- A mesma frase e o mesmo contexto geram a mesma IR e o mesmo efeito, ressalvadas entradas explícitas do programa e estado externo fornecido pelo usuário.
- A gramática semântica é um conjunto finito e explícito de padrões. Português irrestrito, paráfrases inéditas, resolução geral de pronomes e compreensão de intenção implícita não fazem parte desta versão.
- Uma expressão nova no dicionário não passa a ser executável automaticamente. A operação e sua regra precisam ser implementadas e testadas.
- Esta etapa não adiciona módulos, arquivos, exceções definidas pelo usuário ou tipagem estática completa.


## Recursos estruturados disponíveis no front-end semântico

Como o front-end semântico compartilha o parser, a IR e o executor, também aceita as construções estruturadas de atribuição por índice e tratamento de erros:

```text
crie uma variável chamada itens com valor [1, 2]
itens[0] = 8

tente
    lance "falha esperada"
capture erro
    mostre erro
finalmente
    mostre "finalizado"
fim
```

A validação semântica verifica se o destino de atribuição por índice é uma lista quando o tipo é conhecido, e se o índice é inteiro. O tratamento captura erros de execução da Lume e não intercepta falhas arbitrárias do processo Python.


## Módulos e arquivos

As instruções estruturadas importar "apoio.lume" e as funções ler_arquivo, escrever_arquivo, anexar_arquivo e existe_arquivo também estão disponíveis no front-end semântico. A validação verifica os nomes e a quantidade de argumentos; a existência, permissões e conteúdo dos arquivos são verificados em execução.


A validação feita por InterpretadorSemantico também resolve módulos locais declarados no início do arquivo. O verificador lê e analisa os módulos sem executar seus efeitos; os módulos continuam sendo executados no ponto da instrução importar durante a execução real.


## Inferência conservadora de tipos e fluxo

O validador mantém tipos conhecidos em declarações e atribuições. Em condicionais, repetições e blocos de tratamento, mescla os caminhos possíveis. Se os caminhos produzirem tipos diferentes, o tipo passa a desconhecido e a verificação é adiada para o runtime; a Lume continua sendo dinamicamente tipada. Nomes criados em apenas um ramo ou dentro de uma repetição que pode executar zero vezes não são considerados garantidos fora do bloco.
