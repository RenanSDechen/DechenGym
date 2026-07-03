"""
Exemplo: síntese da came de resistência variável.
=================================================

Demonstra o diferencial ergonômico virando geometria:

1. Projeta a ergonomia do exercício (obtém grupo muscular e ADM).
2. Sintetiza a came cujo raio acompanha a curva de força.
3. Prova o casamento (round-trip): resistência da came -> avaliação.
4. Gera a came em OpenSCAD (.scad) e o preview 2D (.svg).

Execução:

    python examples/exemplo_came.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dechengym.ergonomia import avaliar_curva_resistencia, projetar_ergonomia  # noqa: E402
from dechengym.sintese_came import (  # noqa: E402
    calcular_resistencia_came,
    gerar_came_openscad,
    gerar_came_svg,
    sintetizar_came_de_ergonomia,
)


def main() -> None:
    exercicio = "rosca_biceps"
    carga_kg = 40.0
    out_dir = Path(__file__).resolve().parents[1] / "output"
    out_dir.mkdir(exist_ok=True)

    print(f"== DechenGym :: Sintese de came :: {exercicio} ==\n")

    # 1) Ergonomia -> came --------------------------------------------------
    env = projetar_ergonomia(exercicio, percentil=50, sexo="masculino", carga_pico_kg=carga_kg)
    perfil = sintetizar_came_de_ergonomia(env, raio_max_mm=100)
    print(f"Grupo muscular : {perfil['grupo_muscular']} (curva {perfil['tipo_curva']})")
    print(f"Amplitude came : {perfil['amplitude_graus']:.0f} graus")
    print(f"Raio efetivo   : {perfil['raio_min_mm']:.1f} - {perfil['raio_max_mm']:.1f} mm")

    # 2) Prova do casamento (round-trip) -----------------------------------
    resistencia = calcular_resistencia_came(perfil, carga_kg=carga_kg)
    aval = avaliar_curva_resistencia(resistencia["torque_nm"], perfil["grupo_muscular"])
    print(f"\nTorque resistente (N.m): {resistencia['torque_nm']}")
    print(f"Casamento com a curva de forca: {aval['pontuacao']}/100")
    print(f"  -> {aval['recomendacao']}")

    # 3) Saídas: OpenSCAD + SVG --------------------------------------------
    scad = gerar_came_openscad(perfil, espessura_mm=12, diametro_eixo_mm=25)
    svg = gerar_came_svg(perfil)
    (out_dir / f"came_{perfil['grupo_muscular']}.scad").write_text(scad, encoding="utf-8")
    (out_dir / f"came_{perfil['grupo_muscular']}.svg").write_text(svg, encoding="utf-8")

    print(f"\nArtefatos gravados em: {out_dir}")
    print(f"  - came_{perfil['grupo_muscular']}.scad")
    print(f"  - came_{perfil['grupo_muscular']}.svg")


if __name__ == "__main__":
    main()
