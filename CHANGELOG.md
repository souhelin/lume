# Histórico de alterações

## Não lançado — arquitetura Offline-First e conectividade opcional

- Mantido o núcleo semântico e tradicional independente de Internet, sem dependências externas obrigatórias.
- Adicionado controle de permissões de rede negado por padrão, com autorização explícita de hosts exatos pela API ou CLI.
- Adicionado cliente HTTP(S) opcional e carregado sob demanda, com timeout, limites de payload/resposta, TLS padrão e redirecionamentos desativados.
- Adicionadas as funções `http_obter`, `http_enviar` e `baixar` à biblioteca padrão.
- Adicionados testes de execução offline, permissões, falhas de conexão e limites de requisição.
- Documentadas a arquitetura, a configuração de permissões e as limitações de segurança.
- Corrigida a classificação de tags `v0.x` como pré-lançamentos no workflow de release.

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


## 0.3.0 — Recursos para programas maiores

- Atribuição por índice em listas.
- Tratamento estruturado de erros.
- Importação de módulos locais com cache e detecção de ciclos.
- Biblioteca de arquivos UTF-8 com raiz de projeto e limites de tamanho.
- Diagnósticos de execução e validação com linha e coluna.
- Formatador determinístico de indentação.
- CI expandido para Linux, macOS e Windows com Python 3.10–3.13.
- Construção de wheel validada na integração contínua.


## 0.3.0 — Organização interna

- Biblioteca padrão extraída para módulo dedicado, sem alterar as assinaturas das funções nativas.
- Testes de REPL para blocos multilinha, erros léxicos e tratamento semântico.


- Adicionado MANIFEST.in para incluir documentação e exemplos em distribuições fonte.
- Adicionado teste de instalação isolada do wheel na CI.


- Adicionado workflow de release por tag com testes, build e validação isolada do wheel antes de publicar no GitHub Releases.
- A validação do wheel agora compara a versão instalada com os metadados do projeto, sem versão codificada no script.


## Validação de fluxo e distribuição

- A inferência semântica agora mescla conservadoramente os tipos nos caminhos de condicionais, laços e tratamento de erros.
- Adicionados testes de equivalência de formulações em português e de execução de funções importadas.
- Adicionado workflow de publicação por tag, com testes, construção de wheel, instalação isolada e GitHub Release.
- A matriz CI do commit de validação executou 126 testes e aprovou Python 3.10–3.13 em Linux, macOS e Windows.
