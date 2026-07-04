"""
Testes da Academia Virtual — estrutura BDD (Given/When/Then).

Base dos equipamentos mais usados do mercado (rankings Skelcore/WodGuru/
Fitness Expo) + catálogo estruturado + planta baixa em escala.
"""

from dechengym.academia import (
    FOLGA_MAQUINA_MM,
    gerar_catalogo_academia,
    gerar_planta_academia,
)
from dechengym.data.academia_db import (
    ACADEMIA_VIRTUAL,
    categorias,
    resumo_academia,
)
from dechengym.data.exercicios_db import CATALOGO_EXERCICIOS


class TestBaseAcademia:
    def test_base_cobre_os_equipamentos_mais_usados(self):
        # Given a base compilada dos rankings do setor
        # Then ela tem pelo menos 25 equipamentos em 5 zonas
        assert len(ACADEMIA_VIRTUAL) >= 25
        assert len(categorias()) == 5

    def test_todo_equipamento_tem_ficha_tecnica_completa(self):
        # Given cada equipamento da base
        for chave, e in ACADEMIA_VIRTUAL.items():
            # Then footprint, altura, carga e referência de mercado válidos
            w, d = e["footprint_mm"]
            assert w > 0 and d > 0, chave
            assert e["altura_mm"] > 0, chave
            assert e["carga_max_kg"] > 0, chave
            assert e["referencia"], chave
            assert e["musculos"], chave
            assert e["rank"] >= 1, chave

    def test_exercicios_pipeline_apontam_para_o_catalogo_real(self):
        # Given os equipamentos com projeto completo DechenGym
        mapeados = [e["exercicio_pipeline"] for e in ACADEMIA_VIRTUAL.values()
                    if e["exercicio_pipeline"] is not None]
        # Then todos apontam para exercícios reais do pipeline
        assert len(mapeados) == 8
        for ex in mapeados:
            assert ex in CATALOGO_EXERCICIOS, ex

    def test_resumo_consistente_com_a_base(self):
        # When calculamos o resumo
        res = resumo_academia()
        # Then os totais batem com a base
        assert res["total_equipamentos"] == len(ACADEMIA_VIRTUAL)
        assert res["com_projeto_completo"] == 8
        assert sum(res["por_categoria"].values()) == len(ACADEMIA_VIRTUAL)
        assert res["area_ocupada_m2"] > 0


class TestCatalogoAcademia:
    def test_catalogo_estruturado_por_categoria(self):
        # When geramos o catálogo (formato de Tool Calling)
        cat = gerar_catalogo_academia()
        # Then há 5 categorias e todos os equipamentos da base
        assert len(cat["categorias"]) == 5
        total = sum(len(c["equipamentos"]) for c in cat["categorias"])
        assert total == len(ACADEMIA_VIRTUAL)
        # And cada item declara se tem projeto completo
        item = cat["categorias"][0]["equipamentos"][0]
        assert "projeto_completo" in item
        assert "footprint_mm" in item


class TestPlantaAcademia:
    def test_planta_svg_bem_formada_com_todos_os_equipamentos(self):
        # When geramos a planta baixa
        svg = gerar_planta_academia()
        # Then é SVG válido com um retângulo por equipamento
        assert svg.startswith("<svg")
        assert svg.rstrip().endswith("</svg>")
        for e in ACADEMIA_VIRTUAL.values():
            nome = e["nome"].split("(")[0].strip()
            if len(nome) > 24:
                nome = nome[:23] + "…"
            assert nome in svg, nome

    def test_planta_sem_sobreposicao_de_footprints(self):
        # Given o layout interno da planta
        from dechengym.academia import _layout_zonas
        itens, larg_mm, _ = _layout_zonas()
        # Then nenhum par de máquinas se sobrepõe (folga mínima 600 mm)
        for i, a in enumerate(itens):
            assert a["x"] + a["w"] <= larg_mm, a["id"]
            for b in itens[i + 1:]:
                separado = (
                    a["x"] + a["w"] + FOLGA_MAQUINA_MM <= b["x"] + 1e-6
                    or b["x"] + b["w"] + FOLGA_MAQUINA_MM <= a["x"] + 1e-6
                    or a["y"] + a["d"] <= b["y"] + 1e-6
                    or b["y"] + b["d"] <= a["y"] + 1e-6
                )
                assert separado, f"{a['id']} sobrepoe {b['id']}"
