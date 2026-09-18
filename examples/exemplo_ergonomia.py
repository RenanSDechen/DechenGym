"""
Exemplo: projeto ergonômico de uma máquina articulada.
=====================================================

Percorre o fluxo ergonômico completo e emenda na geração de geometria:

1. Projeta o envelope ergonômico do exercício (pivô, ADM, pegada, ajustes).
2. Valida o curso projetado do braço contra a ADM de treino.
3. Avalia o casamento da resistência da máquina com a curva de força.
4. Deriva os parâmetros de geometria e gera o `.scad` + memorial.

Execução:

    python examples/exemplo_ergonomia.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dechengym.ergonomia import (  # noqa: E402
    avaliar_curva_resistencia,
    projetar_ergonomia,
    validar_amplitude_projetada,
)
from dechengym.geracao_openscad import (  # noqa: E402
    gerar_memorial_descritivo,
    gerar_script_openscad,
    parametros_geometria_de_ergonomia,
)


def main() -> None:
    exercicio = "rosca_biceps"
    print(f"== DechenGym :: Ergonomia :: {exercicio} ==\n")

    # 1) Envelope ergonômico -----------------------------------------------
    env = projetar_ergonomia(exercicio, percentil=50, sexo="masculino", carga_pico_kg=40)
    pegada = env["pegada"]
    print(f"Articulacao/movimento : {env['articulacao']} / {env['movimento']}")
    print(f"Eixo de pivo          : {env['alinhamento_pivo']['altura_pivo_mm']} mm")
    print(
        "Pegada                : "
        f"{pegada['orientacao']['orientacao']} | "
        f"diametro {pegada['diametro']['diametro_recomendado_mm']} mm | "
        f"distancia {pegada['largura']['distancia_entre_pegas_mm']} mm"
    )
    ajuste = env["ajustes_posto"]["altura_assento"]
    print(
        "Ajuste do assento     : "
        f"{ajuste['minimo_mm']}-{ajuste['maximo_mm']} mm (curso {ajuste['curso_mm']} mm)"
    )

    # 2) Validação do curso projetado --------------------------------------
    adm = env["amplitude_movimento"]["adm_treino"]
    val = validar_amplitude_projetada(env["articulacao"], env["movimento"], 20, 130)
    print(f"\nADM de treino         : {adm} graus")
    print(f"Curso 20-130 graus    : {'OK' if val['aprovado'] else 'REPROVADO'}")

    # 3) Casamento da curva de resistência ---------------------------------
    # Simula uma máquina de resistência constante (came circular) x came ideal.
    aval_const = avaliar_curva_resistencia([1, 1, 1, 1, 1], env["grupo_muscular"])
    perfil_ideal = env["curva_resistencia_alvo"]["resistencia_alvo_kg"]
    aval_ideal = avaliar_curva_resistencia(perfil_ideal, env["grupo_muscular"])
    print(f"\nCurva-alvo (kg)       : {perfil_ideal}")
    print(f"Came circular (const) : pontuacao {aval_const['pontuacao']}/100")
    print(f"  -> {aval_const['recomendacao']}")
    print(f"Came ideal            : pontuacao {aval_ideal['pontuacao']}/100")

    # 4) Geometria + memorial a partir da ergonomia ------------------------
    parametros = parametros_geometria_de_ergonomia(
        env, extras={"espessura_parede_mm": 3.0, "comprimento_alavanca_mm": 350}
    )
    out_dir = Path(__file__).resolve().parents[1] / "output"
    out_dir.mkdir(exist_ok=True)

    scad = gerar_script_openscad(parametros)
    memorial = gerar_memorial_descritivo(parametros)
    (out_dir / f"{exercicio}.scad").write_text(scad, encoding="utf-8")
    (out_dir / f"{exercicio}_memorial.json").write_text(
        json.dumps(memorial, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (out_dir / f"{exercicio}_ergonomia.json").write_text(
        json.dumps(env, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nArtefatos gravados em: {out_dir}")
    print(f"  - {exercicio}.scad")
    print(f"  - {exercicio}_memorial.json")
    print(f"  - {exercicio}_ergonomia.json")


if __name__ == "__main__":
    main()
