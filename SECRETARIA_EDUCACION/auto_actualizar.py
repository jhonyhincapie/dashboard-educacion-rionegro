#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revisa si hay un presupuesto nuevo en entradas/ o si el archivo compartido
'DETALLE FINANCIERO POR CONTRATO' (sincronizado via OneDrive) cambio, y si
alguno de los dos paso, regenera el informe y el dashboard publico, y publica
los cambios en GitHub (lo que dispara el deploy automatico en Netlify).

Disenado para correr sin supervision (Tarea programada de Windows).
No hace nada si nada cambio desde la ultima corrida.
"""
import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime

import extractor_contratos as extc

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(BASE)
ENTRADAS = os.path.join(BASE, "entradas")
ESTADO = os.path.join(BASE, ".ultimo_procesado.json")
LOG = os.path.join(BASE, "auto_actualizar.log")


def log(msg):
    linea = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(linea)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def corte_de(nombre):
    m = re.search(r"(\d{2})_(\d{2})_(\d{4})", nombre)
    return (m.group(3), m.group(2), m.group(1)) if m else None


def excel_presupuesto_mas_reciente():
    archivos = [p for p in glob.glob(os.path.join(ENTRADAS, "Presupuesto de egreso a *.xls*"))
                if not os.path.basename(p).startswith("~$")]
    con_fecha = [(corte_de(os.path.basename(p)), p) for p in archivos]
    con_fecha = [x for x in con_fecha if x[0]]
    if not con_fecha:
        return None
    con_fecha.sort(key=lambda x: x[0])
    return con_fecha[-1][1]


def cargar_estado():
    if not os.path.exists(ESTADO):
        # Compatibilidad con el formato viejo (texto plano, solo presupuesto)
        viejo = os.path.join(BASE, ".ultimo_procesado.txt")
        if os.path.exists(viejo):
            with open(viejo, encoding="utf-8") as f:
                return {"presupuesto": f.read().strip(), "detalle_financiero_mtime": None}
        return {"presupuesto": None, "detalle_financiero_mtime": None}
    with open(ESTADO, encoding="utf-8") as f:
        return json.load(f)


def guardar_estado(estado):
    with open(ESTADO, "w", encoding="utf-8") as f:
        json.dump(estado, f, ensure_ascii=False, indent=2)


def correr(cmd, cwd):
    log("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.stdout.strip():
        log(r.stdout.strip())
    if r.returncode != 0:
        log("  ERROR (codigo %s): %s" % (r.returncode, r.stderr.strip()))
        raise SystemExit(r.returncode)


def main():
    estado = cargar_estado()

    excel = excel_presupuesto_mas_reciente()
    presupuesto_nuevo = excel and os.path.basename(excel) != estado.get("presupuesto")

    ruta_detalle = extc.ruta_detalle_financiero()
    mtime_detalle = os.path.getmtime(ruta_detalle) if ruta_detalle else None
    detalle_cambio = mtime_detalle is not None and mtime_detalle != estado.get("detalle_financiero_mtime")

    if not presupuesto_nuevo and not detalle_cambio:
        log("Sin cambios: presupuesto y detalle financiero iguales a la ultima corrida.")
        return

    motivos = []
    if presupuesto_nuevo:
        motivos.append(f"presupuesto nuevo ({os.path.basename(excel)})")
    if detalle_cambio:
        motivos.append(f"detalle financiero modificado ({ruta_detalle})")
    log("Cambio detectado: " + "; ".join(motivos))

    py = sys.executable

    if presupuesto_nuevo:
        log("1/4 Generando informe (extractor_educacion.py)...")
        correr([py, os.path.join(BASE, "extractor_educacion.py"), excel], cwd=BASE)
    else:
        log("1/4 Presupuesto sin cambios, se omite regenerar el informe base.")

    log("2/4 Regenerando dashboard publico (publicar_dashboard.py)...")
    correr([py, os.path.join(BASE, "publicar_dashboard.py")], cwd=BASE)

    log("3/4 Publicando cambios en GitHub...")
    correr(["git", "add", "publicar", "SECRETARIA_EDUCACION/informes",
             "SECRETARIA_EDUCACION/entradas"], cwd=RAIZ)
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=RAIZ)
    if diff.returncode == 0:
        log("  No hay cambios que publicar (el contenido generado es identico).")
    else:
        msg = "Actualizar dashboard automaticamente: " + "; ".join(motivos)
        correr(["git", "commit", "-m", msg], cwd=RAIZ)
        correr(["git", "push", "origin", "main"], cwd=RAIZ)
        log("  Cambios publicados. Netlify desplegara automaticamente.")

    guardar_estado({
        "presupuesto": os.path.basename(excel) if excel else estado.get("presupuesto"),
        "detalle_financiero_mtime": mtime_detalle if mtime_detalle is not None
        else estado.get("detalle_financiero_mtime"),
    })
    log("4/4 Listo.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FALLO: {e}")
        raise
