# Modelo de segurança e limites

## Modelo de confiança

A Lume é uma linguagem interpretada para programas locais e cooperativos. Ela não é uma sandbox para executar código desconhecido. Um programa Lume pode consumir recursos do processo Python e pode ler ou escrever arquivos dentro da raiz de projeto permitida.

Não execute programas de origem desconhecida em diretórios que contenham dados sensíveis. Para executar código não confiável, use uma sandbox do sistema operacional, conta sem privilégios, diretório descartável e limites externos de CPU/memória.

## Capacidades presentes

- Não há eval, exec, subprocessos, importação de módulos Python ou acesso de rede expostos pela linguagem.
- A importação carrega apenas arquivos .lume dentro da raiz do projeto.
- As funções de arquivo aceitam caminhos relativos à raiz do projeto.
- Caminhos absolutos e caminhos resolvidos fora da raiz são rejeitados.
- Arquivos e módulos têm limite de 1 MiB.
- Coleções têm limite de 100.000 itens.
- A execução possui limite de 100.000 etapas.
- Operações numéricas e chamadas recursivas possuem limites defensivos.

## Limitações importantes

1. A raiz de projeto restringe o escopo normal dos caminhos, mas não constitui uma sandbox contra código hostil.
2. Verificações de caminho e abertura de arquivo não são uma proteção completa contra condições de corrida do sistema de arquivos ou alterações simultâneas de links simbólicos.
3. Módulos importados executam código com as mesmas permissões do programa principal.
4. O limite de etapas não equivale a um limite rígido de memória ou tempo de CPU do processo hospedeiro.
5. A implementação usa o runtime Python; vulnerabilidades no Python e no sistema operacional estão fora do controle da linguagem.
6. A entrada e saída do programa podem revelar dados fornecidos pelo usuário ou pelo ambiente.

## Recomendações

- Execute projetos confiáveis em uma pasta de trabalho dedicada.
- Não use diretórios pessoais, de sistema ou de credenciais como raiz de um programa não confiável.
- Não conceda permissões elevadas ao processo que executa Lume.
- Faça backup antes de executar programas que escrevem arquivos.
- Para ambientes de produção, aplique limites externos de CPU, memória, tempo e permissões.

## Reporte de vulnerabilidades

Consulte SECURITY.md para o canal de reporte. Não publique detalhes exploráveis de uma vulnerabilidade não corrigida em uma issue pública.


As funções de leitura consomem no máximo 1 MiB mais um byte de detecção antes de rejeitar arquivos maiores, evitando carregar um arquivo arbitrariamente grande na memória durante a leitura normal. Isso não elimina corridas de sistema de arquivos nem substitui limites externos do processo.
