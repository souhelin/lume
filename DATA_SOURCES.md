# Fontes de dados do LUME Lexicon

Este documento registra o estado da auditoria preliminar. A presença de uma fonte nesta lista não significa que seus dados já estejam incorporados ao pacote.

## fserb/pt-br

- Repositório: https://github.com/fserb/pt-br
- Licença indicada no repositório: MIT.
- README descreve léxico, conjugações, lista de verbos e pontuações ICF.
- O próprio README informa que o arquivo `lexico` agrega entradas de múltiplas fontes dicionarísticas.

**Decisão:** fonte candidata para formas e flexões. Não copiar o arquivo lexical integral até identificar as fontes upstream, as condições de redistribuição e a cobertura efetiva da licença MIT sobre os dados agregados. Licença do código e direitos sobre cada base de dados podem ser questões distintas.

## OpenWordNet-PT

- Repositório: https://github.com/own-pt/openWordnet-PT
- Licença declarada no README e no arquivo LICENSE: CC BY 4.0.
- O README informa que a construção histórica utilizou Princeton WordNet 3.0, UWN, MENTA, EuroWordNet e material com glossas candidatas provenientes da Wikipédia.
- A licença da Princeton WordNet 3.0 permite uso, cópia, modificação e distribuição, condicionados à preservação do aviso de copyright e do texto de licença.

**Decisão:** candidata para synsets e relações, mas a carga deve ser seletiva e preservar atribuição e licença por componente. Antes de empacotar glossas ou registros derivados, auditar a procedência de cada campo e dependência. Não tratar todo conteúdo histórico como automaticamente coberto por uma única licença.

## Corpus Carolina

- Documentação: https://corpuscarolina.ime.usp.br/pt-br/docs
- Termos e créditos: https://sites.usp.br/corpuscarolina/creditos/
- O corpus reúne documentos de múltiplas origens e licenças.
- A licença específica de cada documento está indicada nos metadados.
- O cabeçalho do corpus está sob CC BY-NC-SA 4.0.

**Decisão:** não incorporar o corpus integral. Não incluir conteúdo CC BY-NC-SA em uma distribuição do LUME destinada a uso comercial. Estatísticas derivadas só poderão ser usadas após análise das condições dos documentos que contribuíram para elas e dos termos aplicáveis.

## Fonte excluída

Dicio (https://www.dicio.com.br/) está excluído. Não extrair, copiar, importar ou redistribuir seu conteúdo.

## Regras de ingestão

1. Registrar nome, URL, versão, licença e atribuição.
2. Identificar a licença de cada subconjunto e campo.
3. Rejeitar registros sem procedência verificável.
4. Não misturar bases com licenças diferentes sem preservar a origem por registro.
5. Manter cópias dos avisos de licença exigidos junto à distribuição.
6. Registrar checksums e versão exata dos arquivos de origem em futuras importações.
7. Não interpretar a ausência de uma licença explícita como permissão.
