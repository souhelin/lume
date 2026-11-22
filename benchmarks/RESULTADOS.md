# Resultados de referência

## Snapshot CI — 2026-11-22

Ambiente: Python 3.12.16, Linux x86_64, runner hospedado do GitHub Actions. O benchmark usa a mediana de cinco amostras; cada amostra executa cem repetições.

| Operação | Mediana observada |
|---|---:|
| Análise léxica | 71,0 µs/op |
| Análise sintática | 103,6 µs/op |
| Compilação semântica | 2.087,3 µs/op |
| Execução tradicional | 309,9 µs/op |
| Execução semântica | 2.444,2 µs/op |

Estes valores são um snapshot de um runner compartilhado, não uma promessa de desempenho nem uma meta de aprovação. O ruído de virtualização, CPU e carga pode alterar os resultados.

A compilação semântica inclui reconhecimento de instruções, análise, construção de IR e validação. A medição de execução semântica recompila a fonte em cada amostra e, portanto, não mede apenas o custo do executor. Uma comparação de otimizações deve separar compilação e execução de IR já compilada, usando a mesma máquina, versão de Python e carga.
