"""
Exemplo: geração da imagem do produto.
=====================================

Fecha o pipeline: ergonomia -> geometria -> imagem, produzindo:

1. Um preview técnico 2D em SVG (blueprint, sem dependências).
2. O prompt para um modelo de texto->imagem (render de produto).
3. (Opcional) um render PNG via OpenSCAD, se o executável estiver instalado.

Execução:

    python examples/exemplo_imagem.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dechengym.ergonomia import projetar_ergonomia  # noqa: E402
from dechengym.geracao_imagem import (  # noqa: E402
    gerar_imagem,
    montar_prompt_imagem_produto,
    renderizar_openscad_png,
)
from dechengym.geracao_openscad import (  # noqa: E402
    gerar_script_openscad,
    parametros_geometria_de_ergonomia,
)


def main() -> None:
    exercicio = "rosca_biceps"
    out_dir = Path(__file__).resolve().parents[1] / "output"
    out_dir.mkdir(exist_ok=True)

    print(f"== DechenGym :: Imagem do produto :: {exercicio} ==\n")

    # Ergonomia -> geometria ------------------------------------------------
    env = projetar_ergonomia(exercicio, percentil=50, sexo="masculino", carga_pico_kg=40)
    parametros = parametros_geometria_de_ergonomia(
        env, extras={"comprimento_alavanca_mm": 350, "espessura_parede_mm": 3.0}
    )
    adm = env["amplitude_movimento"]["adm_treino"]

    # 1) Preview SVG (blueprint) -------------------------------------------
    svg_path = gerar_imagem(
        parametros,
        out_dir / f"{exercicio}_preview.svg",
        angulo_inicial_graus=adm[0],
        angulo_final_graus=min(adm[1], 90),
    )
    print(f"[1] Preview SVG: {svg_path}")

    # 2) Prompt para modelo de imagem --------------------------------------
    prompt = montar_prompt_imagem_produto(parametros, envelope_ergonomico=env)
    (out_dir / f"{exercicio}_prompt_imagem.json").write_text(
        json.dumps(prompt, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"[2] Prompt de imagem: output/{exercicio}_prompt_imagem.json")
    print(f"    -> {prompt['prompt'][:110]}...")

    # 3) Render PNG via OpenSCAD (se disponível) ---------------------------
    scad_path = out_dir / f"{exercicio}.scad"
    scad_path.write_text(gerar_script_openscad(parametros), encoding="utf-8")
    try:
        png = renderizar_openscad_png(scad_path)
        print(f"[3] Render PNG: {png}")
    except RuntimeError as exc:
        print(f"[3] Render PNG indisponivel: {exc}")


if __name__ == "__main__":
    main()
