"""
Meu Treino — visão macro, sugestão do próximo treino e histórico.
=================================================================

A camada de treino do DechenGym: o usuário segue uma divisão (ABC, ABCD,
ABCDE), registra o que treinou e recebe a **visão geral do ciclo** com as
**próximas opções ranqueadas** — podendo trocar o treino do dia à vontade.

O motor de sugestão combina três sinais:

1. **Pendência no ciclo** — o que ainda não foi treinado desde a última
   volta completa da divisão vem primeiro;
2. **Recuperação muscular** — cada grupo do treino é avaliado pelos dias
   desde o último estímulo, contando também o trabalho **indireto** das
   sinergias (treinou costas ontem → bíceps ainda em recuperação);
3. **Ordem da divisão** — desempate estável pela sequência das letras.

O histórico persiste em JSON (``output/treino/historico.json`` por padrão),
para o webapp, as tools de agente e a linha de comando lerem o mesmo estado.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from dechengym.data.treinos_db import (
    DESCANSO_MINIMO_DIAS,
    DIVISAO_PADRAO,
    DIVISOES,
    equipamentos_do_treino,
    grupos_indiretos,
)

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_PADRAO = RAIZ / "output" / "treino" / "historico.json"


# ---------------------------------------------------------------- estado --
def carregar_estado(caminho: str | Path | None = None) -> dict[str, Any]:
    """Carrega o estado do treino (divisão + histórico) do disco."""
    p = Path(caminho or CAMINHO_PADRAO)
    if p.is_file():
        try:
            estado = json.loads(p.read_text(encoding="utf-8"))
            if estado.get("divisao") in DIVISOES:
                estado.setdefault("historico", [])
                return estado
        except (json.JSONDecodeError, OSError):
            pass
    return {"divisao": DIVISAO_PADRAO, "historico": []}


def salvar_estado(estado: dict[str, Any], caminho: str | Path | None = None) -> Path:
    """Grava o estado em JSON (cria o diretório se preciso)."""
    p = Path(caminho or CAMINHO_PADRAO)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(estado, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    return p


def registrar_treino(letra: str, data: str | None = None,
                     caminho: str | Path | None = None) -> dict[str, Any]:
    """Registra um treino feito (letra da divisão atual) e retorna a visão."""
    estado = carregar_estado(caminho)
    letras = DIVISOES[estado["divisao"]]["letras"]
    letra = letra.upper()
    if letra not in letras:
        raise ValueError(f"Letra '{letra}' não existe na divisão "
                         f"{estado['divisao'].upper()} ({'/'.join(letras)})")
    dia = data or date.today().isoformat()
    estado["historico"].append({"data": dia, "letra": letra})
    estado["historico"].sort(key=lambda r: r["data"])
    salvar_estado(estado, caminho)
    return visao_geral_treino(estado, hoje=dia)


def desfazer_ultimo(caminho: str | Path | None = None) -> dict[str, Any]:
    """Remove o último registro do histórico (registro errado)."""
    estado = carregar_estado(caminho)
    if estado["historico"]:
        estado["historico"].pop()
        salvar_estado(estado, caminho)
    return visao_geral_treino(estado)


def definir_divisao(divisao: str,
                    caminho: str | Path | None = None) -> dict[str, Any]:
    """Troca a divisão de treino (mantém o histórico já registrado)."""
    divisao = divisao.lower()
    if divisao not in DIVISOES:
        raise ValueError(f"Divisão '{divisao}' não existe. "
                         f"Disponíveis: {', '.join(DIVISOES)}")
    estado = carregar_estado(caminho)
    estado["divisao"] = divisao
    salvar_estado(estado, caminho)
    return visao_geral_treino(estado)


# ----------------------------------------------------------------- motor --
def _dias(a: str, b: str) -> int:
    return (date.fromisoformat(a) - date.fromisoformat(b)).days


def _ciclo_atual(letras: list[str], historico: list[dict]) -> list[dict]:
    """Registros desde a última volta completa da divisão.

    Percorre o histórico do fim para o início acumulando letras da divisão;
    quando o conjunto fecha (todas as letras vistas), tudo que veio antes
    pertence a ciclos anteriores.
    """
    vistos: set[str] = set()
    ciclo: list[dict] = []
    for reg in reversed(historico):
        if reg["letra"] not in letras:
            continue                      # registro de outra divisão
        if reg["letra"] in vistos:
            continue                      # repetição dentro do ciclo
        vistos.add(reg["letra"])
        ciclo.append(reg)
        if len(vistos) == len(letras):
            break
    ciclo.reverse()
    # ciclo completo = novo ciclo começa vazio
    return [] if len(vistos) == len(letras) else ciclo


def _recuperacao_grupos(historico: list[dict], letras_def: dict,
                        hoje: str) -> dict[str, dict[str, Any]]:
    """Dias desde o último estímulo (direto e indireto) de cada grupo."""
    rec: dict[str, dict[str, Any]] = {}
    for reg in historico:
        det = letras_def.get(reg["letra"])
        if det is None:
            continue
        for g in det["grupos"]:
            d = rec.setdefault(g, {})
            if "direto" not in d or reg["data"] > d["direto"]:
                d["direto"] = reg["data"]
            for gi in grupos_indiretos(g):
                di = rec.setdefault(gi, {})
                if "indireto" not in di or reg["data"] > di["indireto"]:
                    di["indireto"] = reg["data"]
    saida: dict[str, dict[str, Any]] = {}
    for g, d in rec.items():
        dias_dir = _dias(hoje, d["direto"]) if "direto" in d else None
        dias_ind = _dias(hoje, d["indireto"]) if "indireto" in d else None
        efetivo = min(x for x in (dias_dir, dias_ind) if x is not None)
        saida[g] = {"dias_direto": dias_dir, "dias_indireto": dias_ind,
                    "dias_efetivo": efetivo}
    return saida


def visao_geral_treino(estado: dict[str, Any] | None = None,
                       hoje: str | None = None,
                       caminho: str | Path | None = None) -> dict[str, Any]:
    """Tela macro do treino: ciclo, recuperação e próximas opções ranqueadas."""
    estado = estado or carregar_estado(caminho)
    hoje = hoje or date.today().isoformat()
    divisao = estado["divisao"]
    letras_def = DIVISOES[divisao]["letras"]
    letras = list(letras_def)
    historico = [r for r in estado["historico"] if r["data"] <= hoje]

    ciclo = _ciclo_atual(letras, historico)
    feitas = {r["letra"]: r["data"] for r in ciclo}
    recuperacao = _recuperacao_grupos(historico, letras_def, hoje)

    ultimo_por_letra: dict[str, str] = {}
    for reg in historico:
        if reg["letra"] in letras_def:
            ultimo_por_letra[reg["letra"]] = reg["data"]

    # ---- ranqueia as opções --------------------------------------------
    sugestoes = []
    for letra in letras:
        det = letras_def[letra]
        pendente = letra not in feitas
        grupos_rec = []
        pior = None
        for g in det["grupos"]:
            r = recuperacao.get(g)
            dias = r["dias_efetivo"] if r else None
            grupos_rec.append({"grupo": g, "dias_descanso": dias,
                               "indireto": bool(r and r.get("dias_indireto") is not None
                                                and (r.get("dias_direto") is None
                                                     or r["dias_indireto"] < r["dias_direto"]))})
            if dias is not None and (pior is None or dias < pior):
                pior = dias
        descansado = pior is None or pior >= DESCANSO_MINIMO_DIAS

        motivos = []
        if pendente:
            motivos.append("pendente no ciclo atual")
        else:
            motivos.append(f"já feito neste ciclo ({feitas[letra]})")
        if pior is None:
            motivos.append("grupos totalmente descansados")
        elif descansado:
            motivos.append(f"menor descanso: {pior} dia(s) — recuperado")
        else:
            quem = [gr["grupo"] + (" (indireto)" if gr["indireto"] else "")
                    for gr in grupos_rec
                    if gr["dias_descanso"] is not None
                    and gr["dias_descanso"] < DESCANSO_MINIMO_DIAS]
            motivos.append("em recuperação: " + ", ".join(quem))

        sugestoes.append({
            "letra": letra,
            "nome": det["nome"],
            "grupos": det["grupos"],
            "pendente_no_ciclo": pendente,
            "recuperacao": grupos_rec,
            "descansado": descansado,
            "ultimo_treino": ultimo_por_letra.get(letra),
            "motivo": "; ".join(motivos),
            "equipamentos": equipamentos_do_treino(det["grupos"])[:6],
            "_score": (0 if pendente else 1,
                       0 if descansado else 1,
                       -(pior if pior is not None else 999),
                       letras.index(letra)),
        })
    sugestoes.sort(key=lambda s: s.pop("_score"))
    for i, s in enumerate(sugestoes):
        s["recomendado"] = (i == 0)

    seq_7d = sum(1 for r in historico
                 if _dias(hoje, r["data"]) < 7 and r["letra"] in letras_def)
    return {
        "hoje": hoje,
        "divisao": divisao,
        "divisao_nome": DIVISOES[divisao]["nome"],
        "divisoes_disponiveis": {k: v["nome"] for k, v in DIVISOES.items()},
        "ciclo": {
            "feitos": [{"letra": r["letra"], "data": r["data"],
                        "nome": letras_def[r["letra"]]["nome"]} for r in ciclo],
            "pendentes": [le for le in letras if le not in feitas],
            "progresso": f"{len(feitas)}/{len(letras)}",
        },
        "treinos_ultimos_7_dias": seq_7d,
        "sugestoes": sugestoes,
        "historico_recente": [
            {**r, "nome": letras_def[r["letra"]]["nome"],
             "dias_atras": _dias(hoje, r["data"])}
            for r in historico[-14:] if r["letra"] in letras_def
        ][::-1],
    }
