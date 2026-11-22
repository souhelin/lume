"""Ferramenta de publicação para pacotes delta assinados do LUME Lexicon."""
from __future__ import annotations
import argparse
import base64
import hashlib
import json
from pathlib import Path
import zipfile

from cryptography.hazmat.primitives.serialization import load_pem_private_key
from lume.lexicon import SCHEMA_VERSION


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--delta", required=True, type=Path)
    p.add_argument("--chave-privada", required=True, type=Path)
    p.add_argument("--saida", required=True, type=Path)
    p.add_argument("--id-fonte", required=True)
    p.add_argument("--nome-fonte", required=True)
    p.add_argument("--licenca", required=True)
    p.add_argument("--versao", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--atribuicao", required=True)
    a = p.parse_args()
    chave = load_pem_private_key(a.chave_privada.read_bytes(), password=None)
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    if not isinstance(chave, Ed25519PrivateKey):
        raise SystemExit("a chave privada precisa ser Ed25519 em formato PEM")
    delta = a.delta.read_bytes()
    manifesto = {
        "schema_version": SCHEMA_VERSION,
        "delta_sha256": hashlib.sha256(delta).hexdigest(),
        "source": {
            "id": a.id_fonte, "name": a.nome_fonte, "license": a.licenca,
            "version": a.versao, "url": a.url, "attribution": a.atribuicao,
        },
    }
    manifesto_bytes = json.dumps(
        manifesto, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    assinatura = base64.b64encode(chave.sign(manifesto_bytes))
    with zipfile.ZipFile(a.saida, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", manifesto_bytes)
        z.writestr("manifest.sig", assinatura)
        z.writestr("delta.jsonl", delta)
    print(f"Pacote assinado: {a.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
