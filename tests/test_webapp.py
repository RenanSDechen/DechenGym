"""
Testes da interface web local — estrutura BDD (Given/When/Then).
"""

import pytest

from dechengym import webapp


class TestPagina:
    def test_pagina_contem_formulario_e_catalogo(self):
        # Given o catálogo de exercícios
        # When montamos a página
        html = webapp._pagina()
        # Then há formulário com os campos e os exercícios do catálogo
        for campo in ("id=\"exercicio\"", "id=\"carga\"", "id=\"perfil\"", "id=\"bGo\""):
            assert campo in html
        assert "Remada sentada" in html
        # And é auto-contida (sem recursos externos)
        assert "https://" not in html


class TestProjetarViaInterface:
    def test_projetar_gera_payload_e_artefatos(self, tmp_path, monkeypatch):
        # Given a pasta de saída da interface apontada para um tmp
        pytest.importorskip("reportlab")
        pytest.importorskip("cairosvg")
        monkeypatch.setattr(webapp, "SAIDA", tmp_path)
        # When projetamos pela mesma função usada pela rota /api/projetar
        d = webapp._projetar({"exercicio": "remada_maquina", "carga_kg": 90,
                              "perfil": "60x60", "fator_seguranca": 2.0})
        # Then o payload tem os campos que a interface consome
        for chave in ("nome", "aprovado", "resumo", "came_pontuacao", "estrutura", "links"):
            assert chave in d
        # And os artefatos foram gravados (render, viewer, scad)
        destino = tmp_path / "remada_maquina"
        assert (destino / "hero.svg").exists()
        assert (destino / "montagem_3d.html").exists()
        assert (destino / "remada_maquina.scad").exists()
