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

from dechengym.data.exercicios_db import CATALOGO_EXERCICIOS
from dechengym.data.metalon_db import perfis_disponiveis
from dechengym.orquestrador import AdaptadorRegras, orquestrar

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
<header><h1><b>Dechen</b>Gym · Estúdio de Projeto</h1><span>briefing → ergonomia → came → estrutura → 3D → dossiê</span></header>
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
        f'<option{" selected" if p == "60x60" else ""}>{p}</option>' for p in perfis_disponiveis()
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
