# Guia de início rápido da Lume

Este guia acompanha a versão 0.3.0. Os exemplos usam a gramática estruturada, que é a forma mais explícita e estável de escrever programas. O front-end semântico aceita também um conjunto documentado de instruções naturais em português.

## 1. Instalar

Requisitos: Python 3.10 ou superior.

~~~bash
git clone https://github.com/souhelin/lume.git
cd lume
python -m pip install .
~~~

Confira a instalação:

~~~bash
lume --versao
lume exemplos/ola.lume
~~~

No Android, os mesmos comandos funcionam no Termux após instalar Python e Git.

## 2. Primeiro programa

Crie um arquivo chamado ola.lume:

~~~text
mostrar "Olá, mundo!"
~~~

Execute:

~~~bash
lume ola.lume
~~~

Para verificar sem executar:

~~~bash
lume --verificar ola.lume
~~~

## 3. Variáveis e tipos

~~~text
definir nome como "Lia"
definir idade como 16
definir altura como 1.65
definir estudante como verdadeiro
definir resposta como nulo

mostrar nome
mostrar idade
mostrar tipo(altura)
~~~

Os tipos básicos são texto, inteiro, decimal, lógico e nulo. Listas são coleções ordenadas.

Para alterar uma variável existente, use atribuição:

~~~text
idade = idade + 1
~~~

## 4. Condições

~~~text
se idade maior ou igual a 18 então
    mostrar "Maior de idade"
senão
    mostrar "Menor de idade"
fim
~~~

Operadores de comparação: igual a, diferente de, maior que, menor que, maior ou igual a e menor ou igual a. Operadores lógicos: e, ou e não.

## 5. Repetições

~~~text
para cada numero em intervalo(1, 5) faça
    mostrar numero
fim
~~~

O intervalo inclui o início e o fim. Também pode receber um passo:

~~~text
para cada numero em intervalo(10, 2, -2) faça
    mostrar numero
fim
~~~

Uma repetição condicional usa enquanto:

~~~text
definir contador como 0
enquanto contador menor que 3 faça
    mostrar contador
    contador = contador + 1
fim
~~~

## 6. Funções

~~~text
função dobro(numero) faça
    retornar numero * 2
fim

mostrar dobro(21)
~~~

Funções podem receber vários parâmetros separados por vírgula e devolver um resultado com retornar.

## 7. Listas

~~~text
definir notas como [7, 8, 9]
notas[1] = 10
adicionar(notas, 6)
mostrar notas
mostrar comprimento(notas)
~~~

Índices começam em zero. Índices negativos contam a partir do final. A atribuição por índice só funciona em listas.

## 8. Tratamento de erros

~~~text
tente
    lance "operação não concluída"
capture erro
    mostrar erro
finalmente
    mostrar "fim da tentativa"
fim
~~~

A captura recebe erros de execução da Lume. O bloco finalmente é executado mesmo quando o erro não é capturado.

## 9. Módulos e arquivos

Crie apoio.lume:

~~~text
definir saudacao como "Olá, pessoa!"
~~~

No programa principal:

~~~text
importar "apoio.lume"
mostrar saudacao
escrever_arquivo("resultado.txt", saudacao)
mostrar ler_arquivo("resultado.txt")
~~~

Módulos e arquivos ficam confinados à pasta raiz do projeto definida pela CLI. O tamanho máximo de módulos, leituras e escritas é 1 MiB. Importações usam o mesmo ambiente e não têm namespaces nesta versão.

## 10. Português natural controlado

O front-end semântico aceita, entre outros padrões:

~~~text
crie uma variável chamada idade com valor 18
mostre idade
some idade e 2
compare idade maior que 17
~~~

Também reconhece sinônimos documentados, como mostre, exiba e apresente. Ele não interpreta qualquer frase livre: uma instrução fora da gramática reconhecida deve ser reescrita.

Use:

~~~bash
lume --semantico programa.lume
lume --tradicional programa.lume
~~~

## 11. Formatar e diagnosticar

~~~bash
lume --formatar programa.lume
lume --formatar --gravar programa.lume
~~~

A formatação normaliza o recuo de blocos. Sem --gravar, o arquivo original não é alterado. Erros de sintaxe, semântica e execução mostram a localização quando disponível.

## 12. Próximos passos

- Consulte docs/sintaxe.md para a gramática completa.
- Consulte docs/semantica.md para padrões naturais reconhecidos.
- Consulte docs/arquitetura.md para os componentes internos.
- Execute python -m unittest discover -s testes -v para rodar os testes.
- Veja exemplos/ para programas completos.

## Exercícios

1. Crie duas variáveis numéricas e mostre a soma.
2. Faça uma função que receba um número e devolva seu quadrado.
3. Percorra uma lista e mostre apenas os números maiores que cinco.
4. Escreva um texto em arquivo e leia-o novamente.
5. Importe um módulo local e utilize uma variável declarada nele.
