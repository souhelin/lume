# Benchmarks

Execute na raiz do repositório:

~~~bash
python benchmarks/benchmark.py
~~~

O script mede análise léxica, análise sintática, compilação semântica e execução nos dois front-ends. Usa somente a biblioteca padrão do Python e informa versão/plataforma.

Os resultados são informativos, não uma garantia de desempenho. Compare máquinas, versões de Python e condições semelhantes. O benchmark não deve ser usado como teste de aprovação de CI: ruído de sistema, virtualização e frequência de CPU afetam os números. Antes de uma otimização, registre a linha de base e compare a mesma carga.


Um snapshot inicial está em [RESULTADOS.md](RESULTADOS.md). Os números são observações de runner compartilhado, não metas de desempenho.
