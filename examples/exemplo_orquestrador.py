"""
Exemplo: do briefing ao projeto validado (orquestrador).
=======================================================

Recebe um briefing em linguagem natural e produz um projeto completo e
validado — ergonomia, came de resistência variável, estrutura com
autocorreção, geometria OpenSCAD, memorial e imagem — gravando os artefatos.

Uso:
    python examples/exemplo_orquestrador.py
    python examples/exemplo_orquestrador.py "cadeira extensora 120kg feminino P50"

Sem ``ANTHROPIC_API_KEY``, usa o adaptador de regras (offline). Com a chave
(e o pacote ``anthropic``), interpreta briefings livres via Claude.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dechengym.orquestrador import adaptador_padrao, orquestrar  # noqa: E402


def main() -> None:
    briefing = (
        " ".join(sys.argv[1:])
        or "Quero uma rosca de biceps para 40 kg, publico feminino P50, pegada de conforto"
    )
    out_dir = Path(__file__).resolve().parents[1] / "output"

    print("== DechenGym :: Orquestrador ==\n")
    print(f"Adaptador : {adaptador_padrao().nome}")
    print(f"Briefing  : {briefing}\n")

    res = orquestrar(briefing, diretorio_saida=out_dir)
    req = res["requisicao"]
    proj = res["projeto"]

    print(
        "Interpretado: "
        f"{req['exercicio']} | {req['carga_kg']} kg | {req['sexo']} "
        f"P{int(req['percentil'])} | pega {req['objetivo_pega']}"
    )
    print(f"\n{proj['resumo']}")

    estr = proj["estrutura"]
    print("\nAutocorrecao estrutural:")
    for it in estr["iteracoes"]:
        estado = "OK" if it["aprovado"] else "reprovado"
        print(f"  parede {it['espessura_parede_mm']} mm -> {estado} (util {it['coef_utilizacao']})")

    print(f"\nCasamento da came : {proj['came']['avaliacao']['pontuacao']}/100")
    print(f"Peso da estrutura : {proj['geometria']['memorial']['peso_total_estrutura_kg']} kg")
    print(f"Projeto aprovado  : {proj['aprovado']}")
    print(f"\nArtefatos gravados em: {out_dir}")


if __name__ == "__main__":
    main()
