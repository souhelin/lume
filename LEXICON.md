# LUME Lexicon

**Estado desta entrega: fundação de armazenamento implementada; integração semântica ampla e carga de dados ainda pendentes.**

O LUME Lexicon é a camada lexical local planejada para complementar o vocabulário de comandos de `lume/vocabulario.py`. O vocabulário de comandos e o léxico geral têm finalidades diferentes: o primeiro associa construções da linguagem a operações; o segundo registra lemas, classes gramaticais, flexões, sentidos e relações.

## Implementação disponível nesta branch

- Armazenamento SQLite local, sem serviço externo.
- Unicode NFC e normalização de caixa, preservando acentos.
- Entradas com identificador, lema, classe, definição opcional e procedência.
- Formas flexionadas ligadas ao lema.
- Relações semânticas e contextos.
- Consulta exata por lema ou forma.
- Preservação de múltiplos resultados para palavras ambíguas.
- Cache LRU limitado a 512 consultas.
- Integridade referencial, índices e versão de esquema.
- Bloqueio de importação de dados cuja fonte não tenha sido marcada como verificada.

A API está disponível em `lume.lexicon` e é exportada pelo pacote `lume`.

## Exemplo

```python
from lume import EntradaLexical, FonteLexical, Lexicon

with Lexicon("dados/lexicon.sqlite3") as lexicon:
    lexicon.registrar_fonte(
        FonteLexical(
            "fonte-exemplo",
            "Fonte de exemplo",
            "MIT",
            "1.0",
            "https://example.org/dados",
            "Atribuição exigida pela fonte",
        ),
        verificada=True,
    )
    lexicon.adicionar_entrada(
        EntradaLexical(
            "cantar-verbo",
            "cantar",
            "verbo",
            None,
            "fonte-exemplo",
            "MIT",
            "1.0",
        ),
        formas=(("canto", "presente_1s"),),
    )
    correspondencias = lexicon.buscar("canto")
```

A marcação `verificada=True` é uma decisão explícita do processo de importação; não é uma opinião jurídica automática do banco.

## Limites atuais

Esta branch ainda não incorpora os grandes arquivos lexicais das fontes externas. Os formatos de dados precisam ser inspecionados e cada subconjunto precisa ter direitos de redistribuição comprovados antes da carga. A API também ainda não executa desambiguação contextual de frases nem transforma palavras desconhecidas em comandos.

Não confundir uma consulta lexical exata com compreensão semântica. A interpretação contextual exigirá análise sintática, contexto da frase e regras testáveis, mantendo a IR independente das palavras de superfície.

## Testes

```bash
python -m unittest testes.teste_lexicon -v
python -m unittest discover -s testes -v
```
