"""
Exemplo end-to-end: projeto de um braço articulado.
===================================================

Demonstra o fluxo que o agente orquestrador percorreria via Tool Calling:

1. Calcular o momento fletor da alavanca.
2. Validar o perfil de metalon (e obter a recomendação de espessura).
3. Gerar o script OpenSCAD (geometria) e o memorial descritivo (JSON).

Execução:

    python examples/exemplo_braco_articulado.py

Os artefatos são gravados em ``output/``.
"""

import json
import sys
from pathlib import Path

# Torna o pacote importável ao rodar direto (sem instalar).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dechengym.calculo_estrutural import (  # noqa: E402
    calc_momento_fletor,
    validar_resistencia_estrutural,
)
from dechengym.geracao_openscad import (  # noqa: E402
    gerar_memorial_descritivo,
    gerar_script_openscad,
)


def main() -> None:
    forca_kg = 100
    alavanca_mm = 800
    perfil = "50x50"

    print("== DechenGym :: Braco articulado ==\n")

    # 1) Momento fletor -----------------------------------------------------
    momento = calc_momento_fletor(forca_kg, alavanca_mm)
    print(f"Momento fletor: {momento:.3f} N.m  ({forca_kg} kg @ {alavanca_mm} mm)")

    # 2) Validacao estrutural ----------------------------------------------
    relatorio = validar_resistencia_estrutural(forca_kg, alavanca_mm, perfil, 1.5)
    print("\nValidacao (parede 1.5 mm):")
    print("  " + relatorio["mensagem"])

    espessura = relatorio["espessura_recomendada_mm"] or 3.0

    # 3) Geometria + memorial ----------------------------------------------
    parametros = {
        "nome": "braco_articulado",
        "altura_coluna_mm": 1200,
        "comprimento_alavanca_mm": alavanca_mm,
        "perfil_base_mm": 50,
        "perfil_coluna_mm": 50,
        "perfil_alavanca_mm": 50,
        "espessura_parede_mm": espessura,
    }

    out_dir = Path(__file__).resolve().parents[1] / "output"
    out_dir.mkdir(exist_ok=True)

    scad = gerar_script_openscad(parametros)
    memorial = gerar_memorial_descritivo(parametros)

    (out_dir / "braco_articulado.scad").write_text(scad, encoding="utf-8")
    (out_dir / "braco_articulado_memorial.json").write_text(
        json.dumps(memorial, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nEspessura adotada: {espessura} mm")
    print(f"Peso da estrutura: {memorial['peso_total_estrutura_kg']} kg")
    print(f"\nArtefatos gravados em: {out_dir}")
    print("  - braco_articulado.scad")
    print("  - braco_articulado_memorial.json")


if __name__ == "__main__":
    main()
