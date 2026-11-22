"""Valida o wheel em um ambiente virtual temporário e sem dependências externas."""

from __future__ import annotations

import glob
import os
import subprocess
import tempfile
import venv
from pathlib import Path


def main() -> int:
    rodas = glob.glob(str(Path("dist") / "*.whl"))
    if len(rodas) != 1:
        raise SystemExit(f"esperava exatamente um wheel em dist/, encontrei {len(rodas)}")
    with tempfile.TemporaryDirectory(prefix="lume-wheel-") as temporario:
        raiz = Path(temporario)
        ambiente = raiz / "venv"
        venv.EnvBuilder(with_pip=True).create(ambiente)
        python = ambiente / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        subprocess.run(
            [str(python), "-m", "pip", "install", "--no-deps", str(Path(rodas[0]).resolve())],
            check=True,
        )
        ambiente_execucao = os.environ.copy()
        ambiente_execucao.pop("PYTHONPATH", None)
        resultado = subprocess.run(
            [str(python), "-m", "lume", "--versao"],
            cwd=raiz,
            env=ambiente_execucao,
            check=True,
            capture_output=True,
            text=True,
        )
        if "0.3.0" not in resultado.stdout:
            raise SystemExit(f"versão inesperada no wheel: {resultado.stdout.strip()}")
        print(resultado.stdout.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
