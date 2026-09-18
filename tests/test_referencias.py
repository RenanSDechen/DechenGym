"""
Testes dos Projetos de Referência e da Biblioteca de Padrões — BDD.

Base extraída dos desenhos reais de fabricação fornecidos pelo cliente
(201-ABDUTOR ... 210-ARCO + 01-PADROES).
"""

import pytest

from dechengym.data.padroes_db import (
    BIBLIOTECA_PADROES,
    get_padrao_biblioteca,
    listar_biblioteca_padroes,
)
from dechengym.data.projetos_referencia_db import (
    PADROES_CONSTRUTIVOS,
    PROJETOS_REFERENCIA,
    get_projeto_referencia,
    listar_padroes_construtivos,
)
from dechengym.fabricacao import gerar_plano_fabricacao


class TestProjetosReferencia:
    def test_base_cobre_os_projetos_enviados(self):
        # Given os desenhos enviados pelo cliente (201..210)
        # Then a base tem os 8 projetos com ficha completa
        assert len(PROJETOS_REFERENCIA) >= 8
        for chave, p in PROJETOS_REFERENCIA.items():
            assert p["nome"], chave
            assert p["fonte"], chave
            assert p["arquitetura"], chave
            w, d = p["footprint_mm"]
            assert w > 0 and d > 0, chave

    def test_abdutor_tem_pacote_de_articulacao_usinada(self):
        # Given o projeto de referência do abdutor
        p = get_projeto_referencia("abdutor_201")
        art = p["articulacao"]
        # Then eixo SAE 1045, bucha toleranciada, disco 15° e pino trava
        assert "SAE 1045" in art["eixo"]
        assert "+0,05" in art["bucha_guia"]
        assert "15°" in art["disco_regulagem"]
        assert "pino_trava" in art

    def test_projeto_inexistente_rejeitado_com_lista(self):
        # When pedimos um projeto que não existe
        with pytest.raises(ValueError, match="abdutor_201"):
            get_projeto_referencia("nao_existe")

    def test_padroes_construtivos_transversais(self):
        # Given os padrões extraídos dos desenhos
        res = listar_padroes_construtivos()
        # Then cobrem articulação, regulagem, reforço, borracha e proteção
        chaves = set(PADROES_CONSTRUTIVOS)
        assert {"articulacao_usinada", "regulagem_disco_pino",
                "gusset_trapezoidal", "amortecimento_borracha",
                "protecao_movel", "cortes_em_angulo"} <= chaves
        # And cada padrão cita o desenho de origem
        for p in res["padroes"].values():
            assert p["origem"]


class TestBibliotecaPadroes:
    def test_biblioteca_tem_componentes_chave(self):
        # Given a biblioteca 01-PADROES
        # Then os componentes que se repetem em toda máquina estão lá
        for chave in ("polia_190", "protetor_polia_disco", "pino_seletor_placas",
                      "calco_borracha_oblongo", "setor_regulagem_15",
                      "encosto_profissional", "guia_cabo_340"):
            comp = get_padrao_biblioteca(chave)
            assert comp["codigo"], chave
            assert comp["especificacao"], chave

    def test_filtro_por_categoria(self):
        # When listamos apenas as proteções
        res = listar_biblioteca_padroes("protecao")
        # Then todas as entradas são proteções (e existem >= 3 variantes)
        assert res["total"] >= 3
        assert all(v["categoria"] == "protecao"
                   for v in res["componentes"].values())

    def test_componente_inexistente_rejeitado(self):
        with pytest.raises(ValueError, match="polia_190"):
            get_padrao_biblioteca("nao_existe")


class TestPlanoFabricacaoReferencia:
    def test_plano_incorpora_pacote_de_articulacao_do_abdutor(self):
        # Given o plano de fabricação gerado
        plano = gerar_plano_fabricacao()
        itens = {c["item"]: c for c in plano["componentes"]}
        # Then flange mancal, disco de regulagem e pino trava estão presentes
        flange = itens["Flange mancal usinada"]
        assert "+0,05" in flange["processo"]
        disco = itens["Disco de regulagem da posicao inicial"]
        assert disco["espessura_mm"] == pytest.approx(12.7)
        assert "15 graus" in disco["processo"]
        pino = itens["Pino trava torneado"]
        assert "SAE 1045" in pino["material"]
        # And gussets 3,18 e calços de borracha (4 unidades cada)
        assert itens["Gusset (chapa-reforco trapezoidal)"]["espessura_mm"] == pytest.approx(3.18)
        assert itens["Calco de borracha nervurado (pe)"]["quantidade"] == 4

    def test_plano_declara_padroes_e_lista_de_corte_com_angulos(self):
        # Given o plano
        plano = gerar_plano_fabricacao()
        # Then os padrões construtivos aplicados citam a origem nos desenhos
        assert len(plano["padroes_aplicados"]) >= 6
        assert all(p["origem"] for p in plano["padroes_aplicados"])
        # And a observação exige ângulos na lista de corte
        assert "angulo" in plano["observacao_lista_corte"]

    def test_maquina_3d_mostra_o_pacote_profissional(self):
        # Given o modelo 3D da máquina
        from dechengym.montagem3d import gerar_pecas_maquina
        m = gerar_pecas_maquina({"comprimento_alavanca_mm": 800})
        nomes = " ".join(p["nome"] for p in m["pecas"])
        # Then disco de regulagem, pino trava e pés de borracha aparecem
        assert "Disco de regulagem" in nomes
        assert "Pino trava" in nomes
        assert "Pe borracha" in nomes
