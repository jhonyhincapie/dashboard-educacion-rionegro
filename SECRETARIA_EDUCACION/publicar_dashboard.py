#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera la carpeta estatica 'publicar/' (index.html + datos.json + assets) desde el Excel mas reciente.
Uso: python publicar_dashboard.py [ruta_excel]"""
import json, os, shutil, sys
import extractor_contratos as extc
import extractor_dashboard as ext

# Los nombres de contratistas NO se publican en internet salvo que se cambie esto a False.
OCULTAR_CONTRATISTAS_EN_PUBLICO = False

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(RAIZ, "publicar")

d = ext.extraer(sys.argv[1] if len(sys.argv) > 1 else None)
for c in d["componentes"]:
    for s in c["subgrupos"]:
        for r in s["rubros"]:
            r.pop("responsable", None)   # no publicar nombres de personas
os.makedirs(os.path.join(OUT, "assets"), exist_ok=True)
shutil.copyfile(os.path.join(RAIZ, "dashboard_ejecutivo.html"), os.path.join(OUT, "index.html"))
shutil.copyfile(os.path.join(RAIZ, "assets", "logo_horizontal.webp"), os.path.join(OUT, "assets", "logo_horizontal.webp"))
with open(os.path.join(OUT, "datos.json"), "w", encoding="utf-8") as f:
    json.dump(d, f, ensure_ascii=False)
with open(os.path.join(OUT, "_headers"), "w") as f:
    f.write("/*\n  Cache-Control: no-store\n  X-Robots-Tag: noindex, nofollow\n")
try:
    c = extc.extraer_contratos(ocultar_contratista=OCULTAR_CONTRATISTAS_EN_PUBLICO)
    with open(os.path.join(OUT, "contratos.json"), "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False)
    print("contratos:", len(c["contratos"]), "| cruce:", c["cruce"])
except Exception as e:
    print("AVISO: no se genero contratos.json:", e)
print("OK", OUT, "| corte:", d["corte"], "| validacion:", d["validacion"]["ok"])
