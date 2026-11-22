# Segurança

A Lume ainda está em fase alfa. O interpretador possui limites defensivos, mas não oferece isolamento de sistema operacional nem deve ser tratado como uma caixa de segurança para executar programas não confiáveis.

## Recomendações

- Não execute programas `.lume` de origem desconhecida em ambientes com dados importantes.
- Não remova os limites de execução e de coleções sem uma análise de risco e testes.
- Revise futuras funções de acesso a arquivos, rede ou processos como mudanças sensíveis de segurança.
- Não adicione execução arbitrária de Python ou carregamento irrestrito de módulos à biblioteca padrão.

## Relato de vulnerabilidades

Não publique detalhes exploráveis de uma vulnerabilidade ainda não corrigida em uma issue pública. Use a opção **Report a vulnerability** na aba Security do GitHub, caso esteja habilitada para o repositório. Se ela não estiver disponível, entre em contato com os mantenedores por um canal privado antes de divulgar os detalhes.
