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

## 0.2.0 — Consistência e ergonomia

- [ ] Etapa independente de validação semântica.
- [ ] Mensagens de erro de execução com linha e coluna.
- [ ] Testes de compatibilidade da gramática e corpus ampliado de exemplos.
- [ ] Índices e operações mais completas sobre listas.
- [ ] Biblioteca padrão organizada em módulos internos.
- [ ] REPL com blocos de várias linhas e recuperação de erros.

## 0.3.0 — Programas maiores

- [ ] Sistema de módulos e importações com regras explícitas.
- [ ] Manipulação de arquivos com permissões e limites definidos.
- [ ] Tratamento estruturado de erros na própria linguagem.
- [ ] Formatador e ferramenta de diagnóstico.
- [ ] Documentação completa para iniciantes.

## 1.0.0 — Estabilidade

- [ ] Gramática estável e especificação normativa.
- [ ] Política de compatibilidade e suíte de conformidade.
- [ ] Auditoria de segurança da biblioteca padrão e do ambiente de execução.
- [ ] Testes de desempenho reproduzíveis e metas justificadas por medições.
- [ ] Distribuição reproduzível para os sistemas oficialmente suportados.

## Direção de longo prazo

Depois de estabilizar a semântica, avaliar bytecode ou uma implementação nativa. Uma migração de runtime não deve alterar a linguagem visível nem ser feita apenas por expectativa de desempenho: primeiro devem existir benchmarks e requisitos concretos.
