# Roteiro de desenvolvimento

Este roteiro separa o que já existe no repositório do que ainda precisa ser construído. Uma etapa só deve ser marcada como concluída quando houver implementação e validação correspondente.

## 0.1.0 — Base interpretada (implementada; versão alfa)

- [x] Analisador léxico e tokens com suporte a Unicode.
- [x] Parser próprio e árvore de sintaxe abstrata.
- [x] Variáveis, tipos básicos, listas e expressões.
- [x] Condições, repetições e funções.
- [x] Entrada, saída e biblioteca padrão inicial.
- [x] Interface de linha de comando e modo de verificação de sintaxe.
- [x] Exemplos executáveis, documentação inicial e testes automatizados.
- [x] Integração contínua aprovada em Python 3.10, 3.11, 3.12 e 3.13.
- [ ] Publicar o pacote e binários para plataformas suportadas.
- [ ] Validar instalação em ambientes limpos Linux, macOS e Windows.

## 0.2.0 — Núcleo semântico e consistência

- [x] Dicionário semântico expansível com significados, categorias, intenções, operações, relações e regras.
- [x] Reconhecimento de padrões naturais com aliases e equivalências determinísticas.
- [x] Contexto semântico para variáveis, funções e referências pronominais limitadas.
- [x] Representação intermediária com operações canônicas independente da frase de origem.
- [x] Validador semântico separado do executor, com diagnósticos em português.
- [x] Integração do front-end semântico à API, CLI e REPL.
- [x] Testes de vocabulário, equivalência, contexto, ambiguidade, IR e validação.
- [x] Exemplo executável e documentação dos padrões e limites.
- [ ] Ampliar a gramática semântica com corpus de compatibilidade e especificação formal por padrão.
- [x] Posições de linha e coluna preservadas em instruções da AST, IR, erros semânticos e erros de execução.
- [ ] Inferência de tipos e fluxo de controle mais completos.
- [x] Biblioteca padrão separada do executor em módulo interno dedicado.
- [x] Testes de recuperação de erros e conclusão de blocos multilinha no REPL.

## 0.3.0 — Programas maiores

- [x] Sistema de módulos locais com cache por instância, detecção de ciclos e raiz de projeto.
- [x] Leitura e escrita UTF-8 confinadas à raiz do projeto e limitadas a 1 MiB.
- [x] Tratamento estruturado com tente, capture, finalmente e lance.
- [x] Formatador de recuo e diagnósticos de linha/coluna na CLI.
- [ ] Guia completo para iniciantes e tutoriais por projeto.

## 1.0.0 — Estabilidade

- [ ] Gramática estável e especificação normativa.
- [ ] Política de compatibilidade e suíte de conformidade.
- [ ] Auditoria de segurança da biblioteca padrão e do ambiente de execução.
- [ ] Testes de desempenho reproduzíveis e metas justificadas por medições.
- [ ] Distribuição reproduzível para os sistemas oficialmente suportados.

## Direção de longo prazo

Depois de estabilizar a semântica, avaliar bytecode ou uma implementação nativa. Uma migração de runtime não deve alterar a linguagem visível nem ser feita apenas por expectativa de desempenho: primeiro devem existir benchmarks e requisitos concretos.


A versão 0.3.0 reúne os recursos marcados como concluídos nesta etapa. A matriz de CI cobre os três sistemas operacionais e quatro versões do Python; a publicação de artefatos e a verificação em ambientes realmente limpos ainda precisam de uma etapa de lançamento.
