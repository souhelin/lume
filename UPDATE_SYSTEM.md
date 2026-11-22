# Atualização do LUME Lexicon

## Estado

O mecanismo de atualização remota ainda não está implementado nesta branch. O banco possui versão de esquema SQLite e metadados de fonte, mas isso não equivale a um atualizador completo de dados.

## Requisitos para a implementação

Uma futura atualização deve:

1. ser iniciada explicitamente pelo usuário ou administrador;
2. usar manifesto assinado ou mecanismo equivalente de autenticidade;
3. validar hash, tamanho e versão do pacote;
4. validar origem, licença e atribuição de cada dataset;
5. construir uma cópia temporária do banco;
6. executar migrações e `PRAGMA integrity_check`;
7. executar testes de consulta e integridade referencial;
8. substituir o banco ativo de forma atômica;
9. preservar backup e permitir rollback;
10. manter a versão local disponível se rede, validação ou atualização falhar.

## Segurança e offline-first

- Nenhuma consulta lexical deve acessar a rede.
- Não baixar dados durante importação do pacote ou execução de programas.
- Atualizações não podem ser automáticas sem configuração explícita.
- Não aceitar banco ou manifesto de origem não autenticada.
- Não substituir o banco ativo antes de concluir todas as validações.
- Atualizações devem ser compatíveis com Android, Termux e Linux.

## Migrações

O esquema atual usa `PRAGMA user_version`. Cada versão futura deverá ter migração sequencial, transacional e testada. Uma versão de banco superior à suportada deve ser rejeitada sem sobrescrita.
