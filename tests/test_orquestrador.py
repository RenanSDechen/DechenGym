"""
Testes do Orquestrador — estrutura BDD (Given/When/Then).
=========================================================

Cobrem o adaptador de regras (interpretação offline do briefing), o pipeline
determinístico (com autocorreção estrutural) e o ponto de entrada orquestrar.
"""

import json

import pytest

from dechengym.orquestrador import (
    AdaptadorRegras,
    RequisicaoProjeto,
    adaptador_padrao,
    orquestrar,
    projetar_maquina,
)
from dechengym.orquestrador.agente import _gravar_artefatos


# ==========================================================================
# Adaptador de regras (interpretação do briefing)
# ==========================================================================
class TestAdaptadorRegras:
    def test_interpreta_exercicio_carga_sexo_percentil(self):
        # Given um briefing em linguagem natural
        brief = "Quero uma rosca de biceps para 40 kg, publico feminino P30"
        # When interpretamos com o adaptador de regras
        req = AdaptadorRegras().interpretar(brief)
        # Then extrai exercício, carga, sexo e percentil
        assert req.exercicio == "rosca_biceps"
        assert req.carga_kg == pytest.approx(40.0)
        assert req.sexo == "feminino"
        assert req.percentil == pytest.approx(30.0)

    def test_reconhece_sinonimos_de_exercicio(self):
        # Given briefings com sinônimos
        # When interpretamos
        # Then mapeia para o exercício do catálogo
        assert AdaptadorRegras().interpretar("maquina para peito").exercicio == "supino_maquina"
        assert AdaptadorRegras().interpretar("cadeira extensora").exercicio == "cadeira_extensora"
        assert AdaptadorRegras().interpretar("treino de triceps").exercicio == "triceps_maquina"

    def test_objetivo_pega_forca_preensao(self):
        # Given menção a pegada grossa/preensão
        req = AdaptadorRegras().interpretar("supino com pegada grossa para preensao")
        # Then escolhe o objetivo de força de preensão
        assert req.objetivo_pega == "forca_preensao"

    def test_defaults_quando_briefing_vago(self):
        # Given um briefing sem números
        req = AdaptadorRegras().interpretar("uma maquina de rosca")
        # Then usa defaults sensatos
        assert req.carga_kg == pytest.approx(100.0)
        assert req.percentil == pytest.approx(50.0)
        assert req.sexo == "masculino"

    def test_adaptador_padrao_sem_api_key_usa_regras(self, monkeypatch):
        # Given nenhuma ANTHROPIC_API_KEY
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        # When pedimos o adaptador padrão
        # Then é o de regras (offline)
        assert adaptador_padrao().nome == "regras"


# ==========================================================================
# Pipeline determinístico
# ==========================================================================
class TestPipeline:
    def test_projeto_completo_tem_todas_as_etapas(self):
        # Given uma requisição estruturada
        req = RequisicaoProjeto("rosca_biceps", carga_kg=40, comprimento_alavanca_mm=350)
        # When projetamos a máquina
        proj = projetar_maquina(req)
        # Then o projeto reúne ergonomia, came, estrutura, geometria e imagem
        for chave in ("ergonomia", "came", "estrutura", "geometria", "imagem"):
            assert chave in proj
        # And a came casa com a curva de força
        assert proj["came"]["avaliacao"]["pontuacao"] >= 99.0
        # And gera geometria e memorial
        assert "module maquina_articulada" in proj["geometria"]["openscad"]
        assert proj["geometria"]["memorial"]["peso_total_estrutura_kg"] > 0

    def test_autocorrecao_escolhe_menor_espessura_aprovada(self):
        # Given carga alta numa alavanca longa (parede fina reprova)
        req = RequisicaoProjeto(
            "cadeira_extensora", carga_kg=120, comprimento_alavanca_mm=500, perfil="50x50"
        )
        # When projetamos
        proj = projetar_maquina(req)
        estr = proj["estrutura"]
        # Then o loop iterou (mais de uma tentativa) e escolheu uma espessura
        assert len(estr["iteracoes"]) >= 1
        assert estr["aprovado"] is True
        assert estr["espessura_escolhida_mm"] is not None
        # And as tentativas anteriores à escolhida foram reprovadas
        escolhida = estr["espessura_escolhida_mm"]
        for it in estr["iteracoes"]:
            if it["espessura_parede_mm"] < escolhida:
                assert it["aprovado"] is False

    def test_carga_impossivel_para_perfil_pequeno_reprova(self):
        # Given carga enorme num perfil pequeno
        req = RequisicaoProjeto(
            "rosca_biceps", carga_kg=500, comprimento_alavanca_mm=800, perfil="20x20"
        )
        # When projetamos
        proj = projetar_maquina(req)
        # Then a estrutura reprova em todas as espessuras
        assert proj["estrutura"]["aprovado"] is False
        assert proj["aprovado"] is False

    def test_espessura_escolhida_alimenta_a_geometria(self):
        # Given um projeto aprovado
        req = RequisicaoProjeto("rosca_biceps", carga_kg=40, comprimento_alavanca_mm=350)
        proj = projetar_maquina(req)
        # When comparamos a espessura escolhida com a da geometria
        escolhida = proj["estrutura"]["espessura_escolhida_mm"]
        # Then a geometria usa exatamente a espessura validada
        assert proj["geometria"]["parametros"]["espessura_parede_mm"] == escolhida


# ==========================================================================
# Ponto de entrada orquestrar
# ==========================================================================
class TestOrquestrar:
    def test_briefing_ate_projeto_com_adaptador_de_regras(self):
        # Given um briefing em linguagem natural
        brief = "cadeira extensora para 100 kg, feminino P50"
        # When orquestramos com o adaptador de regras
        res = orquestrar(brief, adaptador=AdaptadorRegras())
        # Then interpreta e projeta
        assert res["adaptador"] == "regras"
        assert res["requisicao"]["exercicio"] == "cadeira_extensora"
        assert "resumo" in res["projeto"]

    def test_sobrescritas_forcam_parametros(self):
        # Given um briefing e uma sobrescrita de perfil
        brief = "rosca de biceps 40 kg"
        # When orquestramos forçando o perfil
        res = orquestrar(brief, adaptador=AdaptadorRegras(), perfil="60x60")
        # Then o projeto usa o perfil forçado
        assert res["requisicao"]["perfil"] == "60x60"

    def test_grava_artefatos_em_disco(self, tmp_path):
        # Given um projeto
        proj = projetar_maquina(RequisicaoProjeto("rosca_biceps", carga_kg=40))
        # When gravamos os artefatos
        criados = _gravar_artefatos(proj, tmp_path)
        # Then os arquivos existem e o projeto.json é parseável
        assert any(c.endswith(".scad") for c in criados)
        assert any(c.endswith("_preview.svg") for c in criados)
        proj_json = next(c for c in criados if c.endswith("_projeto.json"))
        dados = json.loads(open(proj_json, encoding="utf-8").read())
        assert "aprovado" in dados and "resumo" in dados
