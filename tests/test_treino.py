"""
Testes da camada Meu Treino (visão macro, sugestões e histórico) — BDD.
"""

import pytest

from dechengym import treino
from dechengym.data.treinos_db import DIVISOES, equipamentos_do_treino


@pytest.fixture
def caminho(tmp_path):
    return tmp_path / "historico.json"


def _semear(caminho, divisao, registros):
    treino.salvar_estado(
        {"divisao": divisao,
         "historico": [{"data": d, "letra": le} for d, le in registros]},
        caminho)


class TestSugestaoProximoTreino:
    def test_cenario_abcde_perna_depois_costas(self, caminho):
        # Given estou no ABCDE e treinei perna (C) anteontem e costas (B) ontem
        _semear(caminho, "abcde", [("2026-09-16", "C"), ("2026-09-17", "B")])
        # When abro a visão geral hoje
        v = treino.visao_geral_treino(treino.carregar_estado(caminho),
                                      hoje="2026-09-18")
        # Then o ciclo mostra 2/5 e as pendências certas
        assert v["ciclo"]["progresso"] == "2/5"
        assert v["ciclo"]["pendentes"] == ["A", "D", "E"]
        ordem = [s["letra"] for s in v["sugestoes"]]
        # And Peito é o recomendado (descansado e pendente)
        assert ordem[0] == "A" and v["sugestoes"][0]["recomendado"]
        # And Braços vem depois de Ombros: bíceps trabalhou indireto ontem
        assert ordem.index("E") > ordem.index("D")
        bracos = next(s for s in v["sugestoes"] if s["letra"] == "E")
        assert not bracos["descansado"]
        assert "indireto" in bracos["motivo"]
        # And os já feitos ficam no fim, com a data no motivo
        assert set(ordem[3:]) == {"C", "B"}

    def test_ciclo_completo_reinicia_com_todas_as_opcoes(self, caminho):
        # Given completei as 5 letras do ABCDE
        _semear(caminho, "abcde", [("2026-09-0%d" % (i + 1), le)
                                   for i, le in enumerate("ABCDE")])
        # When abro a visão dias depois
        v = treino.visao_geral_treino(treino.carregar_estado(caminho),
                                      hoje="2026-09-10")
        # Then o ciclo zera e tudo volta a ser pendente
        assert v["ciclo"]["progresso"] == "0/5"
        assert v["ciclo"]["pendentes"] == list("ABCDE")
        # And o recomendado é o grupo há mais tempo sem estímulo (A, peito)
        assert v["sugestoes"][0]["letra"] == "A"

    def test_grupo_em_recuperacao_e_penalizado(self, caminho):
        # Given treinei costas hoje mesmo
        _semear(caminho, "abc", [("2026-09-18", "B")])
        v = treino.visao_geral_treino(treino.carregar_estado(caminho),
                                      hoje="2026-09-18")
        # Then o recomendado é um treino descansado (empurrar ou pernas)
        assert v["sugestoes"][0]["letra"] in ("A", "C")
        assert v["sugestoes"][0]["descansado"]
        # And costas cai para o fim, marcada em recuperação
        ultimo = v["sugestoes"][-1]
        assert ultimo["letra"] == "B" and not ultimo["descansado"]


class TestRegistroEPersistencia:
    def test_registrar_persiste_e_atualiza_ciclo(self, caminho):
        # When registro um treino A hoje
        v = treino.registrar_treino("a", data="2026-09-18", caminho=caminho)
        # Then o estado persiste em disco e o ciclo conta 1
        assert caminho.is_file()
        assert v["ciclo"]["progresso"].startswith("1/")
        assert v["historico_recente"][0]["letra"] == "A"

    def test_letra_invalida_rejeitada_com_opcoes(self, caminho):
        _semear(caminho, "abc", [])
        with pytest.raises(ValueError, match="A/B/C"):
            treino.registrar_treino("E", caminho=caminho)

    def test_desfazer_remove_o_ultimo(self, caminho):
        treino.registrar_treino("A", data="2026-09-17", caminho=caminho)
        treino.registrar_treino("B", data="2026-09-18", caminho=caminho)
        v = treino.desfazer_ultimo(caminho)
        assert [h["letra"] for h in v["historico_recente"]] == ["A"]

    def test_mudar_divisao_preserva_historico(self, caminho):
        # Given treinos registrados no ABCDE
        _semear(caminho, "abcde", [("2026-09-17", "C")])
        # When mudo para ABCD
        v = treino.definir_divisao("abcd", caminho)
        # Then a divisão muda e o histórico continua lá
        assert v["divisao"] == "abcd"
        assert treino.carregar_estado(caminho)["historico"]
        # And divisão inexistente é rejeitada
        with pytest.raises(ValueError, match="abc"):
            treino.definir_divisao("xyz", caminho)

    def test_estado_corrompido_volta_ao_padrao(self, caminho):
        caminho.write_text("{nao é json", encoding="utf-8")
        estado = treino.carregar_estado(caminho)
        assert estado["divisao"] in DIVISOES and estado["historico"] == []


class TestLigacaoComAcademiaVirtual:
    def test_cada_treino_tem_equipamentos_da_academia(self):
        # Given qualquer letra de qualquer divisão
        for div in DIVISOES.values():
            for det in div["letras"].values():
                eqs = equipamentos_do_treino(det["grupos"])
                # Then há equipamentos reais da academia para treinar
                assert eqs, det["nome"]
                assert all("nome" in e and "rank" in e for e in eqs)

    def test_visao_traz_equipamentos_por_sugestao(self, caminho):
        _semear(caminho, "abcde", [])
        v = treino.visao_geral_treino(treino.carregar_estado(caminho),
                                      hoje="2026-09-18")
        assert all(s["equipamentos"] for s in v["sugestoes"])
