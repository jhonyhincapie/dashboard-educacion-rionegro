#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capa de DATOS de contratos: lee la hoja de vigencia del archivo 'Seguimiento CDP-CRP',
la amarra a rubros del presupuesto por NUMERO DE CDP (verificado con la cola del codigo
presupuestal) y agrega la subsecretaria desde areas_educacion.xlsx.
Nunca adivina: lo que no se puede resolver queda marcado, no asignado."""
import glob
import os
import re
import shutil
import sys
import tempfile
from datetime import datetime

import openpyxl

import extractor_dashboard as ext
import extractor_educacion as EE

BASE = os.path.dirname(os.path.abspath(__file__))
ENTRADAS = os.path.join(BASE, "entradas")
CDPCRP_DIR = os.path.join(BASE, "entradas_contratos")
RUTA_TXT = os.path.join(BASE, "ruta_cdpcrp.txt")
AREAS_PATH = os.path.join(BASE, "areas_educacion.xlsx")

AREAS = ["Subsecretaría Administrativa y Financiera",
         "Subsecretaría de Planeación y Calidad Educativa",
         "Subsecretaría de Educación Inicial y Cobertura Educativa"]

DETALLE_FINANCIERO_NOMBRE = "DETALLE FINANCIERO POR CONTRATO -V3 - ER.xlsx"
DETALLE_FINANCIERO = os.path.join(ENTRADAS, DETALLE_FINANCIERO_NOMBRE)
# Carpeta de OneDrive sincronizada via "Agregar acceso directo" (fuente en linea,
# editada por varias personas). Si existe y tiene el archivo, tiene prioridad
# sobre la copia estatica en entradas/.
ONEDRIVE_ROOT = os.environ.get("OneDrive", os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(BASE))))))
DETALLE_FINANCIERO_ONEDRIVE = os.path.join(
    ONEDRIVE_ROOT, "NO BORRAR - CONTROL FINANCIERO", DETALLE_FINANCIERO_NOMBRE)


def ruta_detalle_financiero():
    """Prioriza la carpeta de OneDrive sincronizada (fuente en linea, siempre
    actualizada); si no esta disponible, cae a la copia estatica en entradas/."""
    if os.path.exists(DETALLE_FINANCIERO_ONEDRIVE):
        return DETALLE_FINANCIERO_ONEDRIVE
    if os.path.exists(DETALLE_FINANCIERO):
        return DETALLE_FINANCIERO
    return None

COL_ACTA_INI, COL_ACTA_FIN = 9, 25
_cache = {}


def _abrir(path, data_only=True):
    try:
        return openpyxl.load_workbook(path, data_only=data_only)
    except PermissionError:  # abierto en Excel / bloqueado por OneDrive: leer copia
        tmp = os.path.join(tempfile.gettempdir(), "_cp_" + os.path.basename(path))
        shutil.copyfile(path, tmp)
        return openpyxl.load_workbook(tmp, data_only=data_only)


def ruta_cdpcrp():
    """1) variable CDPCRP_PATH  2) primera linea de ruta_cdpcrp.txt  3) carpeta entradas_contratos/"""
    p = os.environ.get("CDPCRP_PATH")
    if not p and os.path.exists(RUTA_TXT):
        with open(RUTA_TXT, encoding="utf-8") as f:
            p = f.readline().strip().strip('"')
    if p and os.path.exists(p):
        return p
    archivos = [a for a in glob.glob(os.path.join(CDPCRP_DIR, "Seguimiento CDP-CRP*.xlsx"))
                if not os.path.basename(a).startswith("~$")]
    return max(archivos, key=os.path.getmtime) if archivos else None


def _num(v):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        s = v.strip().replace(",", "")
        try:
            return float(s)
        except ValueError:
            return 0.0
    return 0.0


def _txt(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


# ------------------------------------------------------------------ AREAS
def _normalizar_nro_contrato(nro):
    """Normaliza número de contrato para comparación (espacios, puntos, etc)."""
    if not nro:
        return ""
    return _txt(nro).strip()


def _leer_subsecretarias_detalle():
    """Lee mapeo desde DETALLE FINANCIERO POR CONTRATO por código presupuestal.
    Columnas: Col2=Subsecretaria, Col3=Código presupuestal, Col4=Objeto, Col5=Contratista. Hoja 2026."""
    mapa_subsec = {}
    mapa_objeto = {}
    mapa_contratista = {}
    ruta = ruta_detalle_financiero()
    if not ruta:
        return {"subsec": mapa_subsec, "objeto": mapa_objeto, "contratista": mapa_contratista}
    try:
        wb = _abrir(ruta)
        if "2026" not in wb.sheetnames:
            return {"subsec": mapa_subsec, "objeto": mapa_objeto, "contratista": mapa_contratista}
        ws = wb["2026"]
        for row_idx in range(3, ws.max_row + 1):
            subsec = _txt(ws.cell(row=row_idx, column=2).value)
            # La columna 3 contiene código presupuestal (cons_ppt) en el DETALLE FINANCIERO
            cod_presupuestal = _txt(ws.cell(row=row_idx, column=3).value)
            objeto = _txt(ws.cell(row=row_idx, column=4).value)
            contratista = _txt(ws.cell(row=row_idx, column=5).value)
            if cod_presupuestal:
                # Normalizar el código presupuestal para que coincida con cons_ppt del CDP-CRP
                cod_normalizado = cod_presupuestal.replace("-", ".") if "-" in cod_presupuestal else cod_presupuestal
                if subsec:
                    mapa_subsec[cod_normalizado] = subsec
                if objeto:
                    mapa_objeto[cod_normalizado] = objeto
                if contratista:
                    mapa_contratista[cod_normalizado] = contratista
        if mapa_subsec or mapa_objeto or mapa_contratista:
            print(f"debug: mapeo detalle: {len(mapa_subsec)} subsecretarías, {len(mapa_objeto)} objetos, {len(mapa_contratista)} contratistas", file=sys.stderr)
    except Exception as e:
        print(f"debug: no se pudo leer detalle: {e}", file=sys.stderr)
    return {"subsec": mapa_subsec, "objeto": mapa_objeto, "contratista": mapa_contratista}


def leer_areas():
    """MAPA_RUBRO: cons_ppt -> subsecretaria. MAPA_CONTRATO: nro_contrato -> (subsecretaria, objeto)."""
    out = {"rubro": {}, "contrato": {}, "objeto": {}, "existe": os.path.exists(AREAS_PATH), "areas": list(AREAS)}
    if not out["existe"]:
        return out
    wb = _abrir(AREAS_PATH)
    if "LISTA_AREAS" in wb.sheetnames:
        lst = [str(r[0]).strip() for r in wb["LISTA_AREAS"].iter_rows(min_row=2, values_only=True) if r[0]]
        if lst:
            out["areas"] = lst
    if "MAPA_RUBRO" in wb.sheetnames:
        for r in wb["MAPA_RUBRO"].iter_rows(min_row=2, values_only=True):
            if r[0] and len(r) > 4 and r[4]:
                out["rubro"][_txt(r[0])] = str(r[4]).strip()
    if "MAPA_CONTRATO" in wb.sheetnames:
        for r in wb["MAPA_CONTRATO"].iter_rows(min_row=2, values_only=True):
            if r[0]:
                k = _txt(r[0])
                if len(r) > 1 and r[1]:
                    out["contrato"][k] = str(r[1]).strip()
                if len(r) > 2 and r[2]:
                    out["objeto"][k] = str(r[2]).strip()
    return out


def asegurar_areas(rubros, contratos):
    """Crea areas_educacion.xlsx si no existe y agrega (sin tocar lo ya diligenciado)
    los rubros / contratos nuevos. rubros: lista de dicts; contratos: lista de nro."""
    from openpyxl.styles import Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    if os.path.exists(AREAS_PATH):
        cambio = False
        try:
            wb = openpyxl.load_workbook(AREAS_PATH)
        except PermissionError:
            return
    else:
        cambio = True
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "LISTA_AREAS"
        ws.append(["subsecretaria"])
        for a in AREAS:
            ws.append([a])
        ws["C1"] = "Una por fila. Agregue o cambie nombres aqui; el resto del archivo usa esta lista."
        wr = wb.create_sheet("MAPA_RUBRO")
        wr.append(["cons_ppt", "rubro", "componente", "con_contratos", "subsecretaria"])
        wc = wb.create_sheet("MAPA_CONTRATO")
        wc.append(["nro_contrato", "subsecretaria (opcional: manda sobre el rubro)", "objeto del contrato"])
        wa = wb.create_sheet("AYUDA")
        for fila in [["hoja", "que hacer"],
                     ["MAPA_RUBRO", "Elija en la columna subsecretaria a que area pertenece cada rubro. Los que tienen contratos aparecen primero. Un contrato toma el area de su rubro."],
                     ["MAPA_CONTRATO", "Solo si un contrato debe ir a un area distinta a la de su rubro, o para escribir el objeto que no viene en el archivo CDP-CRP."],
                     ["LISTA_AREAS", "Nombres de las subsecretarias. La lista desplegable de MAPA_RUBRO sale de aqui."],
                     ["Dashboard", "Lo que quede vacio se muestra como 'Sin asignar'. Nada se asigna automaticamente."]]:
            wa.append(fila)
    for ws in wb.worksheets:
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = PatternFill("solid", fgColor="144E76")
    wr, wc = wb["MAPA_RUBRO"], wb["MAPA_CONTRATO"]
    ya = {_txt(r[0].value) for r in wr.iter_rows(min_row=2) if r[0].value is not None}
    conctos = {r["cons_ppt"] for r in rubros if r.get("con_contratos")}
    nuevos = sorted([r for r in rubros if r["cons_ppt"] not in ya], key=lambda r: (not r.get("con_contratos"), r["componente"], r["nombre"] or ""))
    for r in nuevos:
        cambio = True
        wr.append([r["cons_ppt"], r["nombre"], r["componente"], "SI" if r.get("con_contratos") else "", None])
    for row in wr.iter_rows(min_row=2):  # actualiza la marca 'con_contratos' de los existentes
        marca = "SI" if _txt(row[0].value) in conctos else ""
        if (row[3].value or "") != marca:
            cambio = True
            row[3].value = marca
    yac = {_txt(r[0].value) for r in wc.iter_rows(min_row=2) if r[0].value}
    for n in contratos:
        if n not in yac:
            cambio = True
            wc.append([n, None, None])
    if not cambio:
        return
    wr.column_dimensions["B"].width, wr.column_dimensions["C"].width, wr.column_dimensions["E"].width = 55, 34, 52
    wc.column_dimensions["A"].width, wc.column_dimensions["B"].width, wc.column_dimensions["C"].width = 30, 52, 60
    wb["LISTA_AREAS"].column_dimensions["A"].width = 55
    n_areas = max(2, wb["LISTA_AREAS"].max_row)
    for hoja, col in (("MAPA_RUBRO", "E"), ("MAPA_CONTRATO", "B")):
        w = wb[hoja]
        w.data_validations.dataValidation = []
        dv = DataValidation(type="list", formula1=f"=LISTA_AREAS!$A$2:$A${n_areas}", allow_blank=True)
        w.add_data_validation(dv)
        dv.add(f"{col}2:{col}400")
    wb.save(AREAS_PATH)


# ------------------------------------------------------------------ CRUCE CON HACIENDA
def _hacienda_para(archivo_informe):
    m = re.search(r"(\d{2}_\d{2}_\d{4})", archivo_informe or "")
    if not m:
        return None
    p = os.path.join(ENTRADAS, f"Presupuesto de egreso a {m.group(1)}.xls")
    return p if os.path.exists(p) else None


def _mapa_cdp(path):
    k = ("cdp", path, os.path.getmtime(path))
    if k not in _cache:
        _cache.clear()
        _cache[k] = EE._construir_mapa_cdp_hacienda(path)
    return _cache[k]


def _mapa_cdps_hacienda(path):
    """Construye un mapa inverso de la columna 'cdps' de Hacienda para búsquedas directas.
    Retorna: cdp_numero -> [(cons_ppt, tail), ...] de rubros donde ese CDP aparece en 'cdps'."""
    try:
        import xlrd
    except ImportError:
        import openpyxl as xlrd
    k = ("cdps", path, os.path.getmtime(path))
    if k in _cache:
        return _cache[k]
    mapa = {}
    try:
        wb = xlrd.open_workbook(path)
        sh = wb.sheet_by_index(0)
        H = [str(sh.cell_value(0, c)).strip() for c in range(sh.ncols)]
        if "cdps" not in H:
            _cache[k] = mapa
            return mapa
        C = {h: H.index(h) for h in set(H) if h}
        for r in range(1, sh.nrows):
            if str(sh.cell_value(r, C.get("final", -1))) != "S":
                continue
            cons = sh.cell_value(r, C.get("cons_ppt"))
            cons_str = str(int(cons)) if isinstance(cons, float) else str(cons).strip()
            full = (str(sh.cell_value(r, C.get("codigo_padre", -1)) or "") +
                    str(sh.cell_value(r, C.get("codigo", -1)) or "")).strip()
            tail = EE._codigo_tail(full)
            cdps_str = str(sh.cell_value(r, C.get("cdps", -1)) or "")
            # extrae todos los números de la columna cdps
            for n in re.findall(r"\d+", cdps_str):
                mapa.setdefault(n, []).append((cons_str, tail))
    except Exception as e:
        print(f"aviso: no se pudo leer cdps de Hacienda: {e}", file=sys.stderr)
    _cache[k] = mapa
    return mapa


def _resolver(cdp, codigo, mapa, rubros_edu, por_cola):
    """-> (resolucion, cons_ppt, confianza, metodo)
    ok/alta: CDP y cola del codigo presupuestal coinciden con el mismo rubro de Hacienda.
    ok/media: CDP unico en Hacienda y la linea no trae codigo para comparar.
    ok_cdps: CDP verificado en la columna 'cdps' de Hacienda pero sin codigo coincidente.
    ok_codigo: el CDP no se pudo verificar en Hacienda, pero la cola del codigo
    presupuestal de la linea apunta a un unico rubro de Educacion.
    verificar: el numero de CDP existe en Hacienda pero su rubro NO coincide con el codigo de la linea
    (el numero de CDP se repite entre vigencias/rubros: no se asigna).
    cons_sugerido: rubro de Educacion cuya cola de codigo coincide de forma unica (solo sugerencia)."""
    tail = EE._codigo_tail(codigo) if codigo else None
    sug = por_cola.get(tail) if tail else None
    if not cdp:
        return ("ok_codigo", sug, "codigo", None) if sug else ("sin_cdp", None, "", None)
    if cdp.startswith("-") and len(cdp) > 4:
        return "vigencia_futura", None, "", sug
    num = cdp
    try:
        num = str(int(float(cdp)))
    except ValueError:
        pass
    cand = mapa.get(num, [])
    if not cand:
        return ("ok_codigo", sug, "codigo", None) if sug else ("cdp_no_hallado", None, "", None)
    cons_unicos = {c for c, t in cand}
    con_tail = {c for c, t in cand if tail and t == tail}
    def pertenece(c):
        return "ok" if c in rubros_edu else "otra_secretaria"
    if len(con_tail) == 1:
        c = next(iter(con_tail))
        return pertenece(c), c, "alta", None
    if len(con_tail) > 1:
        return "ambiguo", None, "", sug
    if not tail and len(cons_unicos) == 1:
        c = next(iter(cons_unicos))
        return pertenece(c), c, "media", None
    if not tail and len(cons_unicos) > 1:
        return "ambiguo", None, "", None
    # fallback: si hay tail pero no coincide con ninguno, intentar por codigo presupuestal
    return ("ok_codigo", sug, "codigo", None) if sug else ("verificar", None, "", None)


# ------------------------------------------------------------------ LECTURA DEL CDP-CRP
def extraer_contratos(ocultar_contratista=False, vigencia="2026"):
    presu = ext.extraer()
    rubros_edu = {}
    for c in presu["componentes"]:
        for s in c["subgrupos"]:
            for r in s["rubros"]:
                rubros_edu[_txt(r["cons_ppt"])] = {"nombre": r["nombre"], "componente": c["nombre"], "color": c["color"],
                                                   "fuente": r.get("fuente") or "", "fondo": r.get("fondo") or "",
                                                   "codigo": r.get("codigo") or ""}
    por_cola = {}
    for k, v in rubros_edu.items():
        t = EE._codigo_tail(v["codigo"])
        por_cola.setdefault(t, set()).add(k)
    por_cola = {t: next(iter(ks)) for t, ks in por_cola.items() if len(ks) == 1}
    hac = _hacienda_para(presu["archivo"])
    mapa = _mapa_cdp(hac) if hac else {}
    mapa_cdps = _mapa_cdps_hacienda(hac) if hac else {}
    detalle_data = _leer_subsecretarias_detalle()
    mapa_subsec = detalle_data["subsec"]
    mapa_objeto_detalle = detalle_data["objeto"]
    mapa_contratista_detalle = detalle_data["contratista"]
    # diagnóstico: cuántos CDP únicos en la columna "cdps"
    if mapa_cdps:
        print(f"debug: columna 'cdps' de Hacienda contiene {len(mapa_cdps)} CDP únicos", file=sys.stderr)
    src = ruta_cdpcrp()
    if not src:
        raise FileNotFoundError("No se encontro el archivo CDP-CRP (ver ruta_cdpcrp.txt o entradas_contratos/)")
    wb = _abrir(src)
    if vigencia not in wb.sheetnames:
        raise KeyError(f"El archivo CDP-CRP no tiene la hoja {vigencia}")
    ws = wb[vigencia]
    merged = {}
    for mr in ws.merged_cells.ranges:
        anc = ws.cell(mr.min_row, mr.min_col).value
        for r in range(mr.min_row, mr.max_row + 1):
            for c in range(mr.min_col, mr.max_col + 1):
                merged[(r, c)] = anc

    def val(r, c):
        v = ws.cell(r, c).value
        return v if v is not None else merged.get((r, c))

    contratos, actual = [], None
    for r in range(2, ws.max_row + 1):
        a = ws.cell(r, 1).value
        if a is not None and _txt(a):
            actual = {"nro": _txt(a), "contratista": _txt(ws.cell(r, 2).value), "valor_contrato": None,
                      "ejecutado_excel": None, "pendiente_excel": None, "lineas": [], "fila": r}
            contratos.append(actual)
        if actual is None:
            continue
        if actual["valor_contrato"] is None and ws.cell(r, 8).value is not None:
            actual["valor_contrato"] = _num(ws.cell(r, 8).value)
        if actual["ejecutado_excel"] is None and ws.cell(r, 26).value is not None:
            actual["ejecutado_excel"] = _num(ws.cell(r, 26).value)
        if actual["pendiente_excel"] is None and ws.cell(r, 28).value is not None:
            actual["pendiente_excel"] = _num(ws.cell(r, 28).value)
        v_cdp, v_crp = _num(ws.cell(r, 5).value), _num(ws.cell(r, 7).value)
        cdp, crp = _txt(val(r, 4)), _txt(val(r, 6))
        codigo = _txt(ws.cell(r, 3).value)
        actas = [_num(ws.cell(r, c).value) for c in range(COL_ACTA_INI, COL_ACTA_FIN + 1)]
        pagado = sum(actas)
        if not (v_cdp or v_crp or pagado or cdp or codigo):
            continue
        res, cons, conf, sug = _resolver(cdp, codigo, mapa, rubros_edu, por_cola)
        # diagnóstico: verifica si el CDP está en la columna "cdps"
        cdp_limpio = cdp
        try:
            cdp_limpio = str(int(float(cdp)))
        except (ValueError, TypeError):
            pass
        en_cdps = cdp_limpio in mapa_cdps if cdp_limpio else False
        if cdp and not en_cdps and res in ("cdp_no_hallado", "verificar"):
            print(f"debug: contrato {actual['nro']} línea CDP={cdp} ({cdp_limpio}) NO en columna 'cdps', "
                  f"fallback: {res}", file=sys.stderr)
        info = rubros_edu.get(cons) if cons and res in ("ok", "ok_codigo") else None
        isug = rubros_edu.get(sug) if sug else None
        actual["lineas"].append({
            "cdp": cdp, "crp": crp, "codigo": codigo, "valor_cdp": v_cdp, "valor_crp": v_crp,
            "pagado": pagado, "actas": sum(1 for x in actas if x),
            "resolucion": res, "confianza": conf, "cons_ppt": cons,
            "rubro": info["nombre"] if info else "", "componente": info["componente"] if info else "",
            "color": info["color"] if info else "", "fuente": info["fuente"] if info else "",
            "fondo": info["fondo"] if info else "",
            "sugerido_cons": sug, "sugerido_rubro": isug["nombre"] if isug else "",
            "sugerido_componente": isug["componente"] if isug else "",
            "sugerido_fuente": isug["fuente"] if isug else "",
            "en_cdps": en_cdps})

    areas = leer_areas()
    salida, dif_pago = [], []
    for c in contratos:
        L = c["lineas"]
        if not L:
            continue
        crp_tot = sum(x["valor_crp"] for x in L)
        pag = sum(x["pagado"] for x in L)
        valor = c["valor_contrato"] if c["valor_contrato"] else None
        ej = c["ejecutado_excel"]
        if ej is not None and abs(ej - pag) > 1000 and pag:
            dif_pago.append({"contrato": c["nro"], "actas": pag, "excel": ej, "diferencia": pag - ej})
        ok = [x for x in L if x["resolucion"] in ("ok", "ok_codigo")]
        por_codigo = [x for x in L if x["resolucion"] == "ok_codigo"]
        comps = sorted({x["componente"] for x in ok})
        fuentes = sorted({x["fuente"] for x in ok if x["fuente"]})
        pend = [x for x in L if x["resolucion"] not in ("ok", "ok_codigo")]
        comps_sug = sorted({x["sugerido_componente"] for x in pend if x["sugerido_componente"]} - set(comps))
        fuentes_sug = sorted({x["sugerido_fuente"] for x in pend if x["sugerido_fuente"]} - set(fuentes))
        if len(ok) == len(L):
            cruce = "completo_codigo" if por_codigo else "completo"
        elif ok:
            cruce = "parcial"
        elif all(x["resolucion"] == "otra_secretaria" for x in L):
            cruce = "otra_secretaria"
        elif all(x["resolucion"] == "vigencia_futura" for x in L):
            cruce = "vigencia_futura"
        elif any(x["resolucion"] in ("ambiguo", "verificar", "cdp_no_hallado", "sin_cdp") for x in L):
            cruce = "verificar"
        else:
            cruce = "sin_resolver"
        # area: contrato manda; si no, la de los rubros resueltos
        area = areas["contrato"].get(c["nro"])
        if not area:
            asig = {areas["rubro"].get(x["cons_ppt"]) for x in ok}
            asig.discard(None)
            faltan = any(areas["rubro"].get(x["cons_ppt"]) is None for x in ok)
            area = (next(iter(asig)) if len(asig) == 1 and not faltan else
                    "Varias áreas" if len(asig) > 1 else "")
        for x in L:
            x["area"] = areas["contrato"].get(c["nro"]) or areas["rubro"].get(x["cons_ppt"] or "", "")
        # Subsecretaría, objeto y contratista: MAPA_CONTRATO (areas_educacion.xlsx, manual y confiable)
        # manda primero; el DETALLE FINANCIERO por código presupuestal es solo respaldo.
        responsable = areas["contrato"].get(c["nro"], "")
        contratista_final = c["contratista"]
        objeto_final = areas["objeto"].get(c["nro"], "")
        if not (responsable and objeto_final and contratista_final):
            for linea in L:
                cons_ppt = _txt(linea.get("cons_ppt"))
                if cons_ppt:
                    if not responsable and cons_ppt in mapa_subsec:
                        responsable = mapa_subsec[cons_ppt]
                    if not objeto_final and cons_ppt in mapa_objeto_detalle:
                        objeto_final = mapa_objeto_detalle[cons_ppt]
                    if not contratista_final and cons_ppt in mapa_contratista_detalle:
                        contratista_final = mapa_contratista_detalle[cons_ppt]
                    if responsable and objeto_final and contratista_final:
                        break
        salida.append({
            "nro": c["nro"], "contratista": "" if ocultar_contratista else contratista_final,
            "objeto": objeto_final, "valor_contrato": valor,
            "valor_cdp": sum(x["valor_cdp"] for x in L), "valor_crp": crp_tot, "pagado": pag,
            "ejecutado_excel": ej, "actas": sum(x["actas"] for x in L),
            "componentes": comps, "fuentes": fuentes, "area": area or "",
            "responsable": responsable,
            "componentes_sugeridos": comps_sug, "fuentes_sugeridas": fuentes_sug,
            "cruce": cruce, "lineas_por_codigo": len(por_codigo),
            "fila_excel": c["fila"], "lineas": L})

    # diagnóstico: resumen de CDP en columna "cdps"
    total_lineas = sum(len(c["lineas"]) for c in salida)
    lineas_en_cdps = sum(sum(1 for x in c["lineas"] if x.get("en_cdps")) for c in salida)
    lineas_no_en_cdps = sum(sum(1 for x in c["lineas"] if x.get("cdp") and not x.get("en_cdps")) for c in salida)
    if total_lineas > 0:
        pct_en_cdps = 100 * lineas_en_cdps / total_lineas if total_lineas else 0
        print(f"resumen: {lineas_en_cdps}/{total_lineas} líneas con CDP en columna 'cdps' ({pct_en_cdps:.1f}%)", file=sys.stderr)
    resumen_cruce = {}
    for c in salida:
        resumen_cruce[c["cruce"]] = resumen_cruce.get(c["cruce"], 0) + 1
    rubros_con = {x["cons_ppt"] for c in salida for x in c["lineas"] if x["resolucion"] in ("ok", "ok_codigo")}
    try:
        asegurar_areas([dict(cons_ppt=k, nombre=v["nombre"], componente=v["componente"], con_contratos=k in rubros_con)
                        for k, v in rubros_edu.items()], [c["nro"] for c in salida])
    except Exception as e:  # el mapa es opcional; no debe tumbar el dashboard
        print("aviso: no se pudo actualizar areas_educacion.xlsx:", e, file=sys.stderr)
    # Obtener fecha de última actualización del archivo DETALLE FINANCIERO
    ruta_detalle = ruta_detalle_financiero()
    fecha_ultima_act = None
    if ruta_detalle and os.path.exists(ruta_detalle):
        try:
            mtime = os.path.getmtime(ruta_detalle)
            fecha_ultima_act = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M:%S")
        except Exception as e:
            print(f"debug: no se pudo obtener fecha del detalle: {e}", file=sys.stderr)

    return {
        "vigencia": vigencia, "corte": presu["corte"], "archivo_cdpcrp": os.path.basename(src),
        "archivo_presupuesto": presu["archivo"], "generado": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "hacienda": os.path.basename(hac) if hac else None,
        "fecha_ultima_actualizacion_detalle": fecha_ultima_act,
        "areas": areas["areas"], "areas_definidas": len(areas["rubro"]) + len(areas["contrato"]),
        "rubros_total": len(rubros_edu), "rubros_con_contratos": len(rubros_con),
        "rubros_con_contratos_sin_area": len([k for k in rubros_con if k not in areas["rubro"]]),
        "cruce": resumen_cruce,
        "crp_por_estado": {e: sum(l["valor_crp"] for c in salida for l in c["lineas"] if l["resolucion"] == e)
                           for e in {l["resolucion"] for c in salida for l in c["lineas"]}},
        "diferencias_pago": dif_pago,
        "otros_periodos_pendientes": [y for y in wb.sheetnames if y.isdigit() and y != vigencia],
        "contratistas_ocultos": ocultar_contratista, "contratos": salida}


if __name__ == "__main__":
    import json
    d = extraer_contratos()
    print(json.dumps({k: v for k, v in d.items() if k != "contratos"}, ensure_ascii=False, indent=1))
    for c in d["contratos"][:4]:
        print(c["nro"], "|", c["cruce"], "|", c["componentes"], "|", round(c["valor_crp"]), round(c["pagado"]), len(c["lineas"]), "lineas")
