# Lume

**Uma linguagem de programação independente, com sintaxe em português brasileiro.**

A Lume é uma linguagem interpretada criada para que instruções de programação sejam escritas em português. Seu interpretador tem analisador léxico, analisador sintático, árvore de sintaxe abstrata e ambiente de execução próprios. A execução não usa inteligência artificial, conexão com a internet, `eval` ou execução de código Python fornecido pelo programa.

> **Estado do projeto:** versão inicial `0.3.0` (alfa). A base do interpretador e os recursos descritos como implementados estão cobertos por testes. A linguagem ainda não deve ser considerada estável ou pronta para aplicações críticas.

## Primeiro programa

Para um passo a passo do primeiro programa até módulos e arquivos, consulte o [Guia de início rápido](docs/guia-iniciante.md).

Salve o conteúdo abaixo como `ola.lume`:

```text
mostrar "Olá, mundo!"
```

Execute:

```bash
python -m lume ola.lume
```

Para verificar a sintaxe sem executar:

```bash
python -m lume --verificar ola.lume
```

## Instalação para desenvolvimento

Requisitos: Python 3.10 ou superior. O interpretador não usa dependências de terceiros.

```bash
git clone https://github.com/souhelin/lume.git
cd lume
python -m pip install -e .
lume exemplos/ola.lume
```

Também é possível executar sem instalar o comando:

```bash
python -m lume exemplos/ola.lume
```

No Android com Termux, instale Python e Git e use os mesmos comandos:

```bash
pkg update
pkg install python git
git clone https://github.com/souhelin/lume.git
cd lume
python -m pip install .
lume exemplos/ola.lume
```

Ao executar `lume` sem indicar um arquivo, a linguagem abre um console interativo. Ele preserva o ambiente entre comandos e aceita blocos de várias linhas encerrados por fim. O front-end semântico também pode ser usado no REPL.

## Exemplos da linguagem

### Variáveis e cálculos

```text
definir nome como "Ana"
definir anos como 20
definir proximo_ano como anos + 1

mostrar "Olá", nome
mostrar "No próximo ano você terá", proximo_ano
```

`definir nome como valor` cria uma variável. Para atualizar uma variável existente, use `nome = valor`. A forma `definir nome = valor` também é aceita para declaração.

### Condições

```text
se anos maior ou igual a 18 então
    mostrar "Maior de idade"
senão
    mostrar "Menor de idade"
fim
```

### Repetição

```text
para cada numero em intervalo(1, 5) faça
    mostrar numero
fim
```

O limite final de `intervalo(inicio, fim)` é inclusivo. Também é possível informar um passo: `intervalo(10, 2, -2)`.

### Funções

```text
função dobro(numero) faça
    retornar numero * 2
fim

mostrar dobro(21)
```

### Listas

```text
definir cores como ["azul", "verde", "amarelo"]
mostrar "Quantidade:", comprimento(cores)

para cada cor em cores faça
    mostrar cor
fim
```

Mais exemplos executáveis estão em [`exemplos/`](exemplos/).

## Recursos implementados na versão 0.3.0

- Palavras-chave e identificadores em português, com suporte a acentos e Unicode.
- Textos, inteiros, decimais, valores lógicos, valor nulo e listas com acesso por índice (inclusive índices negativos).
- Variáveis, reatribuição de valores e operações matemáticas.
- Comparações com símbolos (`>=`) ou expressões (`maior ou igual a`).
- Operadores lógicos `e`, `ou` e `não`, com avaliação de curto-circuito.
- Condições `se`, `senão` e `senão se`.
- Repetições `enquanto` e `para cada`.
- Funções, parâmetros, retorno e recursão.
- Entrada por `perguntar(...)` e saída por `mostrar` ou `exibir`.
- Biblioteca padrão modularizada para conversões, listas, intervalos, textos, entrada e saída de arquivos.
- Limite padrão de 100.000 etapas por execução, até 100.000 itens por coleção e limites para operações numéricas.
- Mensagens de erro em português e verificação de sintaxe pela CLI, atribuição por índice e tratamento estruturado de erros.

## Sistema semântico de português

O projeto inclui um front-end semântico determinístico para um conjunto documentado de instruções naturais. Ele reconhece padrões controlados, resolve referências explícitas no contexto, converte as intenções em uma representação intermediária (IR) e valida nomes, chamadas e compatibilidade básica de tipos antes da execução. Não usa IA, internet ou serviços externos.

Exemplo:

~~~text
crie uma variável chamada idade com valor 18
mostre idade
exiba idade
some idade e 2

se idade for maior que 17 então
    apresente "Maior de idade"
caso contrário
    apresente "Menor de idade"
fim
~~~

Também são reconhecidas a declaração equivalente "declare uma variável idade e atribua a ela o número 18", atribuição contextual, operações matemáticas por verbo, comparações explícitas, repetição contada, funções e operações de lista. "mostre", "exiba" e "apresente" são sinônimos semânticos da operação exibir.

A flexibilidade é intencionalmente limitada: frases não previstas não são adivinhadas, e comparações sem operador são rejeitadas como ambíguas. O dicionário pode ser expandido pela API Python, mas um novo termo só se torna executável quando sua regra é implementada e testada.

Use "lume --semantico programa.lume" para forçar esse front-end ou "lume --tradicional programa.lume" para usar a gramática estruturada anterior. A CLI também seleciona automaticamente algumas construções naturais exclusivas. Consulte [docs/semantica.md](docs/semantica.md) para o vocabulário, padrões reconhecidos, API e limites.

## Funções disponíveis

| Função | Uso |
|---|---|
| comprimento(valor) | Quantidade de caracteres ou itens de uma lista. |
| texto(valor) | Converte um valor em texto. |
| numero(valor) | Converte para inteiro ou decimal quando possível. Aceita vírgula decimal em textos. |
| inteiro(valor) | Converte para inteiro. |
| decimal(valor) | Converte para decimal. |
| tipo(valor) | Informa o tipo do valor. |
| perguntar(mensagem) | Solicita um texto ao usuário. |
| intervalo(inicio, fim, passo) | Cria uma lista de números inteiros; início e fim são inclusivos. O passo é opcional. |
| somar(lista) | Soma os números de uma lista. |
| minimo(lista) / maximo(lista) | Menor ou maior elemento de uma lista não vazia. |
| arredondar(numero, casas) | Arredonda um número; casas é opcional. |
| maiusculas(texto) / minusculas(texto) | Altera a caixa de um texto. |
| adicionar(lista, valor) | Adiciona um item ao final e devolve o novo tamanho. |
| inserir(lista, indice, valor) | Insere um item em uma posição. |
| remover(lista, indice) | Remove e devolve o item da posição indicada. |
| contem(colecao, valor) | Verifica se um texto ou lista contém um valor. |
| ordenar(lista) | Devolve uma nova lista ordenada. |
| inverter(colecao) | Devolve uma cópia invertida de uma lista ou texto. |
| juntar(lista, separador) | Une uma lista de textos usando um separador. |

## Verificações

Execute a suíte de testes com a biblioteca padrão do Python:

```bash
python -m unittest discover -s testes -v
```

## Arquitetura

```text
Código .lume
    ↓
Analisador léxico (lexer.py)
    ↓
Tokens (tokens.py)
    ↓
Analisador sintático (parser.py)
    ↓
Árvore de sintaxe abstrata (nos.py)
    ↓
Interpretador (interpretador.py)
    ↓
Ambiente de execução (ambiente.py)
```

A gramática estruturada está em [docs/sintaxe.md](docs/sintaxe.md), e o front-end semântico em [docs/semantica.md](docs/semantica.md). A arquitetura está descrita em [`docs/arquitetura.md`](docs/arquitetura.md), e as etapas planejadas estão em [`docs/roteiro.md`](docs/roteiro.md).

## Segurança e limites atuais

A Lume não expõe comandos para executar código Python nem carregar módulos Python arbitrários. A importação de módulos Lume e as funções de arquivo ficam confinadas ao diretório raiz do projeto definido pela CLI. Isso reduz a superfície de risco, mas não torna a execução de programas desconhecidos automaticamente segura: um programa ainda pode consumir tempo e memória dentro dos limites do interpretador. Não execute código de origem desconhecida em ambientes sensíveis.

A gramática natural ainda é um conjunto de padrões controlados, não compreensão irrestrita do português. O validador semântico faz inferência parcial; operações que dependem de valores disponíveis apenas em execução continuam sendo verificadas pelo interpretador. O uso de Python 3.10+ é um requisito do interpretador de referência desta fase; isso não impede que uma implementação nativa própria seja criada futuramente.

## Licença

Distribuído sob a licença MIT. Consulte [`LICENSE`](LICENSE).


## Tratamento de erros e atualização de listas

A Lume permite atualizar itens de listas e tratar erros previsíveis:

```text
definir notas como [7, 8, 9]
notas[1] = 10

tente
    lance "exemplo de erro"
capture erro
    mostrar erro
finalmente
    mostrar "execução encerrada"
fim
```

Consulte [docs/sintaxe.md](docs/sintaxe.md) para as regras e limitações.


## Módulos e arquivos locais

A Lume suporta importação de módulos .lume e operações de leitura e escrita de texto UTF-8. Por padrão, a CLI define a pasta do arquivo principal como raiz do projeto. Importações e operações de arquivo ficam confinadas a essa raiz; arquivos e módulos têm limite de 1 MiB, e ciclos de importação são rejeitados.

~~~text
importar "apoio.lume"
escrever_arquivo("resultado.txt", "Olá")
mostrar ler_arquivo("resultado.txt")
~~~

A importação atual compartilha o ambiente do programa e não oferece namespaces ou importações seletivas. Consulte a gramática para as restrições completas.


## Formatação

A CLI pode normalizar a indentação de blocos sem alterar o conteúdo dos textos:

~~~bash
lume --formatar programa.lume
lume --formatar --gravar programa.lume
~~~

Sem --gravar, o resultado vai para a saída padrão e o arquivo original permanece intacto. O formatador normaliza recuo e espaços externos; não reescreve expressões nem aplica um estilo de pontuação.


A biblioteca padrão está isolada em lume/biblioteca.py, separada do núcleo de avaliação e execução.


A integração contínua também constrói o wheel e testa sua instalação em um ambiente virtual temporário, fora da árvore do repositório. Consulte scripts/validar_wheel.py.


## Publicação de versões

A publicação é acionada por uma tag v* e executa novamente os testes, constrói o wheel, valida a instalação isolada e anexa o pacote ao GitHub Releases. Nenhuma release é publicada automaticamente a partir de pull requests ou commits comuns.
