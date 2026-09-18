#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, glob
from datetime import datetime

def obtener_json():
    base = os.path.dirname(os.path.abspath(__file__))
    archivos = glob.glob(os.path.join(base, "informes", "seguimiento_*.json"))
    if not archivos:
        return None
    archivo = max(archivos, key=os.path.getmtime)
    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)

datos = obtener_json()
if not datos:
    exit(1)

totales = datos.get("totales", {})
brechas = datos.get("brechas", {})
componentes = datos.get("componentes", [])
corte = datos.get("corte", "")

# Participación
participacion = [(c["nombre"][:25], c["totales"]["definitiva"] / totales.get("definitiva", 1) * 100) for c in componentes[:6]]

html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Informe Ejecutivo Presupuestal</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: Arial, sans-serif; background: white; padding: 40px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 3px solid #003d7a; }}
        .title {{ text-align: center; flex: 1; }}
        .title h1 {{ color: #003d7a; font-size: 28px; margin-bottom: 5px; }}
        .kpi-cards {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 30px; }}
        .kpi-card {{ background: white; border-left: 5px solid #003d7a; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .kpi-label {{ font-size: 11px; color: #666; text-transform: uppercase; margin-bottom: 5px; }}
        .kpi-value {{ font-size: 20px; font-weight: bold; color: #003d7a; }}
        .kpi-pct {{ font-size: 14px; color: #999; margin-top: 5px; }}
        .content {{ display: grid; grid-template-columns: 2fr 1fr; gap: 20px; margin-bottom: 30px; }}
        .section {{ background: #f9f9f9; padding: 20px; border-radius: 4px; }}
        .section h2 {{ color: #003d7a; font-size: 16px; margin-bottom: 15px; border-bottom: 2px solid #e0e0e0; padding-bottom: 10px; }}
        .brechas {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }}
        .brecha-card {{ background: white; padding: 15px; border-radius: 4px; border-top: 4px solid #d32f2f; }}
        .brecha-label {{ font-size: 12px; font-weight: bold; color: #333; }}
        .brecha-pct {{ font-size: 20px; font-weight: bold; color: #d32f2f; margin: 10px 0; }}
        .barra {{ display: flex; align-items: center; margin-bottom: 10px; font-size: 12px; }}
        .barra-label {{ width: 150px; }}
        .barra-contenedor {{ flex: 1; background: #e0e0e0; height: 20px; margin: 0 10px; }}
        .barra-fill {{ height: 100%; background: linear-gradient(90deg, #003d7a, #4a90e2); }}
        .tabla {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
        .tabla th {{ background: #003d7a; color: white; padding: 10px; text-align: left; font-size: 12px; }}
        .tabla td {{ padding: 8px 10px; border-bottom: 1px solid #e0e0e0; font-size: 11px; }}
        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; color: #999; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>Alcaldia Rionegro</div>
            <div class="title">
                <h1>Informe Ejecucion Presupuestal</h1>
                <p>Secretaria Educacion | Corte: {corte}</p>
            </div>
            <div>Generado: {datetime.now().strftime('%d/%m/%Y')}</div>
        </div>

        <div class="kpi-cards">
            <div class="kpi-card">
                <div class="kpi-label">Presupuesto Definitivo</div>
                <div class="kpi-value">${totales.get('definitiva', 0)/1e9:.2f}B</div>
                <div class="kpi-pct">100%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Reservado CDP</div>
                <div class="kpi-value">${totales.get('reservado', 0)/1e9:.2f}B</div>
                <div class="kpi-pct">{(totales.get('reservado', 0) / totales.get('definitiva', 1) * 100):.1f}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Comprometido RP</div>
                <div class="kpi-value">${totales.get('comprometido', 0)/1e9:.2f}B</div>
                <div class="kpi-pct">{(totales.get('comprometido', 0) / totales.get('definitiva', 1) * 100):.1f}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Obligado OPS</div>
                <div class="kpi-value">${totales.get('obligado', 0)/1e9:.2f}B</div>
                <div class="kpi-pct">{(totales.get('obligado', 0) / totales.get('definitiva', 1) * 100):.1f}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Pagado</div>
                <div class="kpi-value">${totales.get('pagado', 0)/1e9:.2f}B</div>
                <div class="kpi-pct">{(totales.get('pagado', 0) / totales.get('definitiva', 1) * 100):.1f}%</div>
            </div>
        </div>

        <div class="content">
            <div>
                <div class="section">
                    <h2>Brechas de Ejecucion</h2>
                    <div class="brechas">
                        <div class="brecha-card">
                            <div class="brecha-label">Sin Reservar</div>
                            <div class="brecha-pct">{brechas.get('sin_reservar', {}).get('pct', 0):.1f}%</div>
                            <div class="brecha-label">${brechas.get('sin_reservar', {}).get('valor', 0)/1e9:.2f}B</div>
                        </div>
                        <div class="brecha-card">
                            <div class="brecha-label">Sin Comprometer</div>
                            <div class="brecha-pct">{brechas.get('sin_comprometer', {}).get('pct', 0):.1f}%</div>
                            <div class="brecha-label">${brechas.get('sin_comprometer', {}).get('valor', 0)/1e9:.2f}B</div>
                        </div>
                        <div class="brecha-card">
                            <div class="brecha-label">Sin Obligar</div>
                            <div class="brecha-pct">{brechas.get('sin_obligar', {}).get('pct', 0):.1f}%</div>
                            <div class="brecha-label">${brechas.get('sin_obligar', {}).get('valor', 0)/1e9:.2f}B</div>
                        </div>
                    </div>
                </div>

                <div class="section" style="margin-top: 20px;">
                    <h2>Participacion por Componente</h2>
                    {"".join([f'<div class="barra"><div class="barra-label">{n}</div><div class="barra-contenedor"><div class="barra-fill" style="width:{min(p/50*100,100)}%"></div></div><div>{p:.1f}%</div></div>' for n, p in participacion])}
                </div>
            </div>

            <div>
                <div class="section">
                    <h2>Resumen Ejecutivo</h2>
                    <div style="font-size: 13px; line-height: 1.8;">
                        <p><strong>Ejecucion General:</strong><br>
                        El {(totales.get('comprometido', 0) / totales.get('definitiva', 1) * 100):.1f}% del presupuesto ha sido comprometido.</p>
                        <p style="margin-top: 10px;"><strong>Disponibilidad:</strong><br>
                        Existe ${brechas.get('sin_reservar', {}).get('valor', 0)/1e9:.2f}B sin reservar.</p>
                        <p style="margin-top: 10px;"><strong>Desembolsos:</strong><br>
                        Se han pagado ${totales.get('pagado', 0)/1e9:.2f}B ({(totales.get('pagado', 0) / totales.get('definitiva', 1) * 100):.1f}%).</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Seguimiento por Componente</h2>
            <table class="tabla">
                <thead><tr><th>Componente</th><th>Definitivo</th><th>Reservado</th><th>Comprometido</th><th>Obligado</th><th>Pagado</th><th>% Comp</th></tr></thead>
                <tbody>
                {"".join([f"<tr><td><b>{c['nombre']}</b></td><td>${c['totales']['definitiva']/1e9:.2f}B</td><td>${c['totales']['reservado']/1e9:.2f}B</td><td>${c['totales']['comprometido']/1e9:.2f}B</td><td>${c['totales']['obligado']/1e9:.2f}B</td><td>${c['totales']['pagado']/1e9:.2f}B</td><td>{c.get('pct_comprometido', 0):.1f}%</td></tr>" for c in componentes])}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>Secretaria Educacion - Alcaldia Rionegro</p>
            <p>Sistema Automatico de Presupuesto</p>
        </div>
    </div>
</body>
</html>"""

base = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(base, "informes", f"Informe_Ejecutivo_{corte}.html")
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("[OK] Informe generado:")
print(out)
