# LUME — AGENTS.md

## 1. Identidade do projeto

**Nome:** Lume  
**Categoria:** Linguagem de programação  
**Idioma oficial:** Português brasileiro (pt-BR)  
**Modelo:** Linguagem interpretada  
**Filosofia:** Programação por linguagem textual natural, simples e acessível.

A Lume é uma linguagem de programação independente, desenvolvida para permitir que pessoas criem programas utilizando instruções em português, sem precisar escrever código tradicional em inglês.

A linguagem deve possuir sintaxe, gramática, regras e interpretador próprios.

## 2. Objetivo principal

Desenvolver uma linguagem de programação funcional, independente e acessível, na qual o português seja o idioma utilizado para escrever instruções e desenvolver aplicações.

A Lume deve:

- Eliminar a necessidade de conhecer comandos em inglês.
- Tornar a programação mais compreensível.
- Permitir a criação de programas reais.
- Possuir sintaxe simples e consistente.
- Ser independente de serviços de inteligência artificial.
- Permitir expansão para diferentes áreas da programação.
- Priorizar previsibilidade, estabilidade e desempenho.

## 3. Filosofia e princípios

Todos os desenvolvimentos devem respeitar estes princípios:

1. **Português primeiro:** o português brasileiro é o idioma oficial da linguagem.
2. **Simplicidade:** evitar estruturas desnecessariamente complexas.
3. **Clareza:** cada instrução deve ter significado compreensível.
4. **Consistência:** comandos semelhantes devem seguir padrões semelhantes.
5. **Independência:** a linguagem não deve depender de IA, internet ou serviços externos para executar programas.
6. **Transparência:** o funcionamento deve ser documentado.
7. **Evolução responsável:** novas funcionalidades não devem comprometer a compatibilidade.
8. **Acessibilidade:** iniciantes devem conseguir compreender a linguagem.

## 4. Modelo da linguagem

A Lume deve utilizar um modelo híbrido.

Isso significa:

- Comandos oficiais previamente definidos.
- Flexibilidade controlada na escrita.
- Possibilidade de diferentes expressões equivalentes.
- Regras gramaticais explícitas.
- Interpretação determinística.

Exemplo:

    mostrar "Olá, mundo!"

Também poderá aceitar expressões equivalentes, como:

    exibir "Olá, mundo!"

As duas instruções devem produzir o mesmo resultado, caso ambas sejam oficialmente suportadas.

Não permitir interpretações arbitrárias ou ambíguas.

## 5. Idioma e sintaxe

Regras obrigatórias:

- Utilizar português brasileiro.
- Aceitar acentos e caracteres Unicode.
- Utilizar palavras compreensíveis.
- Evitar palavras-chave em inglês.
- Utilizar nomes de comandos consistentes.
- Definir regras para espaços, pontuação e quebras de linha.
- Definir tratamento de maiúsculas e minúsculas.
- Manter mensagens de erro em português.

Identificadores criados pelos usuários também devem aceitar palavras em português.

Nomes técnicos internos podem utilizar convenções internacionais quando necessário, mas não devem aparecer como exigência para quem programa em Lume.

## 6. Funcionalidades fundamentais

A linguagem deve evoluir para oferecer:

### Operações básicas
- Exibição de informações.
- Entrada de dados.
- Variáveis.
- Tipos de dados.
- Operações matemáticas.
- Operações lógicas.

### Controle de execução
- Condições.
- Repetições.
- Funções.
- Parâmetros.
- Retornos.
- Tratamento de erros.

### Estruturas de dados
- Listas.
- Textos.
- Números.
- Valores lógicos.
- Coleções.

### Recursos avançados
- Manipulação de arquivos.
- Módulos.
- Bibliotecas.
- Tratamento de exceções.
- Programação assíncrona, quando viável.
- Integração com recursos do sistema operacional.

Não implementar todos os recursos de uma só vez. Priorizar uma base funcional e testável.

## 7. Arquitetura técnica

A Lume deve possuir uma arquitetura modular.

Componentes recomendados:

- Analisador léxico (Lexer).
- Analisador sintático (Parser).
- Árvore de sintaxe abstrata (AST).
- Validador semântico.
- Interpretador.
- Ambiente de execução.
- Biblioteca padrão.
- Sistema de erros.
- Testes automatizados.

O interpretador deve executar programas sem depender de um modelo de IA.

A IA poderá ser utilizada futuramente como ferramenta auxiliar de escrita, explicação e conversão, mas nunca como requisito para executar a linguagem.

## 8. Regras de desenvolvimento para agentes de IA

Todo agente que trabalhar no projeto deve:

1. Ler o AGENTS.md antes de modificar arquivos.
2. Respeitar a identidade e os objetivos da Lume.
3. Não alterar a filosofia original sem autorização.
4. Não substituir o português por inglês na sintaxe pública.
5. Não introduzir dependências desnecessárias.
6. Não criar funcionalidades fictícias ou incompletas apresentadas como concluídas.
7. Não remover funcionalidades existentes sem justificativa e autorização.
8. Preservar a compatibilidade sempre que possível.
9. Criar testes para funcionalidades novas.
10. Corrigir erros sem introduzir regressões.
11. Atualizar a documentação quando houver mudanças.
12. Explicar alterações importantes.
13. Evitar duplicação de código.
14. Priorizar código legível e modular.
15. Não modificar arquivos fora do escopo da tarefa sem necessidade.

## 9. O que deve ser mantido

Os seguintes elementos são fundamentais e não devem ser abandonados:

- Nome Lume.
- Português brasileiro como idioma oficial.
- Sintaxe própria.
- Interpretador independente.
- Filosofia de programação acessível.
- Execução sem dependência obrigatória de IA.
- Documentação em português.
- Arquitetura modular.
- Compatibilidade entre versões.
- Código aberto e transparência, conforme a licença definida pelo projeto.

## 10. O que evitar

Não transformar a Lume em:

- Um simples tradutor de Python.
- Um conjunto de comandos que apenas executam scripts externos.
- Um chatbot que simula programação.
- Uma linguagem dependente de inteligência artificial.
- Uma linguagem que exige internet para executar programas.
- Uma cópia de outra linguagem com palavras traduzidas.
- Um projeto com funcionalidades anunciadas, mas não implementadas.

A Lume deve possuir identidade técnica própria.

## 11. Qualidade e desempenho

Prioridades:

1. Correção da execução.
2. Segurança.
3. Estabilidade.
4. Desempenho.
5. Facilidade de manutenção.
6. Compatibilidade.

Evitar otimizações prematuras. Medir o desempenho antes de introduzir complexidade.

O interpretador deve validar instruções e apresentar erros claros, sem executar operações inválidas silenciosamente.

## 12. Documentação

Toda documentação oficial deve ser escrita em português brasileiro.

Manter documentação sobre:

- Introdução à Lume.
- Instalação.
- Sintaxe.
- Palavras-chave.
- Tipos de dados.
- Variáveis.
- Condições.
- Repetições.
- Funções.
- Biblioteca padrão.
- Tratamento de erros.
- Exemplos.
- Arquitetura interna.
- Histórico de versões.

Os exemplos devem ser executáveis na versão correspondente da linguagem.

## 13. Versionamento e compatibilidade

Adotar versionamento semântico:

- MAJOR: alterações incompatíveis.
- MINOR: novas funcionalidades compatíveis.
- PATCH: correções e melhorias compatíveis.

Mudanças na gramática devem ser documentadas.

Não alterar silenciosamente o significado de comandos existentes.

## 14. Critérios para aceitar alterações

Uma alteração somente deve ser considerada concluída quando:

- O código estiver implementado.
- Os testes relevantes passarem.
- A documentação estiver atualizada.
- Não houver regressões conhecidas.
- O comportamento estiver de acordo com a filosofia da Lume.

Não declarar funcionalidades como concluídas apenas porque seus arquivos foram criados.

## 15. Direção de longo prazo

A visão da Lume é se tornar uma linguagem de programação independente, capaz de permitir que pessoas desenvolvam programas reais utilizando exclusivamente o português.

O projeto deve crescer de maneira organizada, sem perder sua simplicidade original.

**Princípio central:**

"Programar deve ser possível utilizando a própria língua, sem transformar o idioma em uma barreira para a tecnologia."


## 16. Estado técnico de referência — versão 0.3.0

A implementação atual é um interpretador Python independente, não um compilador nativo. O front-end semântico aceita um vocabulário e padrões explícitos; não interpreta português irrestrito.

Recursos existentes:
- Lexer, parser, AST, representação intermediária semântica e validador.
- Gramática estruturada e front-end semântico em português.
- Variáveis, listas, condições, repetições, funções e recursão.
- Atribuição por índice em listas.
- Tratamento de erros com tente, capture, finalmente e lance.
- Módulos locais .lume, importações no início do arquivo, cache por instância e detecção de ciclos.
- Biblioteca padrão modular, incluindo operações de arquivo confinadas à raiz do projeto.
- CLI, REPL multilinha, verificação estática e formatador de recuo.
- Diagnósticos de linha e coluna.
- CI em Linux, macOS e Windows, com Python 3.10 a 3.13.

Limites atuais:
- Módulos compartilham o ambiente; não há namespaces nem importação seletiva.
- Arquivos e módulos têm limite de 1 MiB.
- Coleções têm limite de 100.000 itens e a execução tem limite de 100.000 etapas.
- O formatador normaliza indentação, não reescreve expressões.
- A Lume não oferece async/await, classes, rede ou carregamento de módulos Python.
- A raiz de arquivos não é uma sandbox de segurança contra código hostil.

## 17. Regras específicas para alterações

- Não introduzir uma palavra natural sem entrada de dicionário, regra de tradução, teste e documentação.
- Não permitir que o tradutor semântico adivinhe a intenção de frases fora dos padrões registrados.
- Manter AST e IR independentes das palavras usadas pelo front-end.
- Preservar posições de origem ao criar novos nós e instruções IR.
- Importações devem ser verificáveis sem executar o módulo e devem continuar restritas ao início do arquivo.
- Operações de arquivo devem usar a raiz de projeto e limites de tamanho; não remover as verificações de caminho.
- Não tratar limites de caminho como sandbox de segurança.
- Atualizar a especificação e a política de compatibilidade antes de declarar a gramática 1.0 estável.
- A versão 1.0 só pode ser marcada como concluída após critérios do roteiro, testes em matriz e validação de instalação limpa.
