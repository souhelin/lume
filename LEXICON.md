# LUME Lexicon

**Estado desta branch:** armazenamento local, importadores de fontes, representação de sentidos, análise contextual conservadora, atualizações assinadas e benchmarks foram implementados. A base de dados não é baixada nem embutida automaticamente no pacote: o usuário escolhe os arquivos locais e executa a importação uma vez. Depois disso, as consultas são offline.

## Arquitetura

- SQLite local, schema v6, índices e integridade referencial.
- NFC + casefold, preservando diacríticos.
- Lemas, classes gramaticais, formas, fontes, licença e versão por registro.
- Sentidos/synsets independentes dos lemas: uma palavra pode participar de vários sentidos.
- Glossas, membros de synsets, exemplos de uso vinculados a cada sentido e relações semânticas.
- Consulta exata e cache LRU limitado.
- Importação em lote para reduzir transações e uso de memória.
- Nenhuma conexão de rede durante consultas ou importação.

## Importadores

Instale os extras necessários:

```bash
python -m pip install '.[rdf,updates]'
```

Os importadores recebem arquivos locais e não fazem downloads:

- `importar_fserb_lexico`: lista lexical, uma palavra por linha. Como o arquivo agregado não informa classe ou definição por linha, essas entradas ficam como `não_classificada`.
- `importar_fserb_conjugacoes`: lista de formas verbais. O arquivo não fornece o vínculo forma→infinitivo; portanto, as formas são armazenadas como `forma_verbal_sem_lema`, sem inventar uma análise morfológica.
- `importar_fserb_verbos`: lista de infinitivos/verbos como lemas de classe verbal.
- `importar_fserb_icf`: pontuações ICF em tabela própria, sem confundi-las com definições lexicais.
- `importar_openwordnet_ttl`: importa palavras, synsets, palavras-sentido e relações; aceita também os arquivos de relações morfossêmicas e same-as. Preserva POS, glossas, synsets e relações semânticas.
- `importar_openwordnet_tsv`: aceita a exportação tabular OMW separada; ela contém lemas/synsets, mas não substitui o conjunto Turtle completo.

Exemplo de API:

```python
from lume import Lexicon, importar_openwordnet_ttl

with Lexicon("dados/lexicon.sqlite3") as lexicon:
    resultado = importar_openwordnet_ttl(
        lexicon,
        "dados/own-pt-words.ttl",
        "dados/own-pt-synsets.ttl",
        "dados/own-pt-wordsenses.ttl",
        "dados/own-pt-relations.ttl",
        versao="commit-ou-tag",
        confirmar_direitos=True,
    )
    print(resultado)
    print(lexicon.buscar("respirar"))
```

Para importar arquivos fserb pelo script:

```bash
python scripts/importar_lexicon.py --banco dados/lexicon.sqlite3 \
  --fserb-lexico dados/lexico \
  --fserb-conjugacoes dados/conjugacoes \
  --fserb-verbos dados/verbos \
  --fserb-icf dados/icf \
  --confirmar-direitos
```

Para criar o banco completo a partir de snapshots fixados e checksums Git, use o instalador de primeira configuração:

```bash
python -m pip install '.[rdf,updates]'
python scripts/instalar_bases_lexicais.py \
  --destino dados/lexicon.sqlite3 \
  --confirmar-direitos
```

O instalador baixa cerca de 70 MB de dados, verifica cada arquivo pelo hash do objeto Git e monta o SQLite local. A rede é usada apenas durante essa execução explícita; depois, consultas e interpretação lexical funcionam offline. O arquivo de avisos de licença é criado ao lado do banco. Em dispositivos com pouca memória, prefira realizar a importação em um computador e transferir o banco pronto.

Para importar OpenWordNet-PT completo:

```bash
python scripts/importar_lexicon.py --banco dados/lexicon.sqlite3 \
  --openwordnet-palavras dados/own-pt-words.ttl \
  --openwordnet-synsets dados/own-pt-synsets.ttl \
  --openwordnet-palavras-sentido dados/own-pt-wordsenses.ttl \
  --openwordnet-relacoes dados/own-pt-relations.ttl \
  --confirmar-direitos
```

A opção `--confirmar-direitos` é um aceite explícito do operador após revisar os avisos de licença; não é uma certificação jurídica automática. Consulte DATA_SOURCES.md e LICENSES.md.

## Integração semântica

`Interpretador` aceita uma instância compartilhada de `Lexicon`. `InterpretadorSemantico` usa essa instância quando disponível e oferece `analisar_lexico(texto)`. A análise retorna candidatos e evidências; não reescreve AST/IR nem executa palavras encontradas no dicionário.

A desambiguação é determinística e conservadora: expande cada lema em sentidos/synsets, usa pistas locais de classe gramatical, sobreposição de palavras com a glossa, membros do synset e contextos registrados. Quando a diferença de pontuação não é suficiente, mantém a ambiguidade. Não é um modelo de linguagem nem uma compreensão irrestrita de português.

## Atualizações

O módulo `lume.lexical_update` valida pacotes Ed25519, hash do delta e versão de esquema, aplica operações em uma cópia temporária, verifica integridade e troca o banco de forma atômica. Mantém backup `.bak`. Não baixa atualizações sozinho.

Veja UPDATE_SYSTEM.md para o formato e o fluxo de publicação.

## Desempenho e validação

```bash
python -m unittest discover -s testes -v
python benchmarks/benchmark_lexicon.py --iteracoes 5000
python benchmarks/benchmark_lexicon.py --banco dados/lexicon.sqlite3 --iteracoes 20000
```

A CI também executa testes de integração com os seis arquivos Turtle do OpenWordNet-PT e com o snapshot completo fserb/pt-br. Isso valida a integração sem redistribuir os dados no pacote de código.

## Limites conhecidos

- O arquivo fserb de conjugações não identifica o infinitivo de cada forma; não é correto atribuir lemas por heurística de prefixo.
- O arquivo de conjugações fserb não fornece o vínculo forma→lema; as formas são preservadas sem uma análise morfológica falsa.
- A desambiguação atual é uma primeira camada de regras, não análise sintática profunda nem WSD estatístico.
- A análise lexical é consultiva; o tradutor semântico atual ainda reconhece construções por regras explícitas e não converte qualquer frase livre em programa.
- A inclusão de dados externos exige revisar licença e procedência da versão exata usada.
