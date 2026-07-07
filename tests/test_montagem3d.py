"""
Testes de Montagem 3D e Dossiê PDF — estrutura BDD (Given/When/Then).
"""

import xml.etree.ElementTree as ET

import pytest

from dechengym.montagem3d import (
    ETAPAS_MONTAGEM,
    gerar_pecas_maquina,
    gerar_visualizador_html,
    renderizar_svg_3d,
)


class TestModelo3D:
    def test_modelo_iso_lateral_tem_dois_bracos(self):
        # Given parâmetros de geometria
        par = {"perfil_base_mm": 60, "comprimento_alavanca_mm": 520,
               "altura_coluna_mm": 540, "diametro_pega_mm": 38}
        # When geramos o modelo iso-lateral
        mod = gerar_pecas_maquina(par, iso_lateral=True)
        # Then há dois braços e duas pegas
        nomes = [p["nome"] for p in mod["pecas"]]
        assert sum("Braco articulado" in n for n in nomes) == 2
        assert sum("Pega neutra" in n for n in nomes) == 2
        assert mod["specs"]["n_bracos"] == 2

    def test_modelo_braco_unico(self):
        # Given o modo braço único
        mod = gerar_pecas_maquina({}, iso_lateral=False)
        # Then há apenas um braço
        nomes = [p["nome"] for p in mod["pecas"]]
        assert sum("Braco articulado" in n for n in nomes) == 1

    def test_toda_peca_tem_etapa_valida(self):
        # Given o modelo completo
        mod = gerar_pecas_maquina({})
        # Then cada peça pertence a uma etapa de montagem existente
        for p in mod["pecas"]:
            assert 1 <= p["etapa"] <= len(ETAPAS_MONTAGEM)
        # And todas as etapas têm ao menos uma peça
        etapas_usadas = {p["etapa"] for p in mod["pecas"]}
        assert etapas_usadas == set(range(1, len(ETAPAS_MONTAGEM) + 1))


class TestRenderSVG3D:
    def test_svg_valido_e_sombreado(self):
        # Given o modelo
        mod = gerar_pecas_maquina({})
        # When renderizamos
        svg = renderizar_svg_3d(mod, largura_px=600, titulo="Teste")
        # Then é XML bem-formado com polígonos sombreados
        raiz = ET.fromstring(svg)
        assert raiz.tag.endswith("svg")
        assert svg.count("<polygon") > 50

    def test_etapa_max_limita_pecas(self):
        # Given o modelo
        mod = gerar_pecas_maquina({})
        # When renderizamos só a etapa 1 vs todas
        s1 = renderizar_svg_3d(mod, etapa_max=1)
        s6 = renderizar_svg_3d(mod, etapa_max=6)
        # Then a etapa 1 tem menos polígonos
        assert s1.count("<polygon") < s6.count("<polygon")

    def test_explosao_desloca_pecas(self):
        # Given o modelo
        mod = gerar_pecas_maquina({})
        # When renderizamos montado e explodido
        s0 = renderizar_svg_3d(mod, explosao=0.0)
        s1 = renderizar_svg_3d(mod, explosao=0.9)
        # Then o desenho muda (peças deslocadas)
        assert s0 != s1


class TestVisualizadorHTML:
    def test_html_autocontido_com_dados_e_controles(self):
        # Given o modelo
        mod = gerar_pecas_maquina({})
        # When geramos o visualizador
        html = gerar_visualizador_html(mod, titulo="Maquina X")
        # Then é auto-contido (canvas + dados embutidos + controles)
        assert "<canvas" in html
        assert '"pecas"' in html
        assert 'id="rEt"' in html and 'id="rEx"' in html  # sliders
        assert "Maquina X" in html
        # And não referencia nenhum recurso externo
        assert "http://" not in html and "https://" not in html


class TestDossiePDF:
    def test_pdf_e_gerado_e_valido(self, tmp_path):
        # Given um projeto completo
        reportlab = pytest.importorskip("reportlab")  # noqa: F841
        pytest.importorskip("cairosvg")
        from dechengym.orquestrador import RequisicaoProjeto, projetar_maquina
        from dechengym.relatorio_pdf import gerar_dossie_pdf

        proj = projetar_maquina(RequisicaoProjeto("remada_maquina", carga_kg=100))
        # When geramos o dossiê
        caminho = gerar_dossie_pdf(proj, tmp_path / "dossie.pdf", titulo="Teste")
        # Then o arquivo é um PDF válido e não-trivial
        dados = open(caminho, "rb").read()
        assert dados.startswith(b"%PDF")
        assert len(dados) > 50_000  # contém os renders

    def test_artefatos_incluem_html_e_pdf(self, tmp_path):
        # Given o orquestrador com diretório de saída
        pytest.importorskip("reportlab")
        pytest.importorskip("cairosvg")
        from dechengym.orquestrador import AdaptadorRegras, orquestrar

        # When orquestramos
        orquestrar("remada 80kg", adaptador=AdaptadorRegras(), diretorio_saida=tmp_path)
        # Then o visualizador 3D e o dossiê PDF estão entre os artefatos
        nomes = {f.name for f in tmp_path.iterdir()}
        assert "montagem_3d.html" in nomes
        assert any(n.startswith("dossie_") and n.endswith(".pdf") for n in nomes)
