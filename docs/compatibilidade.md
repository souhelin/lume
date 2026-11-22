# Política de compatibilidade

## Estado atual

A versão 0.3.0 é uma versão alfa. Até a publicação de 1.0.0, mudanças na gramática, na biblioteca padrão e na API Python ainda podem ocorrer, mas devem ser documentadas no changelog e acompanhadas de testes.

## Regras para a versão 1.0

Após 1.0.0:

1. Uma versão PATCH corrige erros sem alterar intencionalmente a gramática ou o significado de programas válidos.
2. Uma versão MINOR adiciona palavras, funções ou construções compatíveis; não altera o significado de construções existentes.
3. Uma versão MAJOR pode remover ou alterar recursos incompatíveis.
4. Uma palavra ou função pública não deve ser removida na mesma versão MINOR em que for marcada como obsoleta.
5. Recursos obsoletos devem permanecer disponíveis por pelo menos duas versões MINOR, salvo vulnerabilidade grave.
6. Sinônimos semânticos oficiais não devem mudar de intenção silenciosamente.
7. A gramática normativa, exemplos de referência e suíte de conformidade devem ser atualizados juntos.
8. O formato serializado da IR permanece interno até receber uma versão e um contrato público próprios.

## Compatibilidade de runtime

A versão de referência declara Python 3.10 ou superior. A matriz CI oficial testa Python 3.10–3.13 em Linux, macOS e Windows. Outros sistemas podem funcionar, mas não são oficialmente garantidos até serem incluídos na matriz.

## Migrações

Toda alteração incompatível deve incluir:
- justificativa técnica;
- versão mínima e máxima afetadas;
- exemplo antes/depois;
- orientação de migração;
- teste que demonstre o comportamento novo.
