"""
Interface Web local do DechenGym
================================

Servidor **local** (stdlib, sem dependências novas) com uma interface no
navegador para projetar máquinas: escolha o exercício e os parâmetros (ou
escreva um briefing livre), clique em **Projetar** e receba o resumo, o
histórico de autocorreção estrutural, o render 3D, o visualizador de
montagem interativo e o dossiê PDF.

Uso::

    python -m dechengym.webapp            # http://127.0.0.1:8765
    python -m dechengym.webapp 9000       # porta customizada

Os artefatos de cada projeto são gravados em ``output/webapp/<exercicio>/``.
"""

from __future__ import annotations

import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from dechengym.academia import gerar_catalogo_academia, gerar_planta_academia
from dechengym.data.exercicios_db import CATALOGO_EXERCICIOS
from dechengym.data.metalon_db import perfis_disponiveis
from dechengym.orquestrador import AdaptadorRegras, orquestrar
from dechengym.treino import (
    definir_divisao,
    desfazer_ultimo,
    registrar_treino,
    visao_geral_treino,
)

RAIZ = Path(__file__).resolve().parents[2]
SAIDA = RAIZ / "output" / "webapp"

_PAGINA = """<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>DechenGym — Estúdio de Projeto</title>
<style>
:root{--bg:#0f1216;--panel:#171b21;--line:#262c34;--txt:#e8ebef;--mut:#9aa4b0;--acc:#e0a422;--ok:#22c55e;--err:#ef4444}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--txt);font:14px/1.5 'Segoe UI',system-ui,sans-serif;min-height:100vh}
header{padding:16px 26px;border-bottom:1px solid var(--line);display:flex;align-items:baseline;gap:14px}
header h1{font-size:19px}header h1 b{color:var(--acc)}
header span{color:var(--mut);font-size:12.5px}
main{display:grid;grid-template-columns:340px 1fr;gap:0;min-height:calc(100vh - 58px)}
form{background:var(--panel);border-right:1px solid var(--line);padding:20px;display:flex;flex-direction:column;gap:12px}
h2{font-size:11.5px;text-transform:uppercase;letter-spacing:.09em;color:var(--mut);margin-top:6px}
label{font-size:12.5px;color:var(--mut);display:block;margin-bottom:4px}
input,select,textarea{width:100%;background:#0e1114;border:1px solid var(--line);border-radius:8px;color:var(--txt);padding:8px 10px;font-size:13.5px}
textarea{resize:vertical;min-height:56px}
.linha{display:grid;grid-template-columns:1fr 1fr;gap:10px}
button{background:var(--acc);border:0;border-radius:9px;color:#14161a;font-weight:700;font-size:14px;padding:11px;cursor:pointer}
button.sec{background:#232a33;color:var(--txt);border:1px solid var(--line);font-weight:500;font-size:12.5px;padding:8px}
button:disabled{opacity:.55;cursor:wait}
#res{padding:26px;overflow-y:auto}
.vazio{color:var(--mut);text-align:center;margin-top:16vh}
.vazio div{font-size:44px;margin-bottom:10px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;margin-bottom:16px}
.topo{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.topo h3{font-size:17px}
.selo{padding:5px 14px;border-radius:999px;font-weight:700;font-size:12.5px}
.selo.ok{background:rgba(34,197,94,.15);color:var(--ok);border:1px solid rgba(34,197,94,.4)}
.selo.no{background:rgba(239,68,68,.15);color:var(--err);border:1px solid rgba(239,68,68,.4)}
.resumo{color:var(--mut);margin-top:8px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:10px;margin-top:14px}
.kpi{background:#0e1114;border:1px solid var(--line);border-radius:10px;padding:10px}
.kpi b{display:block;font-size:16px}.kpi span{font-size:11.5px;color:var(--mut)}
.render{width:100%;border-radius:10px;border:1px solid var(--line);background:#fff}
.acoes{display:flex;gap:10px;flex-wrap:wrap;margin-top:6px}
.acoes a{background:#232a33;border:1px solid var(--line);border-radius:9px;color:var(--txt);text-decoration:none;padding:9px 14px;font-size:13px}
.acoes a.pri{background:var(--acc);color:#14161a;font-weight:700}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:8px}
td,th{padding:6px 8px;text-align:left;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-weight:600}
td.ok{color:var(--ok)}td.no{color:var(--err)}
#err{color:var(--err);font-size:12.5px;display:none}
footer{padding:10px 26px;border-top:1px solid var(--line);color:var(--mut);font-size:11.5px}
@media(max-width:860px){main{grid-template-columns:1fr}form{border-right:0;border-bottom:1px solid var(--line)}}
</style></head><body>
<header><h1><b>Dechen</b>Gym · Estúdio de Projeto</h1><span>briefing → ergonomia → came → estrutura → 3D → dossiê</span><a href="/treino" style="margin-left:auto;color:var(--acc);text-decoration:none;font-weight:600">💪 Meu Treino →</a><a href="/academia" style="color:var(--acc);text-decoration:none;font-weight:600">🏟 Academia Virtual →</a></header>
<main>
<form id="f" onsubmit="return false">
  <h2>Briefing livre (opcional)</h2>
  <textarea id="brief" placeholder="Ex.: remada iso lateral premium para 120 kg, publico feminino P50, pegada de conforto"></textarea>
  <button class="sec" id="bInterp">Interpretar briefing → preencher campos</button>
  <h2>Parâmetros</h2>
  <div><label>Exercício</label><select id="exercicio">__OPCOES_EX__</select></div>
  <div class="linha">
    <div><label>Carga (kg)</label><input id="carga" type="number" value="120" min="10" max="500"></div>
    <div><label>Fator de segurança</label><input id="fs" type="number" value="2.0" step="0.1" min="1.2" max="4"></div>
  </div>
  <div class="linha">
    <div><label>Percentil</label><input id="percentil" type="number" value="50" min="5" max="95"></div>
    <div><label>Sexo (nominal)</label><select id="sexo"><option>masculino</option><option>feminino</option></select></div>
  </div>
  <div class="linha">
    <div><label>Perfil metalon</label><select id="perfil">__OPCOES_PERFIL__</select></div>
    <div><label>Alavanca (mm)</label><input id="alavanca" type="number" value="520" min="200" max="900"></div>
  </div>
  <div><label>Objetivo da pega</label><select id="pega"><option value="conforto">conforto</option><option value="forca_preensao">força de preensão</option><option value="precisao">precisão</option></select></div>
  <button id="bGo">⚙ Projetar máquina</button>
  <div id="err"></div>
</form>
<section id="res"><div class="vazio"><div>🏋️</div>Configure os parâmetros (ou interprete um briefing)<br/>e clique em <b>Projetar máquina</b>.</div></section>
</main>
<footer>DechenGym — pipeline validado por 97 testes · artefatos em output/webapp/ · servidor local</footer>
<script>
const $=id=>document.getElementById(id);
const qs=new URLSearchParams(location.search);
if(qs.get('exercicio')){document.addEventListener('DOMContentLoaded',()=>{$('exercicio').value=qs.get('exercicio')});}
$('bInterp').onclick=async()=>{
  const r=await fetch('/api/interpretar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({briefing:$('brief').value})});
  const d=await r.json();
  $('exercicio').value=d.exercicio;$('carga').value=d.carga_kg;$('percentil').value=d.percentil;
  $('sexo').value=d.sexo;$('pega').value=d.objetivo_pega;
};
$('bGo').onclick=async()=>{
  $('bGo').disabled=true;$('bGo').textContent='Projetando… (gera 3D e PDF)';$('err').style.display='none';
  try{
    const corpo={exercicio:$('exercicio').value,carga_kg:+$('carga').value,percentil:+$('percentil').value,
      sexo:$('sexo').value,objetivo_pega:$('pega').value,perfil:$('perfil').value,
      comprimento_alavanca_mm:+$('alavanca').value,fator_seguranca:+$('fs').value};
    const r=await fetch('/api/projetar',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(corpo)});
    const d=await r.json();
    if(!r.ok)throw new Error(d.erro||'falha');
    render(d);
  }catch(e){$('err').textContent='Erro: '+e.message;$('err').style.display='block';}
  $('bGo').disabled=false;$('bGo').textContent='⚙ Projetar máquina';
};
function render(d){
  const it=d.estrutura.iteracoes.map(i=>`<tr><td>${i.espessura_parede_mm} mm</td><td>${i.coef_utilizacao}</td><td class="${i.aprovado?'ok':'no'}">${i.aprovado?'APROVADO':'reprovado'}</td></tr>`).join('');
  $('res').innerHTML=`
  <div class="card"><div class="topo"><h3>${d.nome}</h3>
    <span class="selo ${d.aprovado?'ok':'no'}">${d.aprovado?'APROVADO':'REVISAR'}</span></div>
    <p class="resumo">${d.resumo}</p>
    <div class="kpis">
      <div class="kpi"><b>${d.came_pontuacao}/100</b><span>casamento came × força</span></div>
      <div class="kpi"><b>${d.estrutura.espessura_escolhida_mm??'—'} mm</b><span>parede (autocorreção)</span></div>
      <div class="kpi"><b>${d.pivo_mm} mm</b><span>altura do pivô</span></div>
      <div class="kpi"><b>Ø ${d.pega_mm} mm</b><span>pega ${d.pega_tipo}</span></div>
      <div class="kpi"><b>${d.peso_kg} kg</b><span>estrutura (memorial)</span></div>
    </div></div>
  <div class="card"><img class="render" src="${d.links.render}?t=${Date.now()}" alt="render 3D"/>
    <div class="acoes" style="margin-top:12px">
      <a class="pri" href="${d.links.viewer}" target="_blank">🧊 Visualizador 3D interativo</a>
      <a href="${d.links.pdf}" target="_blank">📄 Dossiê PDF</a>
      <a href="${d.links.scad}" download>⚙ OpenSCAD (.scad)</a>
      <a href="${d.links.memorial}" target="_blank">🧾 Memorial (JSON)</a>
    </div></div>
  <div class="card"><h2 style="margin:0 0 4px">Autocorreção estrutural (FS ${d.fs})</h2>
    <table><tr><th>Parede</th><th>Utilização σ/σ_adm</th><th>Resultado</th></tr>${it}</table></div>`;
}
</script></body></html>"""


def _pagina() -> str:
    op_ex = "".join(
        f'<option value="{k}"{" selected" if k == "remada_maquina" else ""}>{v["nome"]}</option>'
        for k, v in sorted(CATALOGO_EXERCICIOS.items(), key=lambda kv: kv[1]["nome"])
    )
    op_perfil = "".join(
        f'<option{" selected" if p == "40x80" else ""}>{p}</option>' for p in perfis_disponiveis()
    )
    return _PAGINA.replace("__OPCOES_EX__", op_ex).replace("__OPCOES_PERFIL__", op_perfil)


def _projetar(corpo: dict) -> dict:
    """Executa o pipeline e devolve o payload da interface."""
    exercicio = corpo.get("exercicio", "remada_maquina")
    destino = SAIDA / exercicio
    res = orquestrar(
        corpo.get("briefing", exercicio),
        adaptador=AdaptadorRegras(),
        diretorio_saida=destino,
        exercicio=exercicio,
        carga_kg=float(corpo.get("carga_kg", 100)),
        percentil=float(corpo.get("percentil", 50)),
        sexo=corpo.get("sexo", "masculino"),
        objetivo_pega=corpo.get("objetivo_pega", "conforto"),
        perfil=corpo.get("perfil", "60x60"),
        comprimento_alavanca_mm=float(corpo.get("comprimento_alavanca_mm", 520)),
        fator_seguranca=float(corpo.get("fator_seguranca", 2.0)),
    )
    proj = res["projeto"]
    erg = proj["ergonomia"]

    # Render hero para a interface
    from dechengym.montagem3d import gerar_pecas_maquina, renderizar_svg_3d

    modelo = gerar_pecas_maquina(proj["geometria"]["parametros"], iso_lateral=True)
    (destino / "hero.svg").write_text(
        renderizar_svg_3d(modelo, largura_px=1000, yaw_graus=78, pitch_graus=8),
        encoding="utf-8",
    )

    base = f"/output/webapp/{exercicio}"
    tem_pdf = (destino / f"dossie_{exercicio}.pdf").exists()
    return {
        "nome": erg["nome"],
        "aprovado": proj["aprovado"],
        "resumo": proj["resumo"],
        "fs": res["requisicao"]["fator_seguranca"],
        "came_pontuacao": proj["came"]["avaliacao"]["pontuacao"],
        "pivo_mm": erg["alinhamento_pivo"]["altura_pivo_mm"],
        "pega_mm": erg["pegada"]["diametro"]["diametro_recomendado_mm"],
        "pega_tipo": erg["pegada"]["orientacao"]["orientacao"],
        "peso_kg": proj["geometria"]["memorial"]["peso_total_estrutura_kg"],
        "estrutura": proj["estrutura"],
        "links": {
            "render": f"{base}/hero.svg",
            "viewer": f"{base}/montagem_3d.html",
            "pdf": f"{base}/dossie_{exercicio}.pdf" if tem_pdf else "",
            "scad": f"{base}/{exercicio}.scad",
            "memorial": f"{base}/{exercicio}_memorial.json",
        },
    }


def _pagina_academia() -> str:
    """Galeria da Academia Virtual + planta baixa em escala."""
    cat = gerar_catalogo_academia()
    res = cat["resumo"]
    secoes = []
    for bloco in cat["categorias"]:
        cards = []
        for e in bloco["equipamentos"]:
            if e["projeto_completo"]:
                selo = '<span class="tag ok">PROJETO COMPLETO</span>'
                acao = (f'<a class="proj" href="/?exercicio={e["exercicio_pipeline"]}">'
                        f'&#9881; Projetar esta maquina</a>')
            else:
                selo = '<span class="tag">ficha tecnica</span>'
                acao = '<span class="proj off">pipeline em expansao</span>'
            cards.append(f"""<div class="eq">
              <div class="eq-top"><b>#{e['rank']} {e['nome']}</b>{selo}</div>
              <p>{e['tipo']} · ref. {e['referencia']}</p>
              <p class="mus">{', '.join(e['musculos'])}</p>
              <p class="dim">{e['footprint_mm'][0]/1000:.2f} x {e['footprint_mm'][1]/1000:.2f} m
                 · h {e['altura_mm']/1000:.2f} m · carga {e['carga_max_kg']} kg</p>
              {acao}</div>""")
        secoes.append(f'<h2>{bloco["categoria"]} ({len(bloco["equipamentos"])})</h2>'
                      f'<div class="grade">{"".join(cards)}</div>')
    return f"""<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>DechenGym — Academia Virtual</title><style>
:root{{--bg:#0f1216;--panel:#171b21;--line:#262c34;--txt:#e8ebef;--mut:#9aa4b0;--acc:#e0a422;--ok:#22c55e}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--txt);font:14px/1.5 'Segoe UI',system-ui,sans-serif}}
header{{padding:16px 26px;border-bottom:1px solid var(--line);display:flex;gap:14px;align-items:baseline}}
header h1{{font-size:19px}}header h1 b{{color:var(--acc)}}
header a{{margin-left:auto;color:var(--acc);text-decoration:none;font-weight:600}}
main{{max-width:1220px;margin:0 auto;padding:24px}}
.resumo{{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:8px}}
.chip{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 16px}}
.chip b{{font-size:18px;display:block}}
.chip span{{color:var(--mut);font-size:11.5px}}
h2{{font-size:14px;margin:26px 0 12px;color:var(--acc);text-transform:uppercase;letter-spacing:.06em}}
.grade{{display:grid;grid-template-columns:repeat(auto-fill,minmax(265px,1fr));gap:12px}}
.eq{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}}
.eq-top{{display:flex;justify-content:space-between;gap:8px;align-items:start;margin-bottom:6px}}
.eq b{{font-size:13.5px}}
.eq p{{color:var(--mut);font-size:12px;margin:2px 0}}
.eq .mus{{color:#c8d0da}}
.tag{{font-size:9.5px;font-weight:700;border:1px solid var(--line);border-radius:999px;padding:3px 8px;color:var(--mut);white-space:nowrap}}
.tag.ok{{color:var(--ok);border-color:rgba(34,197,94,.5);background:rgba(34,197,94,.1)}}
.proj{{display:inline-block;margin-top:8px;background:var(--acc);color:#14161a;font-weight:700;font-size:12px;
  border-radius:8px;padding:7px 11px;text-decoration:none}}
.proj.off{{background:#232a33;color:var(--mut);font-weight:500}}
.planta{{background:#fff;border-radius:14px;padding:8px;margin-top:14px}}
.planta img{{width:100%;display:block}}
footer{{padding:14px 26px;border-top:1px solid var(--line);color:var(--mut);font-size:11.5px}}
</style></head><body>
<header><h1><b>Dechen</b>Gym · Academia Virtual</h1><a href="/treino" style="margin-left:auto">💪 Meu Treino</a><a href="/">&larr; Estudio de Projeto</a></header>
<main>
<div class="resumo">
  <div class="chip"><b>{res['total_equipamentos']}</b><span>equipamentos mais usados</span></div>
  <div class="chip"><b>{res['com_projeto_completo']}</b><span>com projeto completo DechenGym</span></div>
  <div class="chip"><b>{res['area_ocupada_m2']} m&sup2;</b><span>area ocupada (footprints)</span></div>
  <div class="chip"><b>{len(res['por_categoria'])}</b><span>zonas</span></div>
</div>
<h2>Planta baixa (escala real)</h2>
<div class="planta"><img src="/academia/planta.svg" alt="planta da academia"/></div>
{''.join(secoes)}
</main>
<footer>Base compilada de rankings do setor (Skelcore, WodGuru, Fitness Expo) e fichas de fabricantes topo de linha (Hammer Strength/Life Fitness, Technogym, Matrix). Dimensoes de referencia — confirme na ficha do fabricante.</footer>
</body></html>"""


_PAGINA_TREINO = """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>DechenGym — Meu Treino</title><style>
:root{--bg:#0f1216;--panel:#171b21;--line:#262c34;--txt:#e8ebef;--mut:#9aa4b0;--acc:#e0a422;--ok:#22c55e;--warn:#f59e0b;--err:#ef4444}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--txt);font:14px/1.5 'Segoe UI',system-ui,sans-serif}
header{padding:16px 26px;border-bottom:1px solid var(--line);display:flex;gap:14px;align-items:baseline}
header h1{font-size:19px}header h1 b{color:var(--acc)}
header a{margin-left:auto;color:var(--acc);text-decoration:none;font-weight:600}
main{max-width:1100px;margin:0 auto;padding:24px}
.chips{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:18px}
.chip{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:10px 16px;min-width:130px}
.chip b{font-size:18px;display:block}.chip span{color:var(--mut);font-size:11.5px}
.chip select{background:#0e1114;border:1px solid var(--line);border-radius:8px;color:var(--txt);padding:6px 8px;font-size:13px;margin-top:2px}
h2{font-size:13px;margin:22px 0 10px;color:var(--acc);text-transform:uppercase;letter-spacing:.07em}
.ciclo{display:flex;gap:10px;flex-wrap:wrap}
.pill{display:flex;align-items:center;gap:9px;background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:8px 16px 8px 9px}
.pill .lt{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;font-weight:800;background:#232a33;color:var(--mut)}
.pill.feito .lt{background:rgba(34,197,94,.18);color:var(--ok);border:1px solid rgba(34,197,94,.45)}
.pill small{color:var(--mut);display:block;font-size:11px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px}
.tr{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;position:relative}
.tr.rec{border-color:rgba(224,164,34,.65);box-shadow:0 0 0 1px rgba(224,164,34,.35)}
.tr.feito{opacity:.62}
.badge{position:absolute;top:-9px;right:14px;background:var(--acc);color:#14161a;font-size:10px;font-weight:800;border-radius:999px;padding:3px 10px;letter-spacing:.05em}
.tr-top{display:flex;gap:12px;align-items:center;margin-bottom:6px}
.tr-top .lt{width:44px;height:44px;border-radius:12px;display:grid;place-items:center;font-size:20px;font-weight:800;background:#232a33;color:var(--acc)}
.tr-top b{font-size:15px;display:block}
.tr-top small{color:var(--mut)}
.rec-l{list-style:none;margin:8px 0;font-size:12.5px}
.rec-l li{display:flex;justify-content:space-between;border-bottom:1px dashed var(--line);padding:3px 0;color:var(--mut)}
.rec-l .ok{color:var(--ok)}.rec-l .warn{color:var(--warn)}
.motivo{font-size:12px;color:var(--mut);font-style:italic;margin:6px 0}
.eqs{font-size:11.5px;color:#c8d0da;margin:6px 0 10px}
.eqs a{color:var(--acc);text-decoration:none}
button{background:var(--acc);border:0;border-radius:9px;color:#14161a;font-weight:700;font-size:13px;padding:10px 14px;cursor:pointer;width:100%}
.tr.feito button{background:#232a33;color:var(--mut);font-weight:500}
table{width:100%;border-collapse:collapse;font-size:12.5px;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}
td,th{padding:8px 12px;text-align:left;border-bottom:1px solid var(--line)}
th{color:var(--mut);font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:.05em}
.und{background:none;border:1px solid var(--line);color:var(--mut);width:auto;font-weight:500;font-size:11.5px;padding:6px 10px;margin-top:8px}
#msg{position:fixed;bottom:18px;left:50%;transform:translateX(-50%);background:var(--ok);color:#08110b;font-weight:700;border-radius:10px;padding:10px 18px;display:none}
footer{padding:12px 26px;border-top:1px solid var(--line);color:var(--mut);font-size:11.5px}
</style></head><body>
<header><h1><b>Dechen</b>Gym · Meu Treino</h1><a href="/academia">🏟 Academia Virtual</a><a href="/">⚙ Estúdio de Projeto</a></header>
<main id="app"><p style="color:var(--mut)">Carregando…</p></main>
<div id="msg"></div>
<footer>Sugestões: pendência no ciclo + recuperação por grupo muscular (inclui trabalho indireto das sinergias). Registro em output/treino/historico.json.</footer>
<script>
const $=s=>document.querySelector(s);
async function api(rota,corpo){const r=await fetch(rota,corpo?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(corpo)}:undefined);const d=await r.json();if(!r.ok)throw new Error(d.erro||'falha');return d}
function aviso(t){const m=$('#msg');m.textContent=t;m.style.display='block';setTimeout(()=>m.style.display='none',2600)}
function fmtRec(g){if(g.dias_descanso===null)return `<li><span>${g.grupo}</span><span class="ok">descansado</span></li>`;
 const cls=g.dias_descanso>=2?'ok':'warn';const ind=g.indireto?' (indireto)':'';
 return `<li><span>${g.grupo}${ind}</span><span class="${cls}">${g.dias_descanso}d de descanso</span></li>`}
function render(v){
 const pills=Object.keys(v.divisoes_disponiveis).map(k=>`<option value="${k}"${k===v.divisao?' selected':''}>${v.divisoes_disponiveis[k]}</option>`).join('');
 const feitos=Object.fromEntries(v.ciclo.feitos.map(f=>[f.letra,f.data]));
 const todas=[...v.ciclo.feitos.map(f=>f.letra),...v.ciclo.pendentes];
 todas.sort();
 const ciclo=todas.map(l=>{const ok=l in feitos;return `<div class="pill${ok?' feito':''}"><div class="lt">${ok?'✓':l}</div><div><b>${l}</b><small>${ok?feitos[l]:'pendente'}</small></div></div>`}).join('');
 const cards=v.sugestoes.map(s=>{
  const eqs=s.equipamentos.map(e=>e.projeto_completo?`<a href="/?exercicio=${e.exercicio_pipeline}">${e.nome}</a>`:e.nome).join(' · ');
  return `<div class="tr${s.recomendado?' rec':''}${s.pendente_no_ciclo?'':' feito'}">
   ${s.recomendado?'<div class="badge">RECOMENDADO HOJE</div>':''}
   <div class="tr-top"><div class="lt">${s.letra}</div><div><b>${s.nome}</b><small>${s.ultimo_treino?'último: '+s.ultimo_treino:'nunca treinado'}</small></div></div>
   <ul class="rec-l">${s.recuperacao.map(fmtRec).join('')}</ul>
   <p class="motivo">${s.motivo}</p>
   <p class="eqs">🏋 ${eqs}</p>
   <button onclick="treinar('${s.letra}','${s.nome.replace(/'/g,'')}')">${s.pendente_no_ciclo?'✓ Treinar este hoje':'↻ Repetir mesmo assim'}</button>
  </div>`}).join('');
 const hist=v.historico_recente.map(h=>`<tr><td>${h.data}</td><td><b>${h.letra}</b> — ${h.nome}</td><td>${h.dias_atras===0?'hoje':h.dias_atras+'d atrás'}</td></tr>`).join('')||'<tr><td colspan="3" style="color:var(--mut)">Nenhum treino registrado ainda — escolha um card acima.</td></tr>';
 $('#app').innerHTML=`
 <div class="chips">
  <div class="chip"><b>${v.ciclo.progresso}</b><span>ciclo atual</span></div>
  <div class="chip"><b>${v.treinos_ultimos_7_dias}</b><span>treinos nos últimos 7 dias</span></div>
  <div class="chip"><b>${v.hoje}</b><span>hoje</span></div>
  <div class="chip"><span>divisão</span><br/><select id="div" onchange="mudarDiv(this.value)">${pills}</select></div>
 </div>
 <h2>Ciclo atual — ${v.divisao_nome}</h2><div class="ciclo">${ciclo}</div>
 <h2>Próximos treinos (escolha ou troque)</h2><div class="cards">${cards}</div>
 <h2>Histórico recente</h2><table><tr><th>Data</th><th>Treino</th><th></th></tr>${hist}</table>
 <button class="und" onclick="desfazer()">↶ desfazer último registro</button>`;
}
async function carregar(){render(await api('/api/treino'))}
async function treinar(l,n){render(await api('/api/treino/registrar',{letra:l}));aviso('Treino '+l+' — '+n+' registrado 💪')}
async function mudarDiv(d){render(await api('/api/treino/divisao',{divisao:d}));aviso('Divisão alterada — histórico preservado')}
async function desfazer(){render(await api('/api/treino/desfazer',{}));aviso('Último registro removido')}
carregar();
</script></body></html>"""


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # silencioso
        pass

    def _json(self, dados: dict, status: int = 200):
        corpo = json.dumps(dados, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        rota = urlparse(self.path).path
        if rota in ("/", "/index.html"):
            corpo = _pagina().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        if rota == "/academia":
            corpo = _pagina_academia().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        if rota == "/academia/planta.svg":
            corpo = gerar_planta_academia().encode()
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        if rota == "/treino":
            corpo = _PAGINA_TREINO.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        if rota == "/api/treino":
            self._json(visao_geral_treino())
            return
        if rota == "/api/academia":
            self._json(gerar_catalogo_academia())
            return
        if rota.startswith("/output/"):
            alvo = (RAIZ / unquote(rota).lstrip("/")).resolve()
            if not str(alvo).startswith(str((RAIZ / "output").resolve())) or not alvo.is_file():
                self._json({"erro": "arquivo nao encontrado"}, 404)
                return
            tipos = {".svg": "image/svg+xml", ".html": "text/html; charset=utf-8",
                     ".pdf": "application/pdf", ".json": "application/json",
                     ".scad": "text/plain", ".png": "image/png"}
            corpo = alvo.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", tipos.get(alvo.suffix, "application/octet-stream"))
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        self._json({"erro": "rota desconhecida"}, 404)

    def do_POST(self):
        rota = urlparse(self.path).path
        try:
            tam = int(self.headers.get("Content-Length", 0))
            corpo = json.loads(self.rfile.read(tam) or b"{}")
        except Exception:
            self._json({"erro": "JSON invalido"}, 400)
            return
        try:
            if rota == "/api/interpretar":
                req = AdaptadorRegras().interpretar(corpo.get("briefing", ""))
                self._json(req.to_dict())
            elif rota == "/api/projetar":
                self._json(_projetar(corpo))
            elif rota == "/api/treino/registrar":
                self._json(registrar_treino(corpo["letra"], corpo.get("data")))
            elif rota == "/api/treino/divisao":
                self._json(definir_divisao(corpo["divisao"]))
            elif rota == "/api/treino/desfazer":
                self._json(desfazer_ultimo())
            else:
                self._json({"erro": "rota desconhecida"}, 404)
        except Exception as exc:  # erro de domínio vira mensagem legível
            self._json({"erro": str(exc)}, 500)


def main(porta: int = 8765, abrir_navegador: bool = True) -> None:
    """Sobe o servidor local da interface (Ctrl+C para encerrar)."""
    SAIDA.mkdir(parents=True, exist_ok=True)
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), _Handler)
    url = f"http://127.0.0.1:{porta}"
    print(f"DechenGym Estudio de Projeto: {url}  (Ctrl+C encerra)")
    if abrir_navegador:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
