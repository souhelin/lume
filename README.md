# Lume

**Uma linguagem de programação independente, com sintaxe em português brasileiro.**

A Lume é uma linguagem interpretada criada para que instruções de programação sejam escritas em português. Seu interpretador tem analisador léxico, analisador sintático, árvore de sintaxe abstrata e ambiente de execução próprios. A execução não usa inteligência artificial, conexão com a internet, `eval` ou execução de código Python fornecido pelo programa.

> **Estado do projeto:** versão inicial `0.1.0` (alfa). A base do interpretador e os recursos descritos como implementados estão cobertos por testes. A linguagem ainda não deve ser considerada estável ou pronta para aplicações críticas.

## Primeiro programa

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

Ao executar `lume` sem indicar um arquivo, a linguagem abre um console interativo. Na versão atual, ele aceita instruções completas de uma linha; blocos como `se`, `enquanto` e `função` devem ser escritos em arquivos `.lume`.

## Exemplos da linguagem

### Variáveis e cálculos

```text
definir nome como "Ana"
definir anos como 20
definir proximo_ano como anos + 1

mostrar "Olá", nome
mostrar "No próximo ano você terá", proximo_ano
```

`definir nome como valor` cria ou atualiza uma variável no ambiente atual. A forma `definir nome = valor` também é aceita.

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

## Recursos implementados na versão 0.1.0

- Palavras-chave e identificadores em português, com suporte a acentos e Unicode.
- Textos, inteiros, decimais, valores lógicos, valor nulo e listas.
- Variáveis e operações matemáticas.
- Comparações com símbolos (`>=`) ou expressões (`maior ou igual a`).
- Operadores lógicos `e`, `ou` e `não`, com avaliação de curto-circuito.
- Condições `se`, `senão` e `senão se`.
- Repetições `enquanto` e `para cada`.
- Funções, parâmetros, retorno e recursão.
- Entrada por `perguntar(...)` e saída por `mostrar` ou `exibir`.
- Funções nativas para conversões, listas, intervalos e textos.
- Limite padrão de 100.000 etapas por execução, até 100.000 itens por coleção e limites para operações numéricas.
- Mensagens de erro em português e verificação de sintaxe pela CLI.

## Funções disponíveis

| Função | Uso |
|---|---|
| `comprimento(valor)` | Quantidade de caracteres ou itens de uma lista. |
| `texto(valor)` | Converte um valor em texto. |
| `numero(valor)` | Converte para inteiro ou decimal quando possível. Aceita vírgula decimal em textos. |
| `inteiro(valor)` | Converte para inteiro. |
| `decimal(valor)` | Converte para decimal. |
| `tipo(valor)` | Informa o tipo do valor. |
| `perguntar(mensagem)` | Solicita um texto ao usuário. |
| `intervalo(inicio, fim, passo)` | Cria uma lista de números inteiros; início e fim são inclusivos. O passo é opcional. |
| `somar(lista)` | Soma os números de uma lista. |
| `minimo(lista)` / `maximo(lista)` | Menor ou maior elemento de uma lista não vazia. |
| `arredondar(numero, casas)` | Arredonda um número; casas é opcional. |
| `maiusculas(texto)` / `minusculas(texto)` | Altera a caixa de um texto. |

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

A gramática e as decisões de sintaxe estão em [`docs/sintaxe.md`](docs/sintaxe.md). A arquitetura está descrita em [`docs/arquitetura.md`](docs/arquitetura.md), e as etapas planejadas estão em [`docs/roteiro.md`](docs/roteiro.md).

## Segurança e limites atuais

A Lume não expõe comandos para executar código Python, carregar módulos arbitrários ou acessar arquivos do sistema na versão inicial. Isso reduz a superfície de risco, mas não torna a execução de programas desconhecidos automaticamente segura: um programa ainda pode consumir tempo e memória dentro dos limites do interpretador. Não execute código de origem desconhecida em ambientes sensíveis.

A biblioteca padrão, o modelo de módulos, o tratamento de erros recuperáveis e a análise semântica dedicada ainda serão ampliados. O uso de Python 3.10+ é um requisito do interpretador de referência desta fase; isso não impede que uma implementação nativa própria seja criada futuramente.

## Licença

Distribuído sob a licença MIT. Consulte [`LICENSE`](LICENSE).
