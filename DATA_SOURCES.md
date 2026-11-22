# Fontes de dados do LUME Lexicon

A fonte precisa ser registrada por conjunto e versão. O código MIT do LUME não altera as licenças dos dados.

## fserb/pt-br

- Repositório: https://github.com/fserb/pt-br
- Licença indicada no repositório: MIT.
- README declara aproximadamente 145.744 entradas lexicais, 195.751 formas de conjugação, 4.023 verbos e 419.486 pontuações ICF.
- Os arquivos `lexico` e `conjugações` são listas simples, uma palavra por linha.
- O README informa que o léxico agregado foi reunido de múltiplas fontes dicionarísticas.

**Importação:** há importadores para `lexico`, `conjugações`, `listas/verbos` e `icf`. O léxico preserva as palavras como classe `não_classificada`; as conjugações são armazenadas como `forma_verbal_sem_lema`, pois o arquivo não fornece uma relação explícita forma→infinitivo; a lista de verbos fornece lemas verbais; o ICF fica em uma tabela numérica separada.

**Risco de procedência:** a licença MIT do repositório é registrada, mas a origem de cada dicionário que compõe o agregado não está descrita linha a linha. Antes de redistribuir os dados agregados, confirme que a licença declarada cobre todos os conteúdos de terceiros. A importação exige confirmação explícita.

## OpenWordNet-PT original

- Repositório: https://github.com/own-pt/openWordnet-PT
- Licença declarada no README e LICENSE do projeto original: CC BY 4.0.
- Arquivos usados: `data/own-pt-words.ttl`, `own-pt-synsets.ttl`, `own-pt-wordsenses.ttl` e `own-pt-relations.ttl`.
- O importador preserva lemas, classe gramatical, glossas, identificadores de synset, associação palavra-sentido e relações semânticas.
- O histórico do projeto cita Princeton WordNet 3.0, UWN, MENTA, EuroWordNet e glossas candidatas da Wikipédia. Atribuição e proveniência devem acompanhar a versão redistribuída.

**Importação:** use os quatro arquivos Turtle do mesmo commit/tag. A versão deve ser registrada como o commit ou tag real, não apenas como “latest”.

## Exportação OpenWordNet-PT pelo OMW

- Repositório: https://github.com/omwn/omw-data/tree/main/wns/por
- O arquivo `wn-data-por.tab` é uma exportação tabular que lista lemas associados a synsets.
- O LICENSE dessa exportação declara CC BY-SA 3.0 e inclui referências a WordNet e Wiktionary.
- O importador TSV é mantido separado do importador Turtle original, com licença CC BY-SA 3.0 registrada.

Não misture a exportação OMW com o conjunto original como se fossem a mesma versão/licença.

## Corpus Carolina

- Documentação: https://corpuscarolina.ime.usp.br/pt-br/docs
- Créditos: https://sites.usp.br/corpuscarolina/creditos/
- O corpus reúne documentos de múltiplas origens e licenças.
- A licença específica de cada documento está indicada nos metadados; o cabeçalho do corpus está sob CC BY-NC-SA 4.0.

**Decisão:** não importar o corpus integral. Conteúdo sob cláusula NãoComercial não deve ser incorporado a uma distribuição comercial do LUME. Estatísticas derivadas exigem análise das condições dos documentos que contribuíram para elas.

## Fonte excluída

Dicio (https://www.dicio.com.br/) está excluído. Não extrair, copiar, importar ou redistribuir seu conteúdo.

## Regras de ingestão

1. Fixar commit/tag e checksum dos arquivos.
2. Registrar licença e atribuição por fonte e versão.
3. Rejeitar dados sem metadados de origem.
4. Não misturar licenças sem preservar a proveniência.
5. Manter avisos de copyright e licença junto a qualquer distribuição de dados.
6. Não tratar ausência de licença como permissão.
