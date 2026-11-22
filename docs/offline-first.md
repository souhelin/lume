# Arquitetura Offline-First e conectividade opcional

## Garantia offline

O interpretador, o vocabulário, as regras semânticas, a gramática, a IR, a biblioteca padrão local, as operações matemáticas, os módulos Lume e o sistema de arquivos funcionam localmente. Não há chamadas de rede durante a importação do pacote, a inicialização do interpretador ou a execução de programas que não chamem funções de rede.

A Lume não usa IA hospedada, API remota ou serviço externo para compreender português. O front-end semântico continua determinístico e baseado no vocabulário instalado junto ao pacote.

O módulo `lume.rede` só é importado quando uma função de rede é efetivamente chamada. A ausência de conexão não afeta os caminhos locais do interpretador.

## Permissões: negar por padrão

Nenhum host é autorizado por padrão. Uma chamada de rede sem permissão termina com erro de execução explicando como autorizar o host. A autorização é uma lista explícita de nomes de host, comparados exatamente; autorizar `api.exemplo.com` não autoriza `sub.api.exemplo.com`.

### Pela linha de comando

Autorize somente os hosts necessários:

```bash
lume --permitir-rede api.exemplo.com programa.lume
```

Repita a opção para mais de um host:

```bash
lume --permitir-rede api.exemplo.com --permitir-rede arquivos.exemplo.com programa.lume
```

A CLI informa os hosts autorizados na saída de diagnóstico. Sem `--permitir-rede`, todas as chamadas externas são bloqueadas. O mesmo parâmetro funciona no console interativo.

### Pela API Python

```python
from lume import Interpretador

interpretador = Interpretador(hosts_rede_permitidos=["api.exemplo.com"])

# O hospedeiro pode conceder ou revogar hosts durante a execução.
interpretador.permissoes_rede.permitir_host("arquivos.exemplo.com")
interpretador.permissoes_rede.revogar_host("api.exemplo.com")
```

O programa Lume não pode conceder a si próprio permissões adicionais. A decisão fica com quem inicia e configura o interpretador.

## Funções de rede disponíveis na linguagem

As funções são executadas apenas quando chamadas:

| Função | Comportamento |
|---|---|
| `http_obter(url)` | Faz uma requisição GET e devolve a resposta como UTF-8. |
| `http_enviar(url, texto)` | Envia texto por POST e devolve a resposta como UTF-8. |
| `baixar(url, caminho)` | Baixa até 1 MiB e grava bytes na raiz local do projeto; devolve a quantidade de bytes. |

Exemplo:

```text
mostrar http_obter("https://api.exemplo.com/status")
baixar("https://api.exemplo.com/arquivo.bin", "dados/arquivo.bin")
```

O caminho de destino do download obedece às mesmas restrições da biblioteca de arquivos local: caminho relativo, dentro da raiz do projeto.

## Limites de segurança

- Somente HTTP e HTTPS são aceitos; prefira HTTPS.
- A permissão é por host exato, sem curingas.
- Credenciais embutidas na URL são rejeitadas.
- Redirecionamentos HTTP são desativados; uma nova origem exige autorização e chamada explícitas.
- O timeout padrão é de 10 segundos e não pode exceder 60 segundos.
- Respostas e downloads são limitados a 1 MiB.
- Downloads são gravados dentro da raiz do projeto e não executam o conteúdo.
- Erros HTTP, de DNS, TLS e timeout são convertidos em erros da Lume.
- Não há tentativas automáticas, telemetria, atualização automática ou conexão em segundo plano.

A lista de hosts não é uma sandbox de rede: um host autorizado pode servir muitos caminhos e endereços. Não autorize domínios não confiáveis. A Lume também não promete proteção contra DNS rebinding, proxies configurados no ambiente ou código hostil executado no mesmo processo Python. Para programas não confiáveis, use isolamento no sistema operacional e controles de saída de rede.

## Como preservar o Offline-First ao contribuir

1. Não importe `lume.rede` em módulos centrais, no pacote público ou durante a inicialização.
2. Mantenha a rede atrás de chamadas explícitas e da classe `PermissoesRede`.
3. Não adicione dependências obrigatórias para HTTP; o cliente atual usa a biblioteca padrão do Python.
4. Não faça downloads, verificações de versão ou telemetria automaticamente.
5. Teste inicialização, semântica, matemática, arquivos locais e execução sem permissões.
6. Teste negação por padrão, host não autorizado, falhas de conexão e limites de resposta.
7. Mantenha o caminho offline funcional mesmo quando o módulo de rede não puder ser importado.

## Testes

```bash
python -m unittest discover -s testes -v
```

Os testes de rede usam verificações locais e mocks; não precisam acessar a Internet.
