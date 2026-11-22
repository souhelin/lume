# Roteiro de desenvolvimento

Este roteiro diferencia a base já implementada do trabalho futuro. Uma etapa só deve ser marcada como concluída depois de existir código e teste correspondente.

## 0.1.0 — Base interpretada (em desenvolvimento)

- [x] Analisador léxico e tokens com suporte a Unicode.
- [x] Parser e árvore de sintaxe abstrata.
- [x] Variáveis, valores básicos, listas e expressões.
- [x] Condições, laços e funções.
- [x] Entrada, saída e biblioteca nativa inicial.
- [x] CLI, exemplos e testes automatizados.
- [x] Documentação inicial da sintaxe e arquitetura.
- [ ] Publicar pacote e binários para plataformas suportadas.
- [ ] Validar instalação em ambientes limpos Linux, macOS e Windows.

## 0.2.0 — Consistência e ergonomia

- [ ] Etapa independente de validação semântica.
- [ ] Mensagens de erro de execução com linha e coluna.
- [ ] Testes de compatibilidade da gramática e corpus de exemplos.
- [ ] Índices e operações mais completas sobre listas.
- [ ] Recursos de texto e biblioteca padrão organizados em módulos internos.
- [ ] REPL com blocos de várias linhas e recuperação de erros.

## 0.3.0 — Programas maiores

- [ ] Sistema de módulos e importações com regras explícitas.
- [ ] Manipulação de arquivos com permissões e limites definidos.
- [ ] Tratamento estruturado de erros na própria linguagem.
- [ ] Formatação automática e ferramenta de diagnóstico.
- [ ] Documentação completa para iniciantes.

## 1.0.0 — Estabilidade

- [ ] Gramática estável e especificação normativa.
- [ ] Política de compatibilidade e suíte de conformidade.
- [ ] Auditoria de segurança da biblioteca padrão e do ambiente de execução.
- [ ] Testes de desempenho reproduzíveis e metas justificadas por medições.
- [ ] Distribuição reproduzível para os sistemas oficialmente suportados.

## Direção de longo prazo

Depois de estabilizar a semântica, avaliar bytecode ou uma implementação nativa. Uma migração de runtime não deve alterar a linguagem visível nem ser feita apenas por expectativa de desempenho: primeiro devem existir benchmarks e requisitos concretos.
