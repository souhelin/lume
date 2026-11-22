# Histórico de alterações

## Não lançado — núcleo semântico em desenvolvimento

- Adicionado dicionário semântico extensível com expressões, intenções, operações, regras e ambiguidades.
- Adicionado front-end de instruções naturais controladas, contexto semântico e mensagens de ambiguidade.
- Adicionada representação intermediária com operações canônicas e validador semântico independente do executor.
- Integrada seleção de modo semântico à CLI e disponibilizada API pública em Python.
- Adicionados testes para equivalência, contexto, vocabulário, IR, validação e execução.

## 0.1.0 — versão alfa inicial

- Implementado o primeiro interpretador próprio da Lume, com lexer, parser, AST, variáveis, expressões, coleções, condições, laços, funções, CLI e testes.
- Expandido o acesso a índices, operações sobre listas, atribuição e console interativo.


## Próxima etapa — recursos estruturados

- Adicionada atribuição por índice para listas mutáveis.
- Adicionados blocos `tente`, `capture`, `finalmente` e `lance` para tratamento de erros da linguagem.
- IR e validador semântico estendidos para essas operações.
- Testes de regressão para mutação por índice e fluxo de tratamento de erros.


## Próxima etapa — módulos e arquivos locais

- Adicionada instrução importar "arquivo.lume" com cache por instância e detecção de ciclos.
- Adicionadas funções nativas de leitura, escrita, anexação e verificação de arquivos UTF-8.
- Caminhos confinados à raiz do projeto, com rejeição de caminhos absolutos e travessia de diretório.
- Limites de 1 MiB para módulos e conteúdo de arquivos.
- Preservado o orçamento global de etapas ao executar módulos importados.
- Testes de importação, ciclos, acesso fora da raiz e operações de arquivos.
