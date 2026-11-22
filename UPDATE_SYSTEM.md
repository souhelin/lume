# Atualização do LUME Lexicon

## Estado implementado

O módulo `lume.lexical_update` aplica pacotes delta locais autenticados por Ed25519. Não existe download automático: o usuário ou mantenedor obtém o pacote e inicia a atualização explicitamente.

Instale o extra de verificação:

```bash
python -m pip install '.[updates]'
```

## Formato do pacote

O ZIP deve conter exatamente:

- `manifest.json`: versão do schema, SHA-256 do delta e metadados completos da fonte;
- `manifest.sig`: assinatura Ed25519 do conteúdo exato de manifest.json, codificada em Base64;
- `delta.jsonl`: operações JSON Lines.

Cada linha do delta deve declarar a mesma fonte do manifesto.

Exemplo de operação:

```json
{"op":"upsert","source":"openwordnet-pt","id":"termo-123","lemma":"termo","pos":"substantivo","definition":"Definição licenciada.","forms":[["termos","plural"]],"contexts":["linguística"]}
{"op":"delete","source":"openwordnet-pt","id":"registro-antigo"}
```

A operação `upsert` usa os metadados de licença e versão assinados no manifesto. `delete` remove somente a entrada pertencente à fonte indicada. A licença e a versão ficam gravadas por entrada, preservando a proveniência histórica mesmo quando os metadados da fonte avançam.

## Aplicação e rollback

1. Verifica o formato exato do ZIP.
2. Verifica assinatura Ed25519 e hash SHA-256.
3. Rejeita versão de schema incompatível ou metadados incompletos.
4. Cria um banco temporário a partir de um snapshot SQLite.
5. Aplica o delta em staging.
6. Executa integridade SQLite e verificação de chaves estrangeiras.
7. Fecha conexões e prepara o banco para substituição.
8. Preserva o banco anterior em `.bak`.
9. Substitui o arquivo ativo com `os.replace`; se a substituição falhar, restaura o backup.

Uma assinatura, hash, operação ou validação inválida não deve alterar o banco ativo.

## Assinatura de pacotes

A ferramenta de publicação é `scripts/assinar_pacote_lexicon.py`. Ela exige uma chave privada Ed25519 em PEM. A chave privada deve ficar fora do repositório, protegida pelo responsável pela publicação. A chave pública de 32 bytes é distribuída ao aplicativo/hospedeiro e passada para `aplicar_pacote_assinado`.

## Regras de segurança

- Não executar downloads durante consultas ou execução de programas LUME.
- Não aceitar pacote sem assinatura confiável.
- Não confiar apenas em HTTPS ou no nome do arquivo.
- Não substituir o banco ativo antes de validar o staging.
- Manter backup e permitir restauração manual.
- Registrar a versão exata de cada fonte.
- O usuário controla quando atualizar; o funcionamento normal permanece offline.
