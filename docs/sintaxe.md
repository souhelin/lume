# Sintaxe da Lume — versão 0.1.0

Este documento define a sintaxe aceita pelo interpretador inicial. A linguagem é sensível a quebras de linha para separar instruções, mas não a maiúsculas/minúsculas em identificadores e palavras-chave. Identificadores são normalizados em Unicode NFC.

## Regras gerais

- Cada instrução ocupa uma linha.
- Espaços e tabulações antes das instruções são ignorados; a indentação é visual e não define blocos.
- `#` inicia um comentário até o fim da linha.
- Textos usam aspas simples ou duplas. Escapes aceitos: `\\`, `\"`, `\'`, `\n`, `\t` e `\r`.
- Blocos são encerrados com `fim`.
- O idioma das palavras-chave é português brasileiro.

## Instruções

```text
mostrar expressão
exibir expressão

definir nome como expressão
definir nome = expressão
nome = expressão

se condição então
    instruções
senão
    instruções
fim

enquanto condição faça
    instruções
fim

para cada item em coleção faça
    instruções
fim

função nome(parâmetro1, parâmetro2) faça
    instruções
    retornar expressão
fim

interromper
continuar
```

`senão se` também é aceito entre o bloco `se` e o bloco `senão` final. `retornar` sem valor devolve `nulo`.

`interromper` encerra o laço mais próximo e `continuar` inicia sua próxima iteração. Ambos só podem ser usados dentro de um laço.

## Valores

| Tipo | Exemplos |
|---|---|
| Inteiro | `0`, `42`, `-7` |
| Decimal | `3.14`, `0.5` |
| Texto | `"Olá"`, `'Lume'` |
| Lógico | `verdadeiro`, `falso` |
| Nulo | `nulo` |
| Lista | `[1, 2, 3]`, `["azul", "verde"]` |

## Operadores

| Grupo | Operadores |
|---|---|
| Lógicos | `ou`, `e`, `não` |
| Comparação | `==`, `!=`, `<`, `<=`, `>`, `>=`, `igual a`, `diferente de`, `menor que`, `maior que`, `menor ou igual a`, `maior ou igual a` |
| Aritméticos | `+`, `-`, `*`, `/`, `//`, `%`, `**` |
| Agrupamento | `(expressão)` |

Precedência, da maior para a menor: agrupamento e chamadas, potência, multiplicação/divisão, soma/subtração, comparação, `e`, `ou`. A potência é associativa à direita. Os operadores `e` e `ou` usam avaliação de curto-circuito.

`+` aceita dois números, dois textos ou duas listas. Listas e textos aceitam leitura por índice com `colecao[indice]`; índices negativos contam a partir do final. Índices fora dos limites geram erro. Acesso por índice não permite atribuição direta. Comparações ordenadas aceitam dois números ou dois textos do mesmo tipo.

## Identificadores

Identificadores começam com letra Unicode ou `_` e podem continuar com letras, números ou `_`. Acentos são aceitos. Palavras-chave e nomes de variáveis não diferenciam maiúsculas de minúsculas; por isso, `Nome` e `nome` identificam a mesma variável.

## Entrada, saída e funções nativas

A saída é feita por `mostrar` ou `exibir`. É possível informar vários valores separados por vírgula:

```text
mostrar "Resultado:", 2 + 2
```

A entrada usa `perguntar("Mensagem: ")`, que devolve um texto.

A biblioteca padrão inclui `adicionar(lista, valor)`, `inserir(lista, indice, valor)`, `remover(lista, indice)`, `contem(colecao, valor)`, `ordenar(lista)`, `inverter(colecao)` e `juntar(lista_de_textos, separador)`, além das conversões e funções descritas no README. Chamadas usam parênteses e argumentos separados por vírgula.

## Limites da versão inicial

A versão 0.1.0 não possui mapas/dicionários, atribuição por índice, propriedades, classes, importação de módulos, manipulação de arquivos, exceções escritas pelo usuário, tipagem estática, interpolação de textos ou sintaxe de bloco em uma única linha. Esses recursos não devem ser presumidos como disponíveis.


## Front-end semântico

Além das instruções estruturadas acima, o front-end semântico reconhece construções naturais documentadas:

~~~text
crie uma variável chamada idade com valor 18
declare uma variável idade e atribua a ela o número 18
mostre idade
exiba idade
apresente idade
atribua 19 à variável idade
some 2 e 3
subtraia 5 de 10
multiplique 3 por 4
divida 20 por 5
compare idade maior que 17
repita 3 vezes
fim da repetição
~~~

O front-end também reconhece condições iniciadas por "se ... então", "caso contrário", funções introduzidas por "defina uma função chamada ...", retornos com "retorne" e operações básicas sobre listas. A lista de padrões completos e os exemplos estão em [semantica.md](semantica.md).

Esses padrões não substituem a gramática tradicional nem permitem qualquer frase livre. Uma frase fora dos padrões é rejeitada; relações incompletas ou conflituosas geram diagnósticos semânticos. A forma canônica pode continuar usando a gramática estruturada e ambos os front-ends compartilham o mesmo executor.


## Atribuição por índice

Listas permitem atualizar um elemento existente usando um índice inteiro:

```text
definir notas como [7, 8, 9]
notas[1] = 10
mostrar notas
```

A atribuição por índice só aceita listas mutáveis. Textos e tuplas não podem ser alterados por índice. Índices negativos seguem a mesma regra de acesso; índices fora dos limites produzem erro.

## Tratamento estruturado de erros

Um bloco `tente` pode capturar erros de execução e executar uma etapa final:

```text
tente
    lance "não foi possível concluir"
capture erro
    mostrar erro
finalmente
    mostrar "etapa encerrada"
fim
```

`capture` pode receber um identificador opcional para armazenar a mensagem do erro. `finalmente` é opcional e é executado mesmo quando o erro não é capturado. `lance` interrompe o fluxo atual com um erro de execução. O mecanismo captura erros da linguagem, não exceções arbitrárias do processo hospedeiro.


## Módulos locais

Um programa pode carregar outro arquivo Lume com:

~~~text
importar "apoio.lume"
~~~

O caminho é relativo ao diretório do arquivo principal executado pela CLI. O módulo é executado uma única vez por instância do interpretador; novas importações do mesmo caminho reutilizam o módulo carregado. Ciclos de importação são rejeitados. As declarações do módulo são disponibilizadas no ambiente compartilhado do programa; esta versão ainda não oferece espaços de nomes nem importação seletiva.

Módulos precisam usar a extensão .lume, estar dentro do diretório raiz do projeto e ter no máximo 1 MiB. Caminhos absolutos e travessia para fora do projeto são rejeitados.

## Biblioteca de arquivos

A biblioteca padrão fornece:

- ler_arquivo(caminho): lê texto UTF-8.
- escrever_arquivo(caminho, texto): cria ou substitui um arquivo.
- anexar_arquivo(caminho, texto): acrescenta texto ao final.
- existe_arquivo(caminho): verifica se um arquivo existe.

Os caminhos são relativos ao diretório raiz do projeto, não podem escapar dele e os arquivos são limitados a 1 MiB. Os diretórios pais precisam existir. A biblioteca não oferece acesso a arquivos fora dessa raiz. Isso é uma restrição de escopo, não uma sandbox de segurança contra código hostil.


## Formatação automática

O comando lume --formatar arquivo.lume valida a fonte e normaliza o recuo de blocos para quatro espaços. lume --formatar --gravar arquivo.lume grava o resultado no arquivo original; sem --gravar, imprime o resultado sem modificar a fonte. O formatador preserva o conteúdo dos textos e não reescreve expressões.


Importações devem ficar no início do arquivo, antes de declarações, expressões ou blocos. A validação estática carrega recursivamente os módulos, verifica ciclos e disponibiliza seus nomes para validar o restante do programa. Importações dentro de blocos não são permitidas.
