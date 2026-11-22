# Como contribuir

A Lume está em fase alfa. Contribuições devem preservar o português brasileiro como idioma público, a execução independente de IA e a previsibilidade da gramática.

## Antes de alterar

1. Leia `AGENTS.md`, este guia e a documentação da sintaxe.
2. Confira se a funcionalidade já existe ou está planejada em `docs/roteiro.md`.
3. Prefira mudanças pequenas e compatíveis.
4. Não apresente protótipos ou funcionalidades incompletas como concluídos.

## Ambiente de desenvolvimento

- Python 3.10 ou superior.
- Nenhuma dependência de terceiros é necessária para executar os testes.

```bash
python -m pip install -e .
python -m unittest discover -s testes -v
```

Antes de enviar uma alteração, execute todos os exemplos:

```bash
for arquivo in exemplos/*.lume; do
    python -m lume --verificar "$arquivo" || exit 1
done
```

## Regras para mudanças na linguagem

- Atualize `docs/sintaxe.md` quando alterar a gramática.
- Inclua testes para comportamentos novos e casos inválidos.
- Atualize o README e os exemplos quando a experiência de uso mudar.
- Não use `eval`, `exec` ou tradução da fonte para código Python.
- Não adicione dependências sem uma necessidade técnica clara.
- Preserve as mensagens e palavras-chave públicas em português brasileiro.
- Avalie limites de memória, execução e recursão ao criar recursos novos.

## Pull requests

Descreva o problema, a solução, os arquivos alterados e os testes executados. Indique explicitamente qualquer mudança incompatível na sintaxe ou semântica.
