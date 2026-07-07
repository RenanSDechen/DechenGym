"""
Testes do modelo 3D Remada Frontal (desenhos 901-904 do acervo) — BDD.
"""

from dechengym.montagem3d import (
    ETAPAS_REMADA_FRONTAL,
    gerar_pecas_maquina,
    gerar_pecas_remada_frontal,
    renderizar_svg_3d,
)


class TestRemadaFrontal:
    def test_arquitetura_do_acervo_com_cotas_do_desenho_901(self):
        # Given o modelo gerado com a arquitetura do acervo
        m = gerar_pecas_remada_frontal({})
        specs = m["specs"]
        # Then as cotas-chave do desenho 901 estão declaradas
        assert "1700" in specs["torre_mm"]
        assert "550 x 500" in specs["braco_u_mm"]
        assert "Ø42 +0,05" in specs["bucha_pivo"]
        assert "15 graus" in specs["coluna_inclinada"]
        assert "901" in specs["referencia"]

    def test_pecas_essenciais_presentes(self):
        # Given as peças do modelo
        nomes = " | ".join(p["nome"] for p in gerar_pecas_remada_frontal({})["pecas"])
        # Then torre, tijolos, braço em U, bucha, polias e cabo existem
        for esperado in ("Torre Ø60", "Tijolo 10", "Haste-guia", "Braco em U",
                         "Bucha Ø48", "Pega cruz", "Polia do topo", "Cabo de aco",
                         "Apoio de peito", "Apoio de pe"):
            assert esperado in nomes, esperado

    def test_dispatch_por_parametro_arquitetura(self):
        # When gerar_pecas_maquina recebe arquitetura remada_frontal
        m = gerar_pecas_maquina({"arquitetura": "remada_frontal"})
        # Then delega ao modelo do acervo (etapas próprias)
        assert m["etapas"] == ETAPAS_REMADA_FRONTAL
        assert len(m["etapas"]) == 7

    def test_nenhuma_peca_abaixo_do_piso(self):
        # Given todas as peças mesh do modelo
        m = gerar_pecas_remada_frontal({})
        for p in m["pecas"]:
            if p.get("tipo") == "mesh" and "rot" not in p:
                y_min = min(v[1] for v in p["verts"])
                # Then nada atravessa o piso (tolerância de 1 mm)
                assert y_min >= -1.0, f"{p['nome']} em y={y_min}"

    def test_render_svg_valido(self):
        # When renderizamos o modelo
        svg = renderizar_svg_3d(gerar_pecas_remada_frontal({}), largura_px=400,
                                yaw_graus=140, pitch_graus=14)
        # Then o SVG é bem formado
        assert svg.startswith("<svg") and svg.rstrip().endswith("</svg>")

    def test_pipeline_remada_usa_arquitetura_do_acervo(self):
        # Given um projeto de remada pelo pipeline completo
        from dechengym.orquestrador import RequisicaoProjeto, projetar_maquina
        proj = projetar_maquina(RequisicaoProjeto("remada_maquina", carga_kg=80))
        # Then os parâmetros de geometria carregam a arquitetura do acervo
        assert proj["geometria"]["parametros"]["arquitetura"] == "remada_frontal"
