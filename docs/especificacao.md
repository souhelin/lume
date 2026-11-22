# Especificação da linguagem Lume

**Edição:** 0.3.0  
**Estado:** especificação de referência em evolução; a gramática ainda não recebeu garantia de estabilidade 1.0.

Este documento define o comportamento observável da implementação de referência. As palavras “deve”, “não deve” e “pode” indicam, respectivamente, requisito obrigatório, proibição e comportamento opcional.

## 1. Fonte e caracteres

1. Arquivos-fonte devem ser codificados em UTF-8.
2. A linguagem aceita identificadores Unicode e normaliza identificadores para NFC e comparação sem distinção de caixa.
3. Textos entre aspas preservam caixa e conteúdo.
4. Espaços e tabulações separam tokens; quebras de linha separam instruções.
5. O caractere # inicia comentário até o final da linha, exceto dentro de um texto.
6. Pontuação terminal pode ser aceita pelo front-end semântico fora de textos entre aspas.

## 2. Tokens

- Identificadores começam com letra Unicode ou sublinhado; os caracteres seguintes podem incluir letras, números e sublinhado.
- Números são inteiros decimais ou decimais com ponto.
- Textos usam aspas simples ou duplas.
- Sequências de escape aceitas: \n, \t, \r, \\, \", \'.
- Valores lógicos: verdadeiro e falso.
- Valor nulo: nulo.
- Comentários começam com #.

## 3. Gramática estruturada

A gramática abaixo é uma descrição resumida; a implementação do parser e os testes de conformidade são a referência para detalhes de precedência e mensagens de erro.

~~~text
programa          = { instrucao, quebra_de_linha } ;
instrucao         = mostrar | definir | atribuicao | condicional
                  | enquanto | para_cada | funcao | retornar
                  | interromper | continuar | tentar | importar
                  | lance | expressao ;
mostrar           = ("mostrar" | "exibir"), expressao, { ",", expressao } ;
definir           = "definir", identificador, ("como" | "="), expressao ;
atribuicao        = identificador, "=", expressao
                  | identificador, "[", expressao, "]", "=", expressao ;
condicional       = "se", expressao, "então", bloco,
                    [ "senão", bloco ], "fim" ;
enquanto          = "enquanto", expressao, "faça", bloco, "fim" ;
para_cada         = "para cada", identificador, "em", expressao,
                    "faça", bloco, "fim" ;
funcao            = "função", identificador, "(", [ parametros ], ")",
                    "faça", bloco, "fim" ;
retornar          = "retornar", [ expressao ] ;
tentar            = "tente", bloco, ( "capture", [ identificador ], bloco
                    | "finalmente", bloco
                    | "capture", [ identificador ], bloco, "finalmente", bloco ), "fim" ;
lance             = "lance", expressao ;
importar          = "importar", texto ;
~~~

A forma real dos blocos exige quebra de linha após os cabeçalhos. Cada bloco é encerrado por fim. As importações devem aparecer no início do arquivo, antes das demais instruções, e fora de blocos.

## 4. Expressões e precedência

Da menor para a maior precedência:

| Nível | Operadores |
|---|---|
| 1 | ou |
| 2 | e |
| 3 | ==, !=, menor, menor ou igual, maior, maior ou igual |
| 4 | +, - |
| 5 | *, /, //, % |
| 6 | ** |

A potência é associativa à direita. O operador unário não tem precedência menor que comparações; o sinal negativo é aplicado conforme a precedência do parser. Parênteses alteram a ordem de avaliação.

## 5. Tipos e valores

Os valores básicos são inteiro, decimal, texto, lógico e nulo. Listas são coleções mutáveis e ordenadas. Textos e tuplas podem ser consultados por índice, mas não alterados por índice.

- + aceita dois números, dois textos ou duas listas.
- Operações aritméticas exigem números.
- Comparações ordenadas aceitam dois números ou dois textos.
- e e ou usam avaliação de curto-circuito e a conversão lógica definida pelo runtime.
- Índices de listas e textos começam em zero; índices negativos contam do final.

## 6. Escopos e funções

Funções possuem parâmetros posicionais, fechamento léxico e retorno por retornar. Variáveis definidas dentro de um escopo local não substituem automaticamente variáveis externas. A atribuição procura um nome existente no escopo local e, depois, nos escopos anteriores.

Recursão é permitida, sujeita aos limites do interpretador e do Python hospedeiro.

## 7. Erros

Erros léxicos, sintáticos, semânticos e de execução são reportados em português. Quando a origem da instrução é conhecida, o diagnóstico deve incluir linha e coluna. O bloco capture intercepta erros de execução da Lume; não intercepta exceções arbitrárias do processo hospedeiro. finalmente é executado ao sair do bloco tente, inclusive quando há erro não capturado.

## 8. Módulos e arquivos

- importar recebe um caminho relativo a raiz do projeto.
- Módulos devem terminar em .lume, são executados uma vez por instância e ciclos são rejeitados.
- Módulos compartilham o ambiente do programa; não existem namespaces nem importações seletivas nesta edição.
- ler_arquivo, escrever_arquivo, anexar_arquivo e existe_arquivo operam somente dentro da raiz do projeto.
- Módulos e operações de arquivo têm limite de 1 MiB e usam UTF-8.
- Caminhos absolutos e travessia para fora da raiz são rejeitados.

## 9. Limites de execução

A implementação de referência limita a execução a 100.000 etapas por execução, coleções a 100.000 itens e resultados numéricos a limites defensivos. Arquivos e módulos têm limite de 1 MiB. Esses limites são valores de implementação documentados e podem ser configuráveis em edições futuras.

## 10. Front-end semântico

O front-end semântico reconhece somente padrões naturais documentados em docs/semantica.md. Não existe interpretação irrestrita de português. Sinônimos só são equivalentes quando registrados e ligados a uma regra de tradução implementada. Ambiguidades não devem ser resolvidas por suposição.

## 11. Independência

A implementação não deve depender de IA, rede, APIs ou execução dinâmica de código Python fornecido pelo programa. A AST, IR e o interpretador são os mecanismos de execução da Lume.
