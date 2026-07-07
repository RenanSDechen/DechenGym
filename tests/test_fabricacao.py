"""
Testes do Plano de Fabricação Industrial — estrutura BDD (Given/When/Then).

Especificações cruzadas de memoriais descritivos industriais: perfis
retangulares 75x35/80x40 (parede 2-3 mm), berços em chapa SAE 1020 de 3/8",
eixos CNC com rolamentos blindados, cremalheira inox 3 mm, solda MIG e
pintura eletrostática a pó.
"""

import pytest

from dechengym.fabricacao import PROCESSOS_FABRICACAO, gerar_plano_fabricacao
from dechengym.orquestrador import RequisicaoProjeto, projetar_maquina


class TestPlanoFabricacao:
    def test_berco_em_chapa_sae1020_de_tres_oitavos(self):
        # Given o plano de fabricação iso-lateral
        plano = gerar_plano_fabricacao({"perfil": "40x80"})
        # When localizamos o berço de articulação
        berco = next(c for c in plano["componentes"] if "Berco" in c["item"])
        # Then é chapa SAE 1020 de 9,525 mm (3/8"), corte a laser, 4 unidades
        assert berco["espessura_mm"] == pytest.approx(9.525)
        assert "SAE 1020" in berco["material"]
        assert "laser" in berco["processo"].lower()
        assert berco["quantidade"] == 4  # 2 por braço × 2 braços

    def test_eixos_cnc_com_rolamentos_blindados_sem_buchas(self):
        # Given o plano
        plano = gerar_plano_fabricacao()
        # When localizamos eixo e rolamentos
        eixo = next(c for c in plano["componentes"] if c["item"] == "Eixo de articulacao")
        rol = next(c for c in plano["componentes"] if "Rolamento" in c["item"])
        # Then eixo é usinado em CNC sem buchas plásticas, 2 rolamentos/eixo
        assert "CNC" in eixo["material"] or "CNC" in eixo["processo"]
        assert "bucha" in eixo["processo"].lower()  # menciona a proibição
        assert rol["quantidade"] == 4

    def test_cremalheira_inox_3mm_e_chapas_de_estofado_4mm(self):
        # Given o plano
        plano = gerar_plano_fabricacao()
        crem = next(c for c in plano["componentes"] if "Cremalheira" in c["item"])
        base_enc = next(c for c in plano["componentes"] if "encosto" in c["item"])
        # Then cremalheira inox 3 mm; bases de estofado chapa 4 mm
        assert crem["espessura_mm"] == pytest.approx(3.0)
        assert "inox" in crem["material"].lower()
        assert base_enc["espessura_mm"] == pytest.approx(4.0)

    def test_processos_incluem_mig_e_pintura_eletrostatica(self):
        # Given os processos obrigatórios
        nomes = " ".join(p["processo"] for p in PROCESSOS_FABRICACAO)
        # Then MIG e pintura eletrostática a pó estão listados
        assert "MIG" in nomes
        assert "eletrost" in nomes.lower()

    def test_footprint_e_altura_das_hastes(self):
        # Given a estrutura do plano
        est = gerar_plano_fabricacao()["estrutura"]
        # Then footprint 120x150 cm e hastes até 180 cm (specs industriais)
        assert est["footprint_mm"] == [1200, 1500]
        assert est["altura_maxima_hastes_mm"] == 1800


class TestPerfilRetangularNoPipeline:
    def test_pipeline_com_40x80_usa_perfil_correto_no_memorial(self):
        # Given uma remada com perfil retangular 40x80 (alma na vertical)
        proj = projetar_maquina(RequisicaoProjeto(
            "remada_maquina", carga_kg=120, perfil="40x80",
            comprimento_alavanca_mm=800, fator_seguranca=2.5))
        # Then o memorial identifica o perfil retangular (não "40x40")
        assert proj["geometria"]["memorial"]["lista_cortes"][0]["perfil"] == "40x80"
        # And o peso foi estimado (perfil existe no catálogo)
        assert proj["geometria"]["memorial"]["peso_total_completo"] is True
        # And a parede escolhida respeita a faixa industrial (2-3 mm)
        assert proj["estrutura"]["espessura_escolhida_mm"] in (2.0, 3.0)
        # And o plano de fabricação acompanha o projeto
        assert "fabricacao" in proj
        assert len(proj["fabricacao"]["componentes"]) >= 7

    def test_perfil_75x35_disponivel_no_catalogo(self):
        # Given o catálogo atualizado
        from dechengym.calculo_estrutural import get_especificacao_metalon
        # When consultamos 75x35 com parede 2 mm
        spec = get_especificacao_metalon("35x75", 2.0)
        # Then propriedades positivas com a alma de 75 mm na vertical
        assert spec["modulo_secao_mm3"] > 0
        assert spec["dimensoes_mm"]["altura"] == 75
