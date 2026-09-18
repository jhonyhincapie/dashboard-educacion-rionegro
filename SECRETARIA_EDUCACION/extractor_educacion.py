# -*- coding: utf-8 -*-
"""
EXTRACTOR DE PRESUPUESTO — SECRETARIA DE EDUCACION DE RIONEGRO
=============================================================

Transforma el Excel de egresos del municipio (formato Hacienda) en un
informe consolidado que contiene SOLO el presupuesto de la Secretaria de
Educacion, con los contratos y su ejecucion.

ENTRADAS
  1. Presupuesto de egreso a DD_MM_YYYY.xls   (Hacienda -> las cifras, SIN colorear --
                                                el usuario ya NO tiene que marcar nada)
  2. maestro_rubros_educacion.xlsx            (usuario  -> hoja RUBROS_EDUCACION: lista
                                                confirmada de cons_ppt -> componente;
                                                hoja MAPA_COLORES: componente -> color
                                                que el SISTEMA usa para pintar la salida)
  3. seguimiento_manual_educacion.xlsx        (usuario  -> contratos y observaciones)
        - hoja RUBROS   : una fila por rubro (nombre legible, responsable, nota)
        - hoja CONTRATOS: una fila por contrato (varios por rubro)

SALIDA  ->  informes/Seguimiento Presupuestal ...
  Hoja 1 EJECUTIVO   : cifras clave, por componente, por fuente, por concepto SGP, alertas
  Hoja 2 SEGUIMIENTO : la tabla por componente -> proyecto, coloreada automaticamente
  Hoja 3 CONTRATOS   : una fila por contrato, con ejecucion y % + conciliacion contra el rubro
  Hoja 4 NOTAS        : glosario, conciliacion, como se alimenta

REGLA DE ALCANCE (vigencia 2026, confirmada por el usuario el 2026-09-16)
  ES_EDUCACION = el cons_ppt del rubro esta en la lista maestra RUBROS_EDUCACION
                 (127 cons_ppt confirmados sobre el corte 15_09_2026, uno por uno,
                 cruzando colores que el usuario puso a mano UNA SOLA VEZ contra el
                 Hacienda). El componente de cada rubro es el que indique esa lista.
  Sobre filas hoja (final = 'S'). Se excluye la seccion "CIERRE DE RESERVAS".
  NOTA: el codigo_rubro (prefijo 02.01/01.01) NO basta para clasificar -- rubros
  hermanos bajo el mismo codigo padre pueden ser de otra Secretaria (confirmado
  con el caso 01.01.2.3.2.02.02.009: solo 1 de 8 hijos es de Educacion). Por eso
  la lista de cons_ppt es la fuente de verdad, no el codigo.
  Un cons_ppt NUEVO (adicion presupuestal, proyecto nuevo) que no este en la lista
  y cuyo codigo/fuente sugiera Educacion cae en "REVISAR": el usuario lo confirma
  una vez y se agrega a RUBROS_EDUCACION para que en adelante entre solo.

Uso:
    python extractor_educacion.py "ruta\\Presupuesto de egreso a 31_08_2026.xls"
"""

import os
import re
import sys
import csv
import json
import datetime

import xlrd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, GradientFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart, Reference
from openpyxl.drawing.image import Image as XLImage

# --------------------------------------------------------------------------- #
# CONFIG
# --------------------------------------------------------------------------- #
BASE = os.path.dirname(os.path.abspath(__file__))
MAESTRO_PATH = os.path.join(BASE, "maestro_rubros_educacion.xlsx")
MANUAL_PATH = os.path.join(BASE, "seguimiento_manual_educacion.xlsx")
SALIDAS_DIR = os.path.join(BASE, "informes")
HIST_PATH = os.path.join(BASE, "historial_corridas.csv")
CDPCRP_DIR = os.path.join(BASE, "entradas_contratos")

EXCLUIR_SECCIONES = ("CIERRE DE RESERVAS",)
SEGUIMIENTO_MANUAL_TOTAL_15_08 = 219_422_883_163  # referencia de conciliacion

COLS_EGRESOS = [
    "ano", "cons_ppt", "codigo_padre", "codigo", "final", "fondo",
    "descripcion_fuente", "tip_destinac", "vlr_aprobado", "adiciones",
    "reducciones", "tras_adic", "tras_reduc", "tot_ppto", "tot_reserv",
    "tot_crp", "tot_ops", "tot_pag",
]


# --------------------------------------------------------------------------- #
# COMPONENTES — definidos por el color que el usuario pone en el Hacienda.
# Confirmado por el usuario el 2026-09-16 sobre el corte 15_09_2026.
# El color_hex es el color EXACTO de relleno que trae la celda 'descripcion'
# en el archivo de Hacienda (paleta clasica de Excel .xls). Este mismo color
# se usa luego para pintar la fila en el informe de salida (EJECUTIVO/SEGUIMIENTO),
# asi el informe se ve igual a como el usuario marco el Hacienda.
# --------------------------------------------------------------------------- #
MAPA_COLORES_DEFAULT = {
    "FFFF00": "PRESTACION DEL SERVICIO",
    "CCFFFF": "RECURSOS PROPIOS O LIBRE INVERSION",
    "FFFFCC": "RENDIMIENTOS O RECURSOS DEL BALANCE DE PRESTACION DEL SERVICIO",
    "00CCFF": "SGP - PGN - PAE",
    "99CC00": "CALIDAD MATRICULA",
    "FFCC99": "PRIMERA INFANCIA",
    "FFCC00": "CALIDAD GRATUIDAD",
    "FF99CC": "INFRAESTRUCTURA",
    "C0C0C0": "VIGENCIAS ANTERIORES",
}

ORDEN_COMPONENTE = [
    "PRESTACION DEL SERVICIO",
    "RECURSOS PROPIOS O LIBRE INVERSION",
    "RENDIMIENTOS O RECURSOS DEL BALANCE DE PRESTACION DEL SERVICIO",
    "CALIDAD MATRICULA",
    "CALIDAD GRATUIDAD",
    "SGP - PGN - PAE",
    "PRIMERA INFANCIA",
    "INFRAESTRUCTURA",
    "VIGENCIAS ANTERIORES",
]

# Color de relleno a usar en el informe de salida por componente = el mismo
# color que el usuario puso en el Hacienda (se recalcula a partir de MAPA_COLORES
# leido del maestro; este dict es solo el default / fallback).
COLOR_COMPONENTE = {v: k for k, v in MAPA_COLORES_DEFAULT.items()}

H_FONT = Font(bold=True, color="FFFFFF", size=10)
H_FILL = PatternFill("solid", fgColor="1F4E79")
SUB_FONT = Font(bold=True)
SUB_FILL = PatternFill("solid", fgColor="D9E1F2")
TOT_FILL = PatternFill("solid", fgColor="BDD7EE")
ALERT_FILL = PatternFill("solid", fgColor="FFC7CE")
BIG = Font(bold=True, size=16)
LBL = Font(size=9, color="595959")
MON = "#,##0"
PCT = "0.0%"
WRAP = Alignment(wrap_text=True, vertical="top")

# --------------------------------------------------------------------------- #
# IDENTIDAD VISUAL -- Alcaldia de Rionegro (paleta institucional oficial,
# "COLORES AR 2024.pdf"). Uso moderado: titulos, lineas, acentos -- NUNCA para
# repintar la tabla SEGUIMIENTO POR COMPONENTE ni los colores de componente.
# --------------------------------------------------------------------------- #
INST_ROJO_OSCURO = "780001"
INST_ROJO = "A80506"
INST_ROJO_CLARO = "DA121A"
INST_CREMA = "FFF7EA"
INST_DORADO = "D8A563"
INST_AZUL = "144E76"

FUENTE_SANS = "Segoe UI"
MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
           "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _fecha_es(fecha):
    """dd de <mes en espanol> de aaaa -- sin depender del locale del sistema
    (que en este equipo da el mes en ingles con %B)."""
    return "%d de %s de %d" % (fecha.day, MESES_ES[fecha.month - 1], fecha.year)


def _buscar_logo():
    """Busca el logo institucional con glob (evita tildes literales en el
    codigo fuente, que en este equipo se corrompen al leer el .py)."""
    import glob
    patrones = [
        os.path.join("C:\\", "Users", "jhincapie", "OneDrive - Municipio de Rionegro",
                     "Escritorio", "RENTAS", "10_MODELOS_PLANTILLAS", "Logotipo*",
                     "LOGO*VERT*COLOR*.png"),
    ]
    for pat in patrones:
        encontrados = glob.glob(pat)
        if encontrados:
            return encontrados[0]
    return None


RUTA_LOGO = _buscar_logo()

# Rampa secuencial para el embudo Definitivo->Reservado->Comprometido->Obligado->Pagado
# (un solo hilo de color que se oscurece, en vez de 5 colores sin relacion)
COLOR_ETAPA = {
    "Presupuesto Definitivo": "D9D9D9",
    "Reservado CDP": "A9C4D8",
    "Comprometido RP": "5B90B0",
    "Obligado OPS": INST_AZUL,
    "Pagado": INST_DORADO,
}
CARD_BORDE = Side(style="thin", color="C9C9C9")
CARD_BORDE_INST = Side(style="thin", color=INST_DORADO)


# --------------------------------------------------------------------------- #
# LECTURA — EGRESOS
# --------------------------------------------------------------------------- #
def _n(v):
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def fecha_de_corte(path):
    m = re.search(r"(\d{2})[_-](\d{2})[_-](\d{4})", os.path.basename(path))
    if not m:
        raise SystemExit("No se pudo leer la fecha de corte del nombre del archivo "
                         "(se espera 'a DD_MM_YYYY').")
    d, mth, y = m.groups()
    return datetime.date(int(y), int(mth), int(d))


def leer_egresos(path):
    # El archivo de Hacienda entra TAL CUAL se descarga -- sin colorear.
    # La clasificacion Educacion/no-Educacion se hace despues, por cons_ppt,
    # contra la lista maestra RUBROS_EDUCACION (ver clasificar()).
    wb = xlrd.open_workbook(path)
    sh = wb.sheet_by_index(0)
    H = [str(sh.cell_value(0, c)).strip() for c in range(sh.ncols)]
    faltan = [c for c in COLS_EGRESOS if c not in H]
    if faltan:
        raise SystemExit("El archivo de egresos no tiene el formato esperado.\n"
                         "Faltan columnas: " + ", ".join(faltan))

    ix_desc = [i for i, h in enumerate(H) if h == "descripcion"]
    ix_cod = [i for i, h in enumerate(H) if h == "codigo"]
    C = {h: H.index(h) for h in set(H)}
    PAD = C["codigo_padre"]
    COD_SEG = ix_cod[0]
    DESCR, SECNOM = ix_desc[0], ix_desc[1]

    filas = []
    for r in range(2, sh.nrows):
        row = [sh.cell_value(r, c) for c in range(sh.ncols)]
        if str(row[C["final"]]) != "S":
            continue
        sec = str(row[SECNOM]).strip()
        if any(x in sec.upper() for x in EXCLUIR_SECCIONES):
            continue
        cons = str(row[C["cons_ppt"]]).strip()
        if not cons:
            continue
        try:
            cons = str(int(float(cons)))
        except ValueError:
            pass
        full = (str(row[PAD]) + str(row[COD_SEG])).strip()
        d = {
            "cons_ppt": cons,
            "codigo_rubro": full,
            "naturaleza": ".".join(full.split(".")[2:5]),
            "nombre": str(row[DESCR]).strip(),
            "seccion": sec,
            "fondo": str(row[C["fondo"]]).strip(),
            "fuente": str(row[C["descripcion_fuente"]]).strip(),
            "tip_destinac": str(row[C["tip_destinac"]]).strip(),
            "bpim": str(row[C["bpim"]]).strip() if "bpim" in C else "",
            "definitiva": _n(row[C["tot_ppto"]]),
            "reservado": _n(row[C["tot_reserv"]]),
            "comprometido": _n(row[C["tot_crp"]]),
            "obligado": _n(row[C["tot_ops"]]),
            "pagado": _n(row[C["tot_pag"]]),
        }
        d["grupo_naturaleza"] = ("Nomina y aportes" if d["naturaleza"] == "2.3.1"
                                 else "Inversion / proyectos" if d["naturaleza"] == "2.3.2"
                                 else "Otro")
        filas.append(d)
    return filas


# --------------------------------------------------------------------------- #
# MAESTRO
# --------------------------------------------------------------------------- #
def crear_maestro_vacio(path):
    wb = Workbook()
    ws = wb.active
    ws.title = "REGLA_BASE"
    ws.append(["regla", "descripcion"])
    ws.append(["cons_ppt esta en la lista maestra RUBROS_EDUCACION",
               "Un rubro es de Educacion si su cons_ppt aparece en la hoja "
               "RUBROS_EDUCACION. El color de cada fila en el informe de salida lo "
               "pone el SISTEMA segun el componente (ver MAPA_COLORES) -- el usuario "
               "NO tiene que colorear el archivo de Hacienda. El codigo (02.01/01.01) "
               "NO basta para clasificar: rubros hermanos bajo el mismo codigo padre "
               "pueden ser de otra Secretaria."])
    for c in range(1, 3):
        ws.cell(1, c).font = SUB_FONT
        ws.cell(1, c).fill = SUB_FILL
    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 90

    wm = wb.create_sheet("MAPA_COLORES")
    wm.append(["componente", "color_hex"])
    for c in range(1, 3):
        wm.cell(1, c).font = SUB_FONT
        wm.cell(1, c).fill = SUB_FILL
    for color_hex, comp in MAPA_COLORES_DEFAULT.items():
        r = wm.max_row + 1
        wm.append([comp, color_hex])
        wm.cell(r, 2).fill = PatternFill("solid", fgColor=color_hex)
    wm.column_dimensions["A"].width = 60
    wm.column_dimensions["B"].width = 14

    wr = wb.create_sheet("RUBROS_EDUCACION")
    wr.append(["cons_ppt", "codigo_rubro", "descripcion", "componente",
               "fecha_confirmacion", "fuente_confirmacion"])
    for c in range(1, 7):
        wr.cell(1, c).font = SUB_FONT
        wr.cell(1, c).fill = SUB_FILL
    for c, wd in zip(range(1, 7), [10, 24, 60, 45, 16, 40]):
        wr.column_dimensions[get_column_letter(c)].width = wd

    w = wb.create_sheet("EXCLUSIONES")
    w.append(["cons_ppt", "codigo_rubro", "nombre", "motivo",
              "documento_soporte", "fecha", "responsable"])
    for c in range(1, 8):
        w.cell(1, c).font = SUB_FONT
        w.cell(1, c).fill = SUB_FILL
    for c, wd in zip(range(1, 8), [12, 30, 45, 40, 24, 14, 20]):
        w.column_dimensions[get_column_letter(c)].width = wd
    wb.save(path)


def leer_maestro(path):
    if not os.path.exists(path):
        crear_maestro_vacio(path)
        print("  + creado maestro vacio:", os.path.basename(path))
    wb = load_workbook(path)

    rubros_edu = {}  # cons_ppt -> {"componente": ..., "subgrupo": ...}
    if "RUBROS_EDUCACION" in wb.sheetnames:
        ws_re = wb["RUBROS_EDUCACION"]
        # Buscar columnas por NOMBRE (no por posicion fija) -- robusto a columnas
        # vacias intermedias o reordenamientos manuales del maestro.
        headers_re = [str(c.value).strip().lower() if c.value else "" for c in ws_re[1]]
        def idx_col(nombre, default=None):
            return headers_re.index(nombre) if nombre in headers_re else default
        ix_cons = idx_col("cons_ppt", 0)
        ix_comp = idx_col("componente", 3)
        ix_subg = idx_col("subgrupo")
        for row in ws_re.iter_rows(min_row=2, values_only=True):
            if row and row[ix_cons] not in (None, "") and row[ix_comp] not in (None, ""):
                cons = str(row[ix_cons]).strip()
                try:
                    cons = str(int(float(cons)))
                except ValueError:
                    pass
                comp = " ".join(str(row[ix_comp]).split())
                subg = (" ".join(str(row[ix_subg]).split())
                        if ix_subg is not None and row[ix_subg] not in (None, "") else comp)
                rubros_edu[cons] = {"componente": comp, "subgrupo": subg}

    mapa_colores = dict(MAPA_COLORES_DEFAULT)  # componente -> color_hex
    if "MAPA_COLORES" in wb.sheetnames:
        leido = {}
        for row in wb["MAPA_COLORES"].iter_rows(min_row=2, values_only=True):
            if row and row[0] not in (None, "") and row[1] not in (None, ""):
                leido[" ".join(str(row[0]).split())] = str(row[1]).strip().upper().lstrip("#")
        if leido:
            mapa_colores = leido

    exc = {}
    if "EXCLUSIONES" in wb.sheetnames:
        for row in wb["EXCLUSIONES"].iter_rows(min_row=2, values_only=True):
            if row and row[0] not in (None, ""):
                exc[str(row[0]).strip()] = dict(zip(
                    ["codigo_rubro", "nombre", "motivo", "documento_soporte",
                     "fecha", "responsable"], row[1:7]))
    return rubros_edu, mapa_colores, exc


# --------------------------------------------------------------------------- #
# SEGUIMIENTO MANUAL (2 hojas)
# --------------------------------------------------------------------------- #
COLS_M_RUBROS = ["cons_ppt", "codigo_rubro", "nombre_sistema",
                 "proyecto_nombre", "responsable", "observacion"]
COLS_M_CONTRATOS = ["cons_ppt", "nro_contrato", "contratista", "objeto_contrato",
                    "valor_contrato", "fecha_suscripcion", "comprometido",
                    "obligado", "pagado", "cdp", "rp", "estado", "supervisor",
                    "observacion"]
ESTADOS = ["Sin iniciar", "En proceso de contratacion", "En ejecucion",
           "Suspendido", "Liquidado"]


def crear_manual_template(path, filas_edu):
    wb = Workbook()

    ws = wb.active
    ws.title = "RUBROS"
    ws.append(COLS_M_RUBROS)
    for c in range(1, len(COLS_M_RUBROS) + 1):
        ws.cell(1, c).font = H_FONT
        ws.cell(1, c).fill = H_FILL
    for d in sorted(filas_edu, key=lambda x: x["codigo_rubro"]):
        ws.append([d["cons_ppt"], d["codigo_rubro"], d["nombre"], "", "", ""])
    for c, wd in zip(range(1, 7), [12, 30, 48, 46, 22, 50]):
        ws.column_dimensions[get_column_letter(c)].width = wd
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions

    wc = wb.create_sheet("CONTRATOS")
    wc.append(COLS_M_CONTRATOS)
    for c in range(1, len(COLS_M_CONTRATOS) + 1):
        wc.cell(1, c).font = H_FONT
        wc.cell(1, c).fill = H_FILL
    for c, wd in zip(range(1, len(COLS_M_CONTRATOS) + 1),
                     [12, 16, 26, 46, 16, 15, 16, 16, 16, 12, 12, 24, 22, 44]):
        wc.column_dimensions[get_column_letter(c)].width = wd
    # validaciones
    ref = wb.create_sheet("_LISTAS")
    ref.sheet_state = "hidden"
    conss = [d["cons_ppt"] for d in sorted(filas_edu, key=lambda x: x["codigo_rubro"])]
    for i, cv in enumerate(conss, start=1):
        ref.cell(i, 1, cv)
    for i, ev in enumerate(ESTADOS, start=1):
        ref.cell(i, 2, ev)
    dv_cons = DataValidation(type="list",
                             formula1=f"=_LISTAS!$A$1:$A${len(conss)}", allow_blank=True)
    dv_est = DataValidation(type="list",
                            formula1=f"=_LISTAS!$B$1:$B${len(ESTADOS)}", allow_blank=True)
    wc.add_data_validation(dv_cons)
    wc.add_data_validation(dv_est)
    dv_cons.add("A2:A2000")
    dv_est.add("L2:L2000")
    wc.freeze_panes = "C2"
    wc.auto_filter.ref = "A1:N1"

    ay = wb.create_sheet("AYUDA")
    ay.append(["hoja / columna", "que hacer"])
    guia = [
        ("HOJA RUBROS", "Una fila por rubro. Ya vienen los 130. NO editar cons_ppt ni codigo_rubro."),
        ("  proyecto_nombre", "Nombre legible del proyecto (opcional, reemplaza al del sistema)."),
        ("  responsable", "Quien responde por el rubro."),
        ("  observacion", "Nota del rubro para el corte."),
        ("HOJA CONTRATOS", "Una fila por contrato. Un rubro puede tener varios."),
        ("  cons_ppt", "Elegir de la lista desplegable. Es la llave que amarra el contrato al rubro."),
        ("  nro_contrato / contratista / objeto_contrato", "Datos del contrato."),
        ("  valor_contrato", "Valor total del contrato (numero, sin puntos)."),
        ("  fecha_suscripcion", "dd/mm/aaaa."),
        ("  comprometido / obligado / pagado", "Ejecucion del contrato a la fecha de corte (numeros)."),
        ("  cdp / rp", "Numeros de CDP y RP (opcional, para trazabilidad)."),
        ("  estado", "Elegir de la lista."),
        ("  supervisor / observacion", "Texto libre."),
        ("COMO SE ACTUALIZA", "Guardar este archivo y hacer doble clic en GENERAR_INFORME.bat. "
                              "El informe se rehace leyendo todo lo que este aqui."),
    ]
    for g in guia:
        ay.append(list(g))
    ay.column_dimensions["A"].width = 42
    ay.column_dimensions["B"].width = 92
    for r in range(2, ay.max_row + 1):
        ay.cell(r, 1).font = SUB_FONT
        ay.cell(r, 2).alignment = Alignment(wrap_text=True)
    wb.save(path)


def leer_manual(path, filas_edu):
    if not os.path.exists(path):
        crear_manual_template(path, filas_edu)
        print("  + creada plantilla de seguimiento manual:", os.path.basename(path))
        return {}, []
    wb = load_workbook(path)
    rubros = {}
    if "RUBROS" in wb.sheetnames:
        ws = wb["RUBROS"]
        hdr = [str(c.value).strip() if c.value else "" for c in ws[1]]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or row[0] in (None, ""):
                continue
            rec = {hdr[i]: row[i] for i in range(min(len(hdr), len(row)))}
            rubros[str(rec.get("cons_ppt")).strip()] = rec
    contratos = []
    if "CONTRATOS" in wb.sheetnames:
        ws = wb["CONTRATOS"]
        hdr = [str(c.value).strip() if c.value else "" for c in ws[1]]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or all(v in (None, "") for v in row):
                continue
            rec = {hdr[i]: row[i] for i in range(min(len(hdr), len(row)))}
            rec["cons_ppt"] = str(rec.get("cons_ppt") or "").strip()
            contratos.append(rec)
    return rubros, contratos


def _codigo_tail(codigo_str):
    """Parte del codigo presupuestal desde la naturaleza (2.3....) en adelante --
    el prefijo de seccion/dependencia difiere entre el Hacienda y el CDP-CRP
    (usan esquemas de codificacion distintos), pero esta cola es comparable."""
    codigo_str = (codigo_str or "").strip()
    i = codigo_str.find("2.3.")
    return codigo_str[i:] if i >= 0 else codigo_str


def _construir_mapa_cdp_hacienda(hacienda_path):
    """cdp_numero (str, sin signo ni prefijo de vigencia) -> lista de
    (cons_ppt, codigo_tail) de cada rubro final='S' del Hacienda de ESTE corte.
    Un mismo numero de CDP puede amparar varios rubros (CDP de una sola bolsa
    repartida en varios cons_ppt), por eso el valor es una lista."""
    wb = xlrd.open_workbook(hacienda_path)
    sh = wb.sheet_by_index(0)
    H = [str(sh.cell_value(0, c)).strip() for c in range(sh.ncols)]
    if "cdps" not in H:
        return {}
    C = {h: H.index(h) for h in set(H)}
    mapa = {}
    for r in range(1, sh.nrows):
        if str(sh.cell_value(r, C["final"])) != "S":
            continue
        cons = sh.cell_value(r, C["cons_ppt"])
        cons_str = str(int(cons)) if isinstance(cons, float) else str(cons).strip()
        full = (str(sh.cell_value(r, C["codigo_padre"])) + str(sh.cell_value(r, C["codigo"]))).strip()
        tail = _codigo_tail(full)
        cdps_str = str(sh.cell_value(r, C["cdps"]) or "")
        for n in re.findall(r"\d+", cdps_str):
            mapa.setdefault(n, []).append((cons_str, tail))
    return mapa


def leer_cdp_crp(hacienda_path, edu):
    """Lee el archivo CDP-CRP (hoja 2026) y amarra cada contrato a un cons_ppt
    real usando el NUMERO DE CDP (identificador unico del sistema de Hacienda),
    desambiguando con la cola del codigo presupuestal cuando un mismo CDP
    ampara varios rubros. Nunca adivina: si no puede resolver un match unico
    lo deja marcado como 'ambiguo' o 'sin match' en vez de asignar al azar."""
    import glob
    archivos = glob.glob(os.path.join(CDPCRP_DIR, "Seguimiento CDP-CRP*.xlsx"))
    if not archivos:
        return []
    file_path = archivos[0]
    try:
        wb = load_workbook(file_path, data_only=True)
        ws = wb["2026"] if "2026" in wb.sheetnames else None
        if not ws:
            return []
    except Exception:
        return []

    cdp_map = _construir_mapa_cdp_hacienda(hacienda_path)
    cons_edu = {d["cons_ppt"] for d in edu}

    # columnas: 1 Nro contrato, 2 Contratista, 3 Codigo pptal, 4 CDP, 5 Valor CDP,
    # 6 CRP, 7 Valor CRP, 8 Valor contrato, 9..25 ACTA DE PAGO 01..17
    headers_c = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
    cols_acta = [i + 1 for i, h in enumerate(headers_c) if h and "ACTA" in str(h).upper()]

    contratos = []
    contrato = contratista = ""
    for r in range(2, ws.max_row + 1):
        a = ws.cell(r, 1).value
        b = ws.cell(r, 2).value
        cod = ws.cell(r, 3).value
        cdp = ws.cell(r, 4).value
        valor_crp = ws.cell(r, 7).value
        valor_contrato = ws.cell(r, 8).value
        pagado = sum(_n(ws.cell(r, c).value) for c in cols_acta)

        if a:
            contrato = str(a).strip()
        if b:
            contratista = str(b).strip()

        if cdp in (None, "", 0):
            continue
        cdp_str = str(cdp).strip()

        # CDP con formato "-YYYYNNN" = vigencia futura de OTRO periodo (compromiso
        # que ya se registro en un Hacienda de un año distinto al de este corte;
        # no aparece en el 'cdps' del Hacienda actual, es normal -- ver
        # [[vigencias-futuras-cdp-crp]]). Se reporta aparte, sin intentar matchear.
        if cdp_str.startswith("-") and len(cdp_str) > 4:
            try:
                vigencia_futura = str(int(float(cdp_str[1:5])))
            except ValueError:
                vigencia_futura = ""
            contratos.append({
                "nro_contrato": contrato, "contratista": contratista, "cons_ppt": None,
                "cdp": cdp_str, "vigencia_futura": vigencia_futura,
                "comprometido": _n(valor_crp), "obligado": 0, "pagado": pagado,
                "valor_contrato": _n(valor_contrato), "match": "vigencia_futura_otro_periodo",
            })
            continue

        try:
            cdp_num = str(int(float(cdp_str)))
        except ValueError:
            cdp_num = cdp_str

        candidatos = cdp_map.get(cdp_num, [])
        cod_tail = _codigo_tail(str(cod)) if cod else None
        cons_unicos = {c for c, t in candidatos}

        if not cons_unicos:
            cons_final, match_tipo = None, "cdp_no_encontrado_en_hacienda"
        elif len(cons_unicos) == 1:
            cons_final, match_tipo = next(iter(cons_unicos)), "match_unico_por_cdp"
        else:
            filtrados = {c for c, t in candidatos if cod_tail and t == cod_tail}
            if len(filtrados) == 1:
                cons_final, match_tipo = next(iter(filtrados)), "match_por_cdp_y_codigo"
            else:
                cons_final = None
                match_tipo = "ambiguo:" + ",".join(sorted(cons_unicos))

        contratos.append({
            "nro_contrato": contrato, "contratista": contratista, "cons_ppt": cons_final,
            "cdp": cdp_str, "vigencia_futura": "",
            "comprometido": _n(valor_crp), "obligado": 0, "pagado": pagado,
            "valor_contrato": _n(valor_contrato), "match": match_tipo,
            "_es_educacion": cons_final in cons_edu if cons_final else False,
        })

    return contratos


# --------------------------------------------------------------------------- #
# CLASIFICACION
# --------------------------------------------------------------------------- #
def clasificar(filas, rubros_edu, exc):
    """ES_EDUCACION = el cons_ppt esta en la lista maestra RUBROS_EDUCACION.
    'revisar' junta cons_ppt NUEVOS (no estan en la lista) cuyo codigo o fuente
    sugiere que podrian ser de Educacion -- el usuario los confirma una vez y
    quedan agregados a RUBROS_EDUCACION para las corridas futuras."""
    edu, no_edu, revisar = [], [], []
    for d in filas:
        c = d["cons_ppt"]
        if c in exc:
            no_edu.append(d)
        elif c in rubros_edu:
            d["componente"] = rubros_edu[c]["componente"]
            d["subgrupo"] = rubros_edu[c]["subgrupo"]
            edu.append(d)
        else:
            cod = d["codigo_rubro"]
            u = d["fuente"].upper()
            if d["definitiva"] != 0 and (cod.startswith("02.01") or cod.startswith("01.01")
                                          or "EDUCACION" in u or "EDUCACIÓN" in u):
                revisar.append(dict(d, senal="cons_ppt nuevo, no esta en RUBROS_EDUCACION"))
            else:
                no_edu.append(d)
    return edu, no_edu, revisar


# --------------------------------------------------------------------------- #
# INFORME
# --------------------------------------------------------------------------- #
def pct(num, den):
    return (num / den) if den else None


def _hdr(ws, cols, widths, fila=1):
    for j, t in enumerate(cols, start=1):
        cc = ws.cell(fila, j, t)
        cc.font = H_FONT
        cc.fill = H_FILL
        cc.alignment = Alignment(wrap_text=True, vertical="center")
    for j, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w


# Diseño limpio y profesional: fondo extremadamente ligero (casi blanco),
# sin gradientes exagerados, sin sombras fuertes.
CARD_FILL_LIGERO = PatternFill("solid", fgColor="FAFAFA")  # Gris prácticamente blanco


def _caja(ws, r1, c1, r2, c2, borde=None, relleno=None, sombra=False):
    """Dibuja un borde perimetral sobre el rango r1:c1 - r2:c2 y opcionalmente
    aplica un relleno de fondo (efecto "tarjeta"). Sombra = False por defecto
    (diseño limpio). Si se activa, agrega solo una línea muy discreta."""
    borde = borde or CARD_BORDE
    for rr in range(r1, r2 + 1):
        for cc_i in range(c1, c2 + 1):
            cell = ws.cell(rr, cc_i)
            if relleno is not None:
                cell.fill = relleno
            top = borde if rr == r1 else None
            bottom = borde if rr == r2 else None
            left = borde if cc_i == c1 else None
            right = borde if cc_i == c2 else None
            cell.border = Border(top=top, bottom=bottom, left=left, right=right)
    if sombra:
        # Sombra mínima y discreta: línea fina gris muy clara una fila/columna abajo
        sombra_fill_discreta = PatternFill("solid", fgColor="F5F5F5")
        for cc_i in range(c1, c2 + 1):
            ws.cell(r2 + 1, cc_i).fill = sombra_fill_discreta
        for rr in range(r1, r2 + 1):
            ws.cell(rr, c2 + 1).fill = sombra_fill_discreta


def _tarjeta_kpi(ws, r0, c0, ancho, alto, label, valor_formula, pct_formula, desc,
                 borde=None):
    """Construye una tarjeta KPI de `ancho` columnas x `alto` filas:
    fila0=etiqueta, fila1-2=valor grande, fila3=porcentaje, fila4-{alto-1}=descripcion.
    Todo lo numerico es formula/referencia -- nunca un valor fijo."""
    c1, c2 = c0, c0 + ancho - 1
    ws.merge_cells(start_row=r0, start_column=c1, end_row=r0, end_column=c2)
    lb = ws.cell(r0, c1, label)
    lb.font = Font(size=9, bold=True, color="647587")
    lb.alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells(start_row=r0 + 1, start_column=c1, end_row=r0 + 2, end_column=c2)
    val = ws.cell(r0 + 1, c1, valor_formula)
    val.font = Font(size=17, bold=True, color=INST_AZUL, name=FUENTE_SANS)
    val.number_format = MON
    val.alignment = Alignment(horizontal="left", vertical="center")

    if pct_formula is not None:
        ws.merge_cells(start_row=r0 + 3, start_column=c1, end_row=r0 + 3, end_column=c2)
        p = ws.cell(r0 + 3, c1, pct_formula)
        p.font = Font(size=11, bold=True, color=INST_DORADO)
        p.number_format = PCT
        p.alignment = Alignment(horizontal="left", vertical="center")

    d_row0 = r0 + 4 if pct_formula is not None else r0 + 3
    ws.merge_cells(start_row=d_row0, start_column=c1, end_row=r0 + alto - 1, end_column=c2)
    d = ws.cell(d_row0, c1, desc)
    d.font = Font(size=8, italic=True, color="8A94A0")
    d.alignment = Alignment(wrap_text=True, vertical="top", horizontal="left")

    # Alturas de fila COMPACTAS y explicitas (no depender del default del
    # visor, que fue la causa de los espacios excesivos reportados 2026-09-17)
    alturas = [14, 18, 18, 14, 12, 12]
    for i in range(alto):
        ws.row_dimensions[r0 + i].height = alturas[i] if i < len(alturas) else 12

    _caja(ws, r0, c1, r0 + alto - 1, c2, borde=borde, relleno=CARD_FILL_LIGERO, sombra=False)


# --------------------------------------------------------------------------- #
# PLAN DE FILAS -- calcula UNA sola vez la estructura Componente > Subgrupo >
# Rubro (con o sin nivel de subgrupo, segun si el componente tiene mas de uno)
# y en que fila de SEGUIMIENTO va a quedar cada cosa. EJECUTIVO y SEGUIMIENTO
# leen de este mismo plan, para que nunca queden desincronizados.
# --------------------------------------------------------------------------- #
def construir_plan(edu, orden_comp):
    bloques = []
    for comp in orden_comp:
        grupo = [d for d in edu if d["componente"] == comp]
        if not grupo:
            continue
        subgrupos = {}
        for d in grupo:
            subgrupos.setdefault(d.get("subgrupo", comp), []).append(d)
        tiene_subgrupos = len(subgrupos) > 1
        orden_subg = sorted(subgrupos.keys(),
                            key=lambda s: -sum(x["definitiva"] for x in subgrupos[s]))
        bloques.append({
            "componente": comp,
            "tiene_subgrupos": tiene_subgrupos,
            "subgrupos": [(s, sorted(subgrupos[s], key=lambda x: x["codigo_rubro"]))
                          for s in orden_subg],
        })
    return bloques


def calcular_filas_seguimiento(plan, fila_inicio=2):
    """Simula la escritura de SEGUIMIENTO fila por fila (sin escribir nada) para
    saber de antemano en que fila queda cada rubro y cada subtotal."""
    fila = fila_inicio
    fila_por_rubro = {}
    filas_subtotal_comp = []
    info_por_comp = {}
    for bloque in plan:
        comp = bloque["componente"]
        tiene = bloque["tiene_subgrupos"]
        fila_ini_comp = fila
        filas_para_total_comp = []
        subg_info = []
        for subg, items in bloque["subgrupos"]:
            fila_ini_sub = fila
            for d in items:
                fila_por_rubro[d["cons_ppt"]] = fila
                fila += 1
            fila_fin_sub = fila - 1
            fila_subtotal_subg = None
            if tiene:
                fila_subtotal_subg = fila
                filas_para_total_comp.append(fila)
                fila += 1
            subg_info.append((subg, fila_ini_sub, fila_fin_sub, fila_subtotal_subg))
        fila_fin_comp = fila - 1
        fila_subtotal_comp = fila
        filas_subtotal_comp.append(fila_subtotal_comp)
        fila += 1
        info_por_comp[comp] = {
            "fila_ini_comp": fila_ini_comp, "fila_fin_comp": fila_fin_comp,
            "fila_subtotal_comp": fila_subtotal_comp,
            "filas_para_total_comp": filas_para_total_comp if tiene else None,
            "subgrupos": subg_info,
        }
    return fila_por_rubro, filas_subtotal_comp, info_por_comp, fila


# --------------------------------------------------------------------------- #
# GENERADOR JSON PARA DASHBOARD
# --------------------------------------------------------------------------- #
def generar_json_dashboard(edu, tot, plan, color_por_componente, corte, out_dir):
    """Genera un JSON con la estructura completa de componentes, subgrupos y rubros
    para consumo del dashboard online (React)."""

    def rnd(v):
        """Redondea a 2 decimales para evitar errores de flotante."""
        return round(v, 2) if isinstance(v, float) else v

    # Reconstruir la estructura de componentes desde `plan`
    componentes_data = []
    for bloque in plan:
        comp_nombre = bloque["componente"]
        comp_totales = {"definitiva": 0, "reservado": 0, "comprometido": 0, "obligado": 0, "pagado": 0}

        subgrupos_data = []
        for subg_nombre, rubros_lista in bloque["subgrupos"]:
            subg_totales = {"definitiva": 0, "reservado": 0, "comprometido": 0, "obligado": 0, "pagado": 0}
            rubros_data = []

            for rubro in rubros_lista:
                cons_ppt = rubro.get("cons_ppt", "")
                rubros_data.append({
                    "cons_ppt": cons_ppt,
                    "codigo_rubro": rubro.get("codigo_rubro", ""),
                    "nombre": rubro.get("nombre", ""),
                    "definitiva": rnd(rubro.get("definitiva", 0)),
                    "reservado": rnd(rubro.get("reservado", 0)),
                    "comprometido": rnd(rubro.get("comprometido", 0)),
                    "obligado": rnd(rubro.get("obligado", 0)),
                    "pagado": rnd(rubro.get("pagado", 0)),
                })
                for k in ("definitiva", "reservado", "comprometido", "obligado", "pagado"):
                    subg_totales[k] += rubro.get(k, 0)

            # Redondear totales del subgrupo
            for k in subg_totales:
                subg_totales[k] = rnd(subg_totales[k])
                comp_totales[k] += subg_totales[k]

            subgrupos_data.append({
                "nombre": subg_nombre,
                "totales": subg_totales,
                "rubros": rubros_data,
                "pct_pagado": rnd(subg_totales["pagado"] / subg_totales["definitiva"] * 100 if subg_totales["definitiva"] > 0 else 0),
            })

        # Redondear totales del componente
        for k in comp_totales:
            comp_totales[k] = rnd(comp_totales[k])

        componentes_data.append({
            "nombre": comp_nombre,
            "color_hex": color_por_componente.get(comp_nombre, "CCCCCC"),
            "totales": comp_totales,
            "subgrupos": subgrupos_data,
            "pct_pagado": rnd(comp_totales["pagado"] / comp_totales["definitiva"] * 100 if comp_totales["definitiva"] > 0 else 0),
        })

    # Calcular brechas totales
    brechas = {
        "sin_reservar": {
            "valor": rnd(tot["definitiva"] - tot["reservado"]),
            "pct": rnd((tot["definitiva"] - tot["reservado"]) / tot["definitiva"] * 100 if tot["definitiva"] > 0 else 0),
        },
        "sin_comprometer": {
            "valor": rnd(tot["definitiva"] - tot["comprometido"]),
            "pct": rnd((tot["definitiva"] - tot["comprometido"]) / tot["definitiva"] * 100 if tot["definitiva"] > 0 else 0),
        },
        "sin_obligar": {
            "valor": rnd(tot["definitiva"] - tot["obligado"]),
            "pct": rnd((tot["definitiva"] - tot["obligado"]) / tot["definitiva"] * 100 if tot["definitiva"] > 0 else 0),
        },
    }

    # Construir el JSON
    dashboard_data = {
        "corte": corte.isoformat(),
        "fecha_generacion": datetime.date.today().isoformat(),
        "totales": {
            "definitiva": rnd(tot["definitiva"]),
            "reservado": rnd(tot["reservado"]),
            "comprometido": rnd(tot["comprometido"]),
            "obligado": rnd(tot["obligado"]),
            "pagado": rnd(tot["pagado"]),
        },
        "porcentajes": {
            "reservado": rnd(tot["reservado"] / tot["definitiva"] * 100 if tot["definitiva"] > 0 else 0),
            "comprometido": rnd(tot["comprometido"] / tot["definitiva"] * 100 if tot["definitiva"] > 0 else 0),
            "obligado": rnd(tot["obligado"] / tot["definitiva"] * 100 if tot["definitiva"] > 0 else 0),
            "pagado": rnd(tot["pagado"] / tot["definitiva"] * 100 if tot["definitiva"] > 0 else 0),
        },
        "brechas": brechas,
        "componentes": componentes_data,
    }

    # Guardar JSON
    fn_json = "seguimiento_%s.json" % corte.strftime("%d_%m_%Y")
    out_json = os.path.join(out_dir, fn_json)
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    return out_json


def construir_informe(edu, revisar, m_rubros, m_contratos, mapa_colores, exc,
                      corte, src_path, prev):
    os.makedirs(SALIDAS_DIR, exist_ok=True)
    fn = "Seguimiento Presupuestal Educacion a %s.xlsx" % corte.strftime("%d_%m_%Y")
    out = os.path.join(SALIDAS_DIR, fn)
    wb = Workbook()

    # color de relleno por componente: el sistema lo asigna solo, segun MAPA_COLORES
    # del maestro (componente -> color_hex). El usuario no colorea nada.
    color_por_componente = dict(COLOR_COMPONENTE)
    color_por_componente.update(mapa_colores)

    tot = {k: sum(d[k] for d in edu) for k in
           ("definitiva", "reservado", "comprometido", "obligado", "pagado")}
    by_comp = {}
    for d in edu:
        g = by_comp.setdefault(d["componente"],
                               {"def": 0, "res": 0, "cmp": 0, "obl": 0, "pag": 0, "n": 0})
        g["def"] += d["definitiva"]; g["res"] += d["reservado"]
        g["cmp"] += d["comprometido"]; g["obl"] += d["obligado"]
        g["pag"] += d["pagado"]; g["n"] += 1

    # Blindaje: cualquier componente que NO este en ORDEN_COMPONENTE (nombre
    # nuevo, o con una diferencia de tilde/espacio en el maestro) igual se
    # muestra -- se agrega al final en vez de perderse en silencio, que fue
    # exactamente el bug detectado el 2026-09-16 con "RECURSOS PROPIOS O LIBRE
    # INVERSION" (tenia tilde/espacio distinto y desaparecia de las tablas
    # aunque SI sumaba en el TOTAL).
    orden_comp = list(ORDEN_COMPONENTE)
    huerfanos = sorted(set(by_comp) - set(orden_comp), key=lambda c: -by_comp[c]["def"])
    orden_comp.extend(huerfanos)

    # ===================== HOJA 1 · EJECUTIVO =====================
    ws = wb.active
    ws.title = "EJECUTIVO"

    # Fila donde quedara TOTAL GENERAL en SEGUIMIENTO -- se precalcula (una fila
    # de detalle por rubro + una fila SUBTOTAL por componente con datos, empezando
    # en la fila 2) para poder apuntar las tarjetas del EJECUTIVO ahi con formula,
    # sin tener que escribir SEGUIMIENTO primero.
    SEG_MAXFILA = 5000  # rango amplio para los SUMIF/SUMIFS, cubre crecimiento futuro
    plan = construir_plan(edu, orden_comp)
    fila_seg_por_rubro, filas_subtotal_comp, info_por_comp, FILA_TOTAL_SEG = \
        calcular_filas_seguimiento(plan)

    # Columnas de SEGUIMIENTO (definidas aqui para poder calcular la letra de
    # "Subgrupo" y usarla en SUMIFS desde EJECUTIVO antes de escribir SEGUIMIENTO)
    cols_seg = ["Componente", "Naturaleza", "Codigo rubro", "cons_ppt", "Proyecto / Rubro",
                "Fondo", "Fuente", "Definitivo", "Reservado CDP", "Comprometido RP",
                "Obligado OPS", "Pagado", "Sin reservar", "Sin comprometer", "Sin obligar",
                "% Comp", "% Pag", "Contratos", "Responsable", "Observacion", "Subgrupo"]
    COL_SUBGRUPO = get_column_letter(len(cols_seg))  # ultima columna

    def sumif_seg(col_letra, criterio):
        crit_esc = criterio.replace('"', '""')
        return '=SUMIF(SEGUIMIENTO!$A$2:$A$%d,"%s",SEGUIMIENTO!$%s$2:$%s$%d)' % (
            SEG_MAXFILA, crit_esc, col_letra, col_letra, SEG_MAXFILA)

    def sumifs_seg(col_letra, comp, subg):
        """Suma solo las filas de DETALLE (no de subtotal) de un subgrupo
        especifico dentro de un componente: Componente=comp Y Subgrupo=subg."""
        comp_esc = comp.replace('"', '""')
        subg_esc = subg.replace('"', '""')
        return ('=SUMIFS(SEGUIMIENTO!$%s$2:$%s$%d,'
                'SEGUIMIENTO!$A$2:$A$%d,"%s",'
                'SEGUIMIENTO!$%s$2:$%s$%d,"%s")') % (
            col_letra, col_letra, SEG_MAXFILA,
            SEG_MAXFILA, comp_esc,
            COL_SUBGRUPO, COL_SUBGRUPO, SEG_MAXFILA, subg_esc)

    # Anchos base de columna para el area de tarjetas/graficos (B..T)
    for col_letra in ("B", "C", "D", "F", "G", "H", "J", "K", "L", "N", "O", "P", "R", "S", "T"):
        ws.column_dimensions[col_letra].width = 13
    for col_letra in ("E", "I", "M", "Q"):
        ws.column_dimensions[col_letra].width = 3  # columnas "gap" entre tarjetas

    # --------------------------------------------------------------- #
    # ENCABEZADO INSTITUCIONAL -- logo + titulo centrado + corte
    # --------------------------------------------------------------- #
    ws.row_dimensions[1].height = 26
    ws.row_dimensions[2].height = 20
    ws.row_dimensions[3].height = 18
    ws.row_dimensions[4].height = 16
    try:
        if RUTA_LOGO and os.path.exists(RUTA_LOGO):
            logo = XLImage(RUTA_LOGO)
            logo.width = 66
            logo.height = 66
            ws.add_image(logo, "A1")
    except Exception:
        pass  # si el logo no esta disponible en este equipo, el encabezado sigue sin el

    ws.merge_cells("C1:T1")
    t1 = ws["C1"]
    t1.value = "ALCALDÍA DE RIONEGRO   ·   SECRETARÍA DE EDUCACIÓN"
    t1.font = Font(name=FUENTE_SANS, size=15, bold=True, color=INST_AZUL)
    t1.alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("C2:T2")
    t2 = ws["C2"]
    t2.value = "INFORME DE EJECUCIÓN PRESUPUESTAL — RESUMEN EJECUTIVO"
    t2.font = Font(name=FUENTE_SANS, size=11, bold=True, color=INST_DORADO)
    t2.alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("C3:T3")
    t3 = ws["C3"]
    t3.value = "Corte: %s" % _fecha_es(corte)
    t3.font = Font(name=FUENTE_SANS, size=10, bold=True, color="404040")
    t3.alignment = Alignment(horizontal="center", vertical="center")

    ws.merge_cells("C4:T4")
    t4 = ws["C4"]
    t4.value = "Fuente: %s   |   Generado: %s   |   Rubros: %d" % (
        os.path.basename(src_path), datetime.date.today().isoformat(), len(edu))
    t4.font = Font(size=8, italic=True, color="8A94A0")
    t4.alignment = Alignment(horizontal="center", vertical="center")

    # linea institucional bajo el encabezado
    for col_i in range(1, 21):
        ws.cell(4, col_i).border = Border(bottom=Side(style="medium", color=INST_DORADO))

    # --------------------------------------------------------------- #
    # 5 TARJETAS KPI -- Definitivo, Reservado, Comprometido, Obligado, Pagado
    # Todo el valor y el % son formula/referencia, nada escrito a mano.
    # --------------------------------------------------------------- #
    ANCHO_CARD, ALTO_CARD, GAP_COLS = 3, 6, 1
    col0 = 2  # columna B
    r = 6
    kpi_specs = [
        ("PRESUPUESTO\nDEFINITIVO", "H", False, "Presupuesto disponible durante la vigencia."),
        ("RESERVADO\nCDP", "I", True, "Cuenta con Certificado de Disponibilidad Presupuestal."),
        ("COMPROMETIDO\nRP", "J", True, "Respaldado por Registro Presupuestal (contrato/obligación)."),
        ("OBLIGADO\nOPS", "K", True, "Bien o servicio recibido; obligación exigible."),
        ("PAGADO", "L", True, "Giro efectivo realizado a la fecha de corte."),
    ]
    fila_valor = r + 1
    kpi_cell = {}   # etiqueta corta -> coordenada de la celda de VALOR
    def_coord = None
    col_actual = col0
    for label, col_seg, con_pct, desc in kpi_specs:
        valor_formula = "=SEGUIMIENTO!%s%d" % (col_seg, FILA_TOTAL_SEG)
        val_coord = ws.cell(fila_valor, col_actual).coordinate
        pct_formula = "=IFERROR(%s/%s,0)" % (val_coord, def_coord) if con_pct else None
        _tarjeta_kpi(ws, r, col_actual, ANCHO_CARD, ALTO_CARD, label.replace("\n", " "),
                    valor_formula, pct_formula, desc)
        if def_coord is None:
            def_coord = val_coord
        kpi_cell[col_seg] = val_coord
        col_actual += ANCHO_CARD + GAP_COLS
    r += ALTO_CARD + 1

    # --------------------------------------------------------------- #
    # BRECHA DE EJECUCION -- 3 tarjetas, SIEMPRE contra el Presupuesto
    # Definitivo (confirmado con el usuario 2026-09-17): Sin reservar =
    # Definitivo-Reservado; Sin comprometer = Definitivo-Comprometido;
    # Sin obligar = Definitivo-Obligado. (Antes "Sin comprometer" y "Sin
    # obligar" se calculaban en cascada contra la ETAPA anterior -- ver
    # auditoria FASE 1 del 2026-09-17. Esa logica en cascada se conserva
    # SIN TOCAR en la hoja SEGUIMIENTO, que no se modifica en este cambio.)
    # --------------------------------------------------------------- #
    ws.cell(r, 1, "BRECHA DE EJECUCIÓN").font = Font(size=11, bold=True, color=INST_AZUL)
    r += 1
    def_c, res_c, cmp_c, obl_c = kpi_cell["H"], kpi_cell["I"], kpi_cell["J"], kpi_cell["K"]
    brecha_specs = [
        ("SIN RESERVAR", "=%s-%s" % (def_c, res_c),
         "Presupuesto definitivo que aún no tiene CDP (Certificado de Disponibilidad Presupuestal)."),
        ("SIN COMPROMETER", "=%s-%s" % (def_c, cmp_c),
         "Presupuesto definitivo que aún no está respaldado por un RP (Registro Presupuestal)."),
        ("SIN OBLIGAR", "=%s-%s" % (def_c, obl_c),
         "Presupuesto definitivo cuyo bien o servicio aún no ha sido recibido/certificado (OPS)."),
    ]
    col_actual = col0
    brecha_cell = {}
    for label, formula, desc in brecha_specs:
        val_coord = ws.cell(r + 1, col_actual).coordinate
        pct_formula = "=IFERROR(%s/%s,0)" % (val_coord, def_c)
        _tarjeta_kpi(ws, r, col_actual, ANCHO_CARD, ALTO_CARD, label, formula, pct_formula, desc,
                    borde=CARD_BORDE_INST)
        brecha_cell[label] = val_coord
        col_actual += ANCHO_CARD + GAP_COLS
    r += ALTO_CARD + 1

    # Se reserva aqui la fila ancla de los graficos (quedan mas abajo en el
    # layout visual gracias a esta ancla), pero se CONSTRUYEN mas adelante en
    # el codigo, una vez que la tabla SEGUIMIENTO POR COMPONENTE ya asigno sus
    # filas de resumen (filas_comp_ejecutivo) -- el grafico de distribucion
    # necesita conocerlas para poder referenciarlas.
    fila_graficos = r

    # Los graficos miden 8.5 cm (~241pt) de alto. Se fija la altura de cada
    # fila reservada a 15pt EXPLICITAMENTE (en vez de heredar el default del
    # visor, que fue la causa de los espacios vacios reportados 2026-09-17):
    # 241pt / 15pt ~= 16 filas -- se reservan 16 + 1 de margen.
    FILAS_RESERVA_GRAFICOS = 17
    for i in range(FILAS_RESERVA_GRAFICOS):
        ws.row_dimensions[fila_graficos + i].height = 15
    r = fila_graficos + FILAS_RESERVA_GRAFICOS

    # --------------------------------------------------------------- #
    # LECTURA EJECUTIVA -- mensajes cortos, 100% generados por formula
    # (concatenacion de texto con TEXT() sobre las celdas de arriba).
    # --------------------------------------------------------------- #
    ws.cell(r, 1, "LECTURA EJECUTIVA").font = Font(size=11, bold=True, color=INST_AZUL)
    r += 1
    # Coordenada de % de cada tarjeta KPI: ver _tarjeta_kpi -> label(r0),
    # valor(r0+1:r0+2), pct(r0+3). r0 de las tarjetas KPI fue 6.
    fila_pct_kpi = 6 + 3
    col_map = {"H": col0, "I": col0 + (ANCHO_CARD + GAP_COLS), "J": col0 + 2 * (ANCHO_CARD + GAP_COLS),
              "K": col0 + 3 * (ANCHO_CARD + GAP_COLS), "L": col0 + 4 * (ANCHO_CARD + GAP_COLS)}
    pct_cmp_coord = ws.cell(fila_pct_kpi, col_map["J"]).coordinate
    pct_pag_coord = ws.cell(fila_pct_kpi, col_map["L"]).coordinate
    mensajes = [
        '="El "&TEXT(%s,"0.0%%")&" del presupuesto definitivo está comprometido (RP)."' % pct_cmp_coord,
        '="El "&TEXT(%s,"0.0%%")&" del presupuesto definitivo ha sido efectivamente pagado."' % pct_pag_coord,
        '="La brecha sin comprometer, respecto al total, es de $"&TEXT(%s,"#,##0")&"."' % brecha_cell["SIN COMPROMETER"],
    ]
    for m in mensajes:
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=10)
        c = ws.cell(r, 1, m)
        c.font = Font(size=10, color="333333")
        c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
        c.border = Border(left=Side(style="thick", color=INST_DORADO))
        r += 1
    r += 2

    ws.cell(r, 1, "SEGUIMIENTO POR COMPONENTE").font = SUB_FONT
    r += 1
    # Tabla mejorada con todas las columnas -- TODO es formula: cada celda se
    # puede seleccionar en Excel y ver de donde sale (SUMIF contra SEGUIMIENTO,
    # o resta/division de otra celda de esta misma tabla).
    cols_comp = ["Componente", "Ppto. Definitivo", "Reservado CDP", "Comprometido RP",
                 "Obligado OPS", "Pagado", "% Pag", "Sin Reservar", "Sin Comprometer", "Sin Obligar", "% Comp"]
    widths_comp = [35, 16, 14, 16, 14, 14, 10, 14, 16, 14, 10]
    _hdr(ws, cols_comp, widths_comp, fila=r)
    r += 1

    # summaryBelow=False: el resumen (componente) va ARRIBA, el detalle (rubros)
    # abajo -- asi el "+" para expandir queda pegado al nombre del componente,
    # igual que el arbol Proyecto -> hijos del boceto del usuario.
    ws.sheet_properties.outlinePr.summaryBelow = False

    def escribir_fila_valores(fila_xl, formulas_hijkl, nivel):
        """Escribe Definitivo..Pagado (formulas_hijkl = 5 formulas/valores para
        cols B-F) + los gaps/porcentajes derivados (formulas locales), y aplica
        el outlineLevel dado (0 = fila siempre visible)."""
        for col_idx, val in zip(range(2, 7), formulas_hijkl):
            ws.cell(fila_xl, col_idx, val).number_format = MON
        ws.cell(fila_xl, 7, "=IFERROR(F%d/B%d,0)" % (fila_xl, fila_xl)).number_format = PCT
        # Brechas SIEMPRE contra el Definitivo (B), confirmado 2026-09-17 --
        # antes "Sin Comprometer"/"Sin Obligar" eran en cascada (C-D, D-E).
        ws.cell(fila_xl, 8, "=B%d-C%d" % (fila_xl, fila_xl)).number_format = MON
        ws.cell(fila_xl, 9, "=B%d-D%d" % (fila_xl, fila_xl)).number_format = MON
        ws.cell(fila_xl, 10, "=B%d-E%d" % (fila_xl, fila_xl)).number_format = MON
        ws.cell(fila_xl, 11, "=IFERROR(D%d/B%d,0)" % (fila_xl, fila_xl)).number_format = PCT
        if nivel > 0:
            ws.row_dimensions[fila_xl].outlineLevel = nivel
            ws.row_dimensions[fila_xl].hidden = True

    r_ini_tabla = r
    filas_comp_ejecutivo = []  # solo las filas de RESUMEN de componente (para el TOTAL)
    for bloque in plan:
        comp = bloque["componente"]
        tiene = bloque["tiene_subgrupos"]
        fc = color_por_componente.get(comp, "FFFFFF")

        # --- Nivel 0: fila resumen del COMPONENTE (siempre visible) ---
        ws.cell(r, 1, comp)
        if fc != "FFFFFF":
            for col_idx in range(1, len(cols_comp) + 1):
                ws.cell(r, col_idx).fill = PatternFill("solid", fgColor=fc)
        escribir_fila_valores(r, [sumif_seg(cl, comp) for cl in ("H", "I", "J", "K", "L")], nivel=0)
        filas_comp_ejecutivo.append(r)
        r += 1

        for subg, items in bloque["subgrupos"]:
            if tiene:
                # --- Nivel 1: fila resumen del SUBGRUPO (oculta; aparece al
                # expandir el componente) ---
                ws.cell(r, 1, "   " + subg).font = Font(bold=True, size=9)
                if fc != "FFFFFF":
                    ws.cell(r, 1).fill = PatternFill("solid", fgColor=fc)
                escribir_fila_valores(r, [sumifs_seg(cl, comp, subg) for cl in ("H", "I", "J", "K", "L")], nivel=1)
                r += 1

            # --- Nivel 2 (o 1 si el componente no tiene subgrupos): un rubro
            # por fila, formula apuntando a su fila exacta en SEGUIMIENTO ---
            nivel_rubro = 2 if tiene else 1
            for d in items:
                fila_seg = fila_seg_por_rubro[d["cons_ppt"]]
                nombre = m_rubros.get(d["cons_ppt"], {}).get("proyecto_nombre") or d["nombre"]
                indent = "          " if tiene else "     "
                ws.cell(r, 1, indent + nombre).font = Font(italic=True, size=9, color="595959")
                if fc != "FFFFFF":
                    ws.cell(r, 1).fill = PatternFill("solid", fgColor=fc)
                escribir_fila_valores(r, ["=SEGUIMIENTO!%s%d" % (cl, fila_seg) for cl in ("H", "I", "J", "K", "L")],
                                      nivel=nivel_rubro)
                r += 1
    r_fin_tabla = r - 1

    # TOTAL = suma SOLO de las filas de RESUMEN de componente (no del detalle,
    # que ya esta contado dentro de cada SUMIF del resumen -- sumar tambien el
    # detalle duplicaria los valores).
    ws.cell(r, 1, "TOTAL EDUCACIÓN").font = SUB_FONT
    for j in range(1, len(cols_comp) + 1):
        ws.cell(r, j).fill = SUB_FILL
    refs_comp = lambda col: ",".join("%s%d" % (col, f) for f in filas_comp_ejecutivo)
    for col_idx, col_letra in ((2, "B"), (3, "C"), (4, "D"), (5, "E"), (6, "F")):
        ws.cell(r, col_idx, "=SUM(%s)" % refs_comp(col_letra))
        ws.cell(r, col_idx).number_format = MON
        ws.cell(r, col_idx).font = SUB_FONT
    ws.cell(r, 7, "=IFERROR(F%d/B%d,0)" % (r, r)).number_format = PCT
    ws.cell(r, 7).font = SUB_FONT
    ws.cell(r, 8, "=B%d-C%d" % (r, r)).number_format = MON
    ws.cell(r, 8).font = SUB_FONT
    ws.cell(r, 9, "=B%d-D%d" % (r, r)).number_format = MON
    ws.cell(r, 9).font = SUB_FONT
    ws.cell(r, 10, "=B%d-E%d" % (r, r)).number_format = MON
    ws.cell(r, 10).font = SUB_FONT
    ws.cell(r, 11, "=IFERROR(D%d/B%d,0)" % (r, r)).number_format = PCT
    ws.cell(r, 11).font = SUB_FONT
    r_total_edu = r
    r += 2

    # --------------------------------------------------------------- #
    # GRAFICO 1: "Ejecución por etapa" -- datos ocultos dentro de la MISMA
    # hoja EJECUTIVO, en columnas lejanas (no se crea ninguna hoja nueva ni
    # se toca otra hoja). Solo formulas que referencian celdas ya escritas.
    # Ancla en fila_graficos, reservada justo debajo de las tarjetas de brecha.
    # --------------------------------------------------------------- #
    COL_HELP_ETAPA = 28   # AB
    ws.cell(1, COL_HELP_ETAPA, "Etapa")
    ws.cell(1, COL_HELP_ETAPA + 1, "Valor")
    etapas = [("Presupuesto Definitivo", def_c), ("Reservado CDP", res_c),
             ("Comprometido RP", cmp_c), ("Obligado OPS", obl_c), ("Pagado", kpi_cell["L"])]
    for i, (nombre, celda) in enumerate(etapas, start=2):
        ws.cell(i, COL_HELP_ETAPA, nombre)
        vc = ws.cell(i, COL_HELP_ETAPA + 1, "=%s" % celda)
        vc.number_format = MON
    ws.column_dimensions[get_column_letter(COL_HELP_ETAPA)].hidden = True
    ws.column_dimensions[get_column_letter(COL_HELP_ETAPA + 1)].hidden = True

    # Config deliberadamente simple/robusta: un solo color solido por serie,
    # sin colorear punto por punto y sin trucos de ejes -- esas combinaciones
    # han mostrado renderizar en blanco en algunos visores (reportado por el
    # usuario 2026-09-17). Un solo color solido es ademas lo que pide el
    # prompt ("un color principal, no un color distinto por categoria").
    chart_etapa = BarChart()
    chart_etapa.type = "col"
    chart_etapa.grouping = "standard"
    chart_etapa.style = None
    chart_etapa.title = "Ejecución por etapa"
    chart_etapa.y_axis.title = None
    chart_etapa.x_axis.title = None
    chart_etapa.y_axis.delete = False
    chart_etapa.x_axis.delete = False
    chart_etapa.legend = None
    chart_etapa.gapWidth = 50
    chart_etapa.height = 8.5
    chart_etapa.width = 15.5
    data_etapa = Reference(ws, min_col=COL_HELP_ETAPA + 1, min_row=1, max_row=6)
    cats_etapa = Reference(ws, min_col=COL_HELP_ETAPA, min_row=2, max_row=6)
    chart_etapa.add_data(data_etapa, titles_from_data=True)
    chart_etapa.set_categories(cats_etapa)
    chart_etapa.series[0].graphicalProperties.solidFill = INST_AZUL
    chart_etapa.series[0].graphicalProperties.line.noFill = True
    ws.add_chart(chart_etapa, "B%d" % fila_graficos)

    # --------------------------------------------------------------- #
    # GRAFICO 2: DISTRIBUCION POR COMPONENTE -- barras horizontales, un solo
    # color, ordenadas de mayor a menor (el orden se fija al generar el
    # informe; los VALORES siguen siendo formula/referencia a la tabla de
    # arriba, ya con sus filas de resumen asignadas en filas_comp_ejecutivo).
    # --------------------------------------------------------------- #
    COL_HELP_COMP = 31  # AE
    ws.cell(1, COL_HELP_COMP, "Componente")
    ws.cell(1, COL_HELP_COMP + 1, "Definitivo")
    # Orden ASCENDENTE (menor primero): un grafico de barras horizontales
    # dibuja la primera categoria abajo, asi que con este orden el de mayor
    # valor queda arriba -- sin necesidad de invertir ejes (esa combinacion
    # broke el render en algunos visores, ver nota mas abajo).
    comp_ordenados = sorted(zip(plan, filas_comp_ejecutivo),
                            key=lambda x: by_comp[x[0]["componente"]]["def"])
    for i, (bloque, fila_r) in enumerate(comp_ordenados, start=2):
        nombre_corto = bloque["componente"]
        ws.cell(i, COL_HELP_COMP, nombre_corto)
        ws.cell(i, COL_HELP_COMP + 1, "=B%d" % fila_r).number_format = MON
    fila_fin_comp_help = 1 + len(comp_ordenados)
    ws.column_dimensions[get_column_letter(COL_HELP_COMP)].hidden = True
    ws.column_dimensions[get_column_letter(COL_HELP_COMP + 1)].hidden = True

    chart_comp = BarChart()
    chart_comp.type = "bar"  # horizontal
    chart_comp.grouping = "standard"
    chart_comp.style = None
    chart_comp.title = "Distribución por componente (Definitivo)"
    chart_comp.y_axis.title = None
    chart_comp.x_axis.title = None
    chart_comp.y_axis.delete = False
    chart_comp.x_axis.delete = False
    chart_comp.legend = None
    chart_comp.height = 8.5
    chart_comp.width = 15.5
    chart_comp.gapWidth = 40
    data_comp = Reference(ws, min_col=COL_HELP_COMP + 1, min_row=1, max_row=fila_fin_comp_help)
    cats_comp = Reference(ws, min_col=COL_HELP_COMP, min_row=2, max_row=fila_fin_comp_help)
    chart_comp.add_data(data_comp, titles_from_data=True)
    chart_comp.set_categories(cats_comp)
    chart_comp.series[0].graphicalProperties.solidFill = INST_AZUL
    chart_comp.series[0].graphicalProperties.line.noFill = True
    ws.add_chart(chart_comp, "L%d" % fila_graficos)

    # bloque por fuente (participacion) -- % sobre el TOTAL EDUCACIÓN de arriba
    ws.cell(r, 1, "PARTICIPACION POR FUENTE").font = SUB_FONT
    r += 1
    _hdr(ws, ["Fuente / componente", "Definitivo", "% del total"], [40, 18, 12], fila=r)
    r += 1
    for comp in orden_comp:
        if comp not in by_comp:
            continue
        ws.cell(r, 1, comp)
        ws.cell(r, 2, sumif_seg("H", comp)).number_format = MON
        ws.cell(r, 3, "=IFERROR(B%d/$B$%d,0)" % (r, r_total_edu)).number_format = PCT
        r += 1
    r += 1

    # bloque por concepto SGP (comprometido)
    ws.cell(r, 1, "CONCEPTO SGP + NACION (comprometido)").font = SUB_FONT
    r += 1
    _hdr(ws, ["Concepto", "Comprometido"], [40, 20], fila=r)
    r += 1
    sgp_keys = ["PRESTACION DEL SERVICIO", "CALIDAD MATRICULA", "CALIDAD GRATUIDAD",
                "SGP - PGN - PAE"]
    r_sgp_ini = r
    for comp in sgp_keys:
        if comp in by_comp:
            ws.cell(r, 1, comp)
            ws.cell(r, 2, sumif_seg("J", comp)).number_format = MON
            r += 1
    r_sgp_fin = r - 1
    ws.cell(r, 1, "TOTAL SGP + Nacion").font = SUB_FONT
    if r_sgp_fin >= r_sgp_ini:
        ws.cell(r, 2, "=SUM(B%d:B%d)" % (r_sgp_ini, r_sgp_fin))
    else:
        ws.cell(r, 2, 0)
    ws.cell(r, 2).number_format = MON
    ws.cell(r, 2).font = SUB_FONT
    r += 2

    # alertas
    ws.cell(r, 1, "ALERTAS DEL CORTE").font = SUB_FONT
    r += 1
    _hdr(ws, ["Severidad", "Descripcion", "Evidencia", "Accion"], [12, 44, 50, 40], fila=r)
    r += 1
    alertas = _generar_alertas(edu, revisar, m_contratos, tot)
    for a in alertas:
        for j, v in enumerate(a, start=1):
            ws.cell(r, j, v).alignment = WRAP
        if a[0] in ("ALTA", "CRITICA"):
            for j in range(1, 5):
                ws.cell(r, j).fill = ALERT_FILL
        r += 1
    if not alertas:
        ws.cell(r, 1, "Sin alertas en este corte.")

    # Resumen de contratos por cons_ppt (para la columna "Contratos" de SEGUIMIENTO)
    contratos_por_cons = {}
    for c in m_contratos:
        cp = c.get("cons_ppt")
        if cp:
            contratos_por_cons.setdefault(cp, []).append(c)

    def resumen_contratos(cons_ppt):
        lst = contratos_por_cons.get(cons_ppt)
        if not lst:
            return "Sin contratos"
        suma_cmp = sum(_n(c.get("comprometido")) for c in lst)
        return "%d contrato%s | $%s comprometido" % (
            len(lst), "s" if len(lst) != 1 else "", format(suma_cmp, ",.0f"))

    # ===================== HOJA 2 · SEGUIMIENTO =====================
    ws2 = wb.create_sheet("SEGUIMIENTO")
    ws2.sheet_properties.outlinePr.summaryBelow = True
    ws2.sheet_properties.outlinePr.applyStyles = True
    cols = cols_seg
    _hdr(ws2, cols, [26, 18, 26, 9, 44, 15, 32, 16, 15, 16, 15, 15, 15, 15, 14, 9, 9, 28, 20, 40, 45])

    def fila_vacia(etiqueta, formulas_hijkl):
        """Fila de SUBTOTAL (de subgrupo o de componente): etiqueta en col A,
        formulas de suma en H-L, gaps/pct derivados, columnas de detalle vacias."""
        fila_row = ["" for _ in cols]
        fila_row[0] = etiqueta
        for i, v in enumerate(formulas_hijkl):
            fila_row[7 + i] = v  # H=indice 7
        return fila_row

    fila = 2
    for bloque in plan:
        comp = bloque["componente"]
        tiene = bloque["tiene_subgrupos"]
        fc = color_por_componente.get(comp, "FFFFFF")
        fila_ini_comp = fila

        for subg, items in bloque["subgrupos"]:
            fila_ini_sub = fila
            for d in items:
                mr = m_rubros.get(d["cons_ppt"], {})
                defi, res, cmp_, obl, pag = (d["definitiva"], d["reservado"],
                                             d["comprometido"], d["obligado"], d["pagado"])
                ws2.append([comp, d["grupo_naturaleza"], d["codigo_rubro"], d["cons_ppt"],
                            mr.get("proyecto_nombre") or d["nombre"], d["fondo"], d["fuente"],
                            defi, res, cmp_, obl, pag,
                            "=H%d-I%d" % (fila, fila), "=I%d-J%d" % (fila, fila), "=J%d-K%d" % (fila, fila),
                            "=IFERROR(J%d/H%d,\"\")" % (fila, fila), "=IFERROR(L%d/H%d,\"\")" % (fila, fila),
                            resumen_contratos(d["cons_ppt"]),
                            mr.get("responsable", ""), mr.get("observacion", ""), subg])
                if fc != "FFFFFF":
                    ws2.cell(fila, 1).fill = PatternFill("solid", fgColor=fc)
                for cc in range(8, 16):
                    ws2.cell(fila, cc).number_format = MON
                for cc in (16, 17):
                    ws2.cell(fila, cc).number_format = PCT
                # Nivel 2 si el componente tiene subgrupos (se ve al expandir
                # componente Y subgrupo), nivel 1 si no los tiene.
                ws2.row_dimensions[fila].outlineLevel = 2 if tiene else 1
                ws2.row_dimensions[fila].hidden = True
                fila += 1
            fila_fin_sub = fila - 1

            if tiene:
                ws2.append(fila_vacia("   SUBTOTAL " + subg, [
                    "=SUM(H%d:H%d)" % (fila_ini_sub, fila_fin_sub),
                    "=SUM(I%d:I%d)" % (fila_ini_sub, fila_fin_sub),
                    "=SUM(J%d:J%d)" % (fila_ini_sub, fila_fin_sub),
                    "=SUM(K%d:K%d)" % (fila_ini_sub, fila_fin_sub),
                    "=SUM(L%d:L%d)" % (fila_ini_sub, fila_fin_sub)]))
                ws2.cell(fila, 13, "=H%d-I%d" % (fila, fila)).number_format = MON
                ws2.cell(fila, 14, "=I%d-J%d" % (fila, fila)).number_format = MON
                ws2.cell(fila, 15, "=J%d-K%d" % (fila, fila)).number_format = MON
                ws2.cell(fila, 16, "=IFERROR(J%d/H%d,0)" % (fila, fila)).number_format = PCT
                ws2.cell(fila, 17, "=IFERROR(L%d/H%d,0)" % (fila, fila)).number_format = PCT
                for cc in range(1, len(cols) + 1):
                    ws2.cell(fila, cc).font = Font(italic=True, bold=True, size=9)
                    if fc != "FFFFFF":
                        ws2.cell(fila, cc).fill = PatternFill("solid", fgColor=fc)
                for cc in range(8, 13):
                    ws2.cell(fila, cc).number_format = MON
                ws2.row_dimensions[fila].outlineLevel = 1
                ws2.row_dimensions[fila].hidden = True
                fila += 1

        fila_fin_comp = fila - 1
        info = info_por_comp[comp]
        if tiene:
            refs_sub = lambda col: ",".join("%s%d" % (col, f) for f in info["filas_para_total_comp"])
            formulas_comp = [
                "=SUM(%s)" % refs_sub("H"), "=SUM(%s)" % refs_sub("I"),
                "=SUM(%s)" % refs_sub("J"), "=SUM(%s)" % refs_sub("K"), "=SUM(%s)" % refs_sub("L")]
        else:
            formulas_comp = [
                "=SUM(H%d:H%d)" % (fila_ini_comp, fila_fin_comp),
                "=SUM(I%d:I%d)" % (fila_ini_comp, fila_fin_comp),
                "=SUM(J%d:J%d)" % (fila_ini_comp, fila_fin_comp),
                "=SUM(K%d:K%d)" % (fila_ini_comp, fila_fin_comp),
                "=SUM(L%d:L%d)" % (fila_ini_comp, fila_fin_comp)]
        ws2.append(fila_vacia("SUBTOTAL " + comp, formulas_comp))
        ws2.cell(fila, 13, "=H%d-I%d" % (fila, fila)).number_format = MON
        ws2.cell(fila, 14, "=I%d-J%d" % (fila, fila)).number_format = MON
        ws2.cell(fila, 15, "=J%d-K%d" % (fila, fila)).number_format = MON
        ws2.cell(fila, 16, "=IFERROR(J%d/H%d,0)" % (fila, fila)).number_format = PCT
        ws2.cell(fila, 17, "=IFERROR(L%d/H%d,0)" % (fila, fila)).number_format = PCT
        for cc in range(1, len(cols) + 1):
            ws2.cell(fila, cc).font = SUB_FONT
            ws2.cell(fila, cc).fill = SUB_FILL
        for cc in range(8, 13):
            ws2.cell(fila, cc).number_format = MON
        assert fila == info["fila_subtotal_comp"], "Plan desincronizado en %s: %d vs %d" % (
            comp, fila, info["fila_subtotal_comp"])
        fila += 1

    refs = lambda col: ",".join("%s%d" % (col, f) for f in filas_subtotal_comp)
    ws2.append(fila_vacia("TOTAL GENERAL", [
        "=SUM(%s)" % refs("H"), "=SUM(%s)" % refs("I"), "=SUM(%s)" % refs("J"),
        "=SUM(%s)" % refs("K"), "=SUM(%s)" % refs("L")]))
    ws2.cell(fila, 13, "=H%d-I%d" % (fila, fila)).number_format = MON
    ws2.cell(fila, 14, "=I%d-J%d" % (fila, fila)).number_format = MON
    ws2.cell(fila, 15, "=J%d-K%d" % (fila, fila)).number_format = MON
    ws2.cell(fila, 16, "=IFERROR(J%d/H%d,0)" % (fila, fila)).number_format = PCT
    ws2.cell(fila, 17, "=IFERROR(L%d/H%d,0)" % (fila, fila)).number_format = PCT
    for cc in range(1, len(cols) + 1):
        ws2.cell(fila, cc).font = Font(bold=True, size=11)
        ws2.cell(fila, cc).fill = TOT_FILL
    for cc in range(8, 13):
        ws2.cell(fila, cc).number_format = MON
    assert fila == FILA_TOTAL_SEG, "FILA_TOTAL_SEG precalculada (%d) no coincide con la real (%d)" % (FILA_TOTAL_SEG, fila)
    ws2.freeze_panes = "E2"
    ws2.auto_filter.ref = "A1:%s1" % get_column_letter(len(cols))

    # ===================== HOJA 3 · CONTRATOS =====================
    ws3 = wb.create_sheet("CONTRATOS")
    cols = ["Nro contrato", "Contratista", "Objeto", "cons_ppt", "Proyecto / Rubro",
            "Componente", "Fuente", "Valor contrato", "Comprometido", "Obligado",
            "Pagado", "Saldo x pagar", "% Ejec", "CDP", "RP", "Vig Futura", "Estado",
            "Match", "Suscripcion", "Supervisor", "Observacion"]
    _hdr(ws3, cols, [16, 26, 44, 9, 40, 24, 30, 16, 15, 15, 15, 15, 9, 12, 12, 10, 22, 26, 13, 22, 40])
    edu_by_cons = {d["cons_ppt"]: d for d in edu}
    fila = 2

    MATCH_LABELS = {
        "match_unico_por_cdp": "OK - match unico por # de CDP",
        "match_por_cdp_y_codigo": "OK - match por CDP + codigo (CDP compartido)",
        "cdp_no_encontrado_en_hacienda": "CDP no aparece en el Hacienda de este corte",
        "vigencia_futura_otro_periodo": "Vigencia futura de otro periodo (normal)",
    }

    def match_label(c):
        m = c.get("match", "")
        if m.startswith("ambiguo:"):
            return "AMBIGUO -- CDP compartido por: " + m.split(":", 1)[1]
        return MATCH_LABELS.get(m, m or "(contrato manual, sin CDP-CRP)")

    if not m_contratos:
        ws3.cell(2, 1, "Aun no hay contratos cargados. Agreguelos en la hoja "
                       "CONTRATOS de seguimiento_manual_educacion.xlsx y vuelva a generar.")
    else:
        # ordenar: primero los de Educacion confirmada (por componente), luego
        # los de otras Secretarias, luego vigencias futuras (normal, informativo),
        # y al final los ambiguos/sin match (los unicos que de verdad requieren revision)
        def grupo_de(c):
            cons = c.get("cons_ppt")
            m = c.get("match", "")
            if cons and cons in edu_by_cons:
                return 0
            if cons:
                return 1  # otra secretaria -- resuelto, informativo
            if m == "vigencia_futura_otro_periodo":
                return 2  # normal, no es un problema
            return 3  # ambiguo / cdp_no_encontrado -- requiere revision

        def keyf(c):
            cons = c.get("cons_ppt")
            d = edu_by_cons.get(cons)
            grp = grupo_de(c)
            comp = d["componente"] if d else "zzz"
            return (grp, ORDEN_COMPONENTE.index(comp) if comp in ORDEN_COMPONENTE else 99,
                    cons or "", str(c.get("nro_contrato") or ""))

        for c in sorted(m_contratos, key=keyf):
            cons = c.get("cons_ppt")
            d = edu_by_cons.get(cons) if cons else None
            grp = grupo_de(c)
            if d:
                comp = d["componente"]
            elif grp == 1:
                comp = "(otra Secretaria)"
            elif grp == 2:
                comp = "(vigencia futura -- otro periodo)"
            else:
                comp = "(SIN RESOLVER -- revisar)"
            proy = (m_rubros.get(cons, {}).get("proyecto_nombre") if cons else None) or (d["nombre"] if d else "")
            fuente = d["fuente"] if d else ""
            val = _n(c.get("valor_contrato"))
            cm = _n(c.get("comprometido"))
            ob = _n(c.get("obligado"))
            pg = _n(c.get("pagado"))
            vig_fut = c.get("vigencia_futura", "")
            ws3.append([c.get("nro_contrato", ""), c.get("contratista", ""),
                        c.get("objeto_contrato", ""), cons or "", proy, comp, fuente,
                        val, cm, ob, pg, val - pg,
                        pct(pg, val) if val else "—",
                        c.get("cdp", ""), c.get("rp", ""), vig_fut or "", c.get("estado", ""),
                        match_label(c),
                        c.get("fecha_suscripcion", ""), c.get("supervisor", ""),
                        c.get("observacion", "")])
            if grp == 3:
                for cc in range(1, len(cols) + 1):
                    ws3.cell(fila, cc).fill = ALERT_FILL  # ambiguo/sin match -- requiere revision
            for cc in range(8, 13):
                ws3.cell(fila, cc).number_format = MON
            if isinstance(ws3.cell(fila, 13).value, float):
                ws3.cell(fila, 13).number_format = PCT
            fila += 1

        # conciliacion rubro vs contratos -- SOLO sobre contratos con match
        # confirmado a un cons_ppt de Educacion (nunca sobre ambiguos/sin match)
        fila += 1
        ws3.cell(fila, 1, "CONCILIACION RUBRO vs CONTRATOS (solo contratos con match confirmado)").font = SUB_FONT
        fila += 1
        _hdr(ws3, ["cons_ppt", "Proyecto / Rubro", "Comprometido rubro (Hacienda)",
                   "Suma contratos", "Diferencia", "Nota"],
             [10, 44, 24, 20, 18, 40], fila=fila)
        fila += 1
        por_cons = {}
        for c in m_contratos:
            cons = c.get("cons_ppt")
            if cons and cons in edu_by_cons:
                por_cons.setdefault(cons, 0)
                por_cons[cons] += _n(c.get("comprometido"))
        for cons, suma in sorted(por_cons.items()):
            d = edu_by_cons[cons]
            rub_cmp = d["comprometido"]
            dif = rub_cmp - suma
            nota = ("OK" if abs(dif) < 1 else
                    "Faltan contratos por registrar, o parte del comprometido no tiene CDP-CRP" if dif > 0 else
                    "Contratos exceden el comprometido del rubro — revisar")
            ws3.append([cons, d["nombre"], rub_cmp, suma, dif, nota])
            for cc in (3, 4, 5):
                ws3.cell(fila, cc).number_format = MON
            if abs(dif) >= 1:
                ws3.cell(fila, 5).fill = ALERT_FILL
                ws3.cell(fila, 6).fill = ALERT_FILL
            fila += 1

        # resumen de calidad del cruce (para que el usuario vea de un vistazo
        # cuantos contratos quedaron sin resolver)
        fila += 1
        ws3.cell(fila, 1, "CALIDAD DEL CRUCE CDP-CRP").font = SUB_FONT
        fila += 1
        from collections import Counter as _Counter
        cont_match = _Counter()
        for c in m_contratos:
            m = c.get("match", "manual")
            if m.startswith("ambiguo"):
                m = "ambiguo"
            cont_match[m] += 1
        for m, n in cont_match.most_common():
            ws3.cell(fila, 1, MATCH_LABELS.get(m, m))
            ws3.cell(fila, 2, n)
            fila += 1
    ws3.freeze_panes = "D2"

    # ===================== HOJA 4 · NOTAS =====================
    wn = wb.create_sheet("NOTAS")
    _hdr(wn, ["Tema", "Explicacion"], [26, 104])
    filas_n = [
        ("Corte", corte.strftime("%d/%m/%Y") + " — tomado del nombre del archivo de Hacienda."),
        ("Alcance", "Vigencia 2026. Es de Educacion todo rubro cuyo cons_ppt esta en la "
                    "lista maestra RUBROS_EDUCACION (127 cons_ppt confirmados uno por uno "
                    "sobre el corte 15_09_2026), menos EXCLUSIONES. Se excluye 'Cierre de "
                    "reservas'. El codigo (02.01/01.01) NO se usa para clasificar: hay "
                    "rubros hermanos bajo el mismo codigo padre que son de otra Secretaria. "
                    "El color de cada fila lo pone el sistema solo (MAPA_COLORES); el "
                    "usuario no tiene que colorear el archivo de Hacienda."),
        ("Definitivo", "Apropiacion inicial +/- adiciones, reducciones y traslados."),
        ("Reservado (CDP)", "Certificado de Disponibilidad Presupuestal."),
        ("Comprometido (RP)", "Registro Presupuestal — respalda contrato u obligacion."),
        ("Obligado (OPS)", "Orden de Pago — obligacion reconocida y exigible."),
        ("Pagado", "Giro efectivo. En esta entidad suele coincidir con el obligado del corte."),
        ("Sin reservar / comprometer / obligar", "Brecha entre una etapa y la siguiente."),
        ("Componente", "Clasificacion por fuente. Ver hoja EJECUTIVO."),
        ("Contratos", "Se cargan en seguimiento_manual_educacion.xlsx (hoja CONTRATOS). "
                      "Cada corrida de GENERAR_INFORME.bat los vuelve a leer: lo que este "
                      "alli aparece aqui, no hay que copiar nada."),
        ("Conciliacion — definitiva", "Informe: {:,.0f}. Seguimiento manual 15/08/2026: {:,.0f}. "
         "Diferencia: {:,.0f}.".format(tot["definitiva"], SEGUIMIENTO_MANUAL_TOTAL_15_08,
                                       tot["definitiva"] - SEGUIMIENTO_MANUAL_TOTAL_15_08)),
        ("Conciliacion — obligado vs pagado", "Obligado {:,.0f}  Pagado {:,.0f}  Diferencia {:,.0f}. "
         "Confirmar con Hacienda si son OPS del corte sin comprobante de egreso.".format(
             tot["obligado"], tot["pagado"], tot["obligado"] - tot["pagado"])),
        ("Fuente del dato", os.path.basename(src_path)),
        ("Generado", datetime.date.today().isoformat()),
    ]
    if prev:
        filas_n.insert(11, ("Conciliacion — corte anterior",
                            "Corte {}: definitiva {:,.0f}. Variacion: {:,.0f}.".format(
                                prev.get("corte", "?"), prev.get("definitiva", 0),
                                tot["definitiva"] - prev.get("definitiva", 0))))
    if revisar:
        filas_n.append(("cons_ppt nuevos sin confirmar",
                        "; ".join(f"{c['cons_ppt']} ({c['codigo_rubro']})" for c in revisar)
                        + ". Confirmar y agregar a RUBROS_EDUCACION en el maestro, o dejar fuera."))
    for t in filas_n:
        wn.append(list(t))
    for r in range(2, wn.max_row + 1):
        wn.cell(r, 1).font = SUB_FONT
        wn.cell(r, 2).alignment = Alignment(wrap_text=True)

    wb.save(out)
    return out, tot, len(alertas)


def _generar_alertas(edu, revisar, contratos, tot):
    al = []
    UMBRAL = 100_000_000
    sin_comp = sorted([d for d in edu if d["definitiva"] > 0 and d["comprometido"] == 0],
                      key=lambda x: -x["definitiva"])
    for d in sin_comp:
        if d["definitiva"] >= UMBRAL:
            al.append(("MEDIA", "Rubro con apropiacion y sin comprometer",
                       f"{d['codigo_rubro']}  def {d['definitiva']:,.0f}  ({d['componente']})",
                       "Verificar estado de contratacion"))
    menores = [d for d in sin_comp if d["definitiva"] < UMBRAL]
    if menores:
        al.append(("BAJA", f"{len(menores)} rubros menores sin comprometer",
                   f"suma {sum(d['definitiva'] for d in menores):,.0f} (cada uno < {UMBRAL:,.0f})",
                   "Revision agregada; ver hoja SEGUIMIENTO"))
    for d in edu:
        if d["comprometido"] > d["definitiva"] + 0.5:
            al.append(("ALTA", "Comprometido supera la apropiacion definitiva",
                       f"{d['codigo_rubro']}  def {d['definitiva']:,.0f}  RP {d['comprometido']:,.0f}",
                       "REQUIERE REVISION"))
    if abs(tot["obligado"] - tot["pagado"]) > 1:
        al.append(("INFORMATIVA", "Obligado y Pagado no coinciden en el archivo de origen",
                   f"obl {tot['obligado']:,.0f}  pag {tot['pagado']:,.0f}  "
                   f"dif {tot['obligado'] - tot['pagado']:,.0f}",
                   "Confirmar con Hacienda"))
    for c in revisar:
        al.append(("ALTA", "cons_ppt NUEVO que parece de Educacion — sin confirmar",
                   f"{c['codigo_rubro']}  cons_ppt {c['cons_ppt']}  {c['fuente']}  def {c['definitiva']:,.0f}",
                   "Confirmar y agregar a RUBROS_EDUCACION en el maestro, o dejar fuera"))
    for c in contratos:
        m = c.get("match", "")
        if m.startswith("ambiguo:"):
            al.append(("ALTA", "Contrato con match AMBIGUO en CDP-CRP (un mismo CDP ampara varios rubros)",
                       "contrato %s  cdp %s  candidatos: %s" % (
                           c.get("nro_contrato", "?"), c.get("cdp", "?"), m.split(":", 1)[1]),
                       "Revisar manualmente en hoja CONTRATOS y confirmar el cons_ppt correcto"))
        elif m == "cdp_no_encontrado_en_hacienda":
            al.append(("MEDIA", "Contrato con CDP que no aparece en el Hacienda de este corte",
                       "contrato %s  cdp %s" % (c.get("nro_contrato", "?"), c.get("cdp", "?")),
                       "Verificar si el CDP fue anulado, es de otra vigencia, o cambio de numero"))
    return al


# --------------------------------------------------------------------------- #
# HISTORIAL
# --------------------------------------------------------------------------- #
def leer_prev():
    if not os.path.exists(HIST_PATH):
        return None
    rows = list(csv.DictReader(open(HIST_PATH, encoding="utf-8")))
    if not rows:
        return None
    last = rows[-1]
    return {"corte": last.get("fecha_corte"),
            "definitiva": float(last.get("definitiva", 0) or 0)}


def registrar_historial(corte, src, tot, n_edu, n_alertas):
    nuevo = not os.path.exists(HIST_PATH)
    with open(HIST_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["ejecutado", "archivo", "fecha_corte", "rubros_educacion",
                        "definitiva", "comprometido", "obligado", "pagado", "alertas"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"),
                    os.path.basename(src), corte.isoformat(), n_edu,
                    f"{tot['definitiva']:.0f}", f"{tot['comprometido']:.0f}",
                    f"{tot['obligado']:.0f}", f"{tot['pagado']:.0f}", n_alertas])


# --------------------------------------------------------------------------- #
# MAIN
# --------------------------------------------------------------------------- #
def main():
    if len(sys.argv) < 2:
        raise SystemExit('Uso: python extractor_educacion.py '
                         '"ruta\\Presupuesto de egreso a DD_MM_YYYY.xls"')
    src = sys.argv[1]
    if not os.path.exists(src):
        raise SystemExit("No existe el archivo: " + src)

    corte = fecha_de_corte(src)
    print("Corte:", corte.strftime("%d/%m/%Y"))

    filas = leer_egresos(src)
    print("  hojas leidas (vigencia, sin cierre de reservas):", len(filas))

    rubros_edu, mapa_colores, exc = leer_maestro(MAESTRO_PATH)
    print("  maestro: %d cons_ppt confirmados, %d exclusiones" % (len(rubros_edu), len(exc)))

    edu, no_edu, revisar = clasificar(filas, rubros_edu, exc)
    print("  -> Educacion: %d   fuera: %d   NUEVOS a REVISAR: %d" % (len(edu), len(no_edu), len(revisar)))
    if revisar:
        print("     cons_ppt nuevos que parecen de Educacion pero no estan en la lista maestra:")
        for d in sorted(revisar, key=lambda x: -x["definitiva"])[:15]:
            print("       cons_ppt=%s  def=%.0f  %s" % (d["cons_ppt"], d["definitiva"], d["nombre"][:60]))
        print("     -> confirmelos y agreguelos a RUBROS_EDUCACION en el maestro.")

    m_rubros, m_contratos = leer_manual(MANUAL_PATH, edu)
    print("  manual: %d rubros con nota, %d contratos" % (len(m_rubros), len(m_contratos)))

    try:
        cdp_contratos = leer_cdp_crp(src, edu)
    except Exception as e:
        print("  ERROR en leer_cdp_crp:", str(e))
        cdp_contratos = []
    if cdp_contratos:
        m_contratos.extend(cdp_contratos)
        n_ok = sum(1 for c in cdp_contratos if c.get("match", "").startswith("match_"))
        n_ambig = sum(1 for c in cdp_contratos if c.get("match", "").startswith("ambiguo"))
        n_sin = sum(1 for c in cdp_contratos if c.get("match") == "cdp_no_encontrado_en_hacienda")
        n_vig = sum(1 for c in cdp_contratos if c.get("match") == "vigencia_futura_otro_periodo")
        print("  CDP-CRP: %d contratos leidos -> %d con match, %d ambiguos, %d sin match, %d vigencia futura otro periodo" % (
            len(cdp_contratos), n_ok, n_ambig, n_sin, n_vig))
    else:
        print("  CDP-CRP: no se agregaron contratos")

    prev = leer_prev()
    out, tot, n_alertas = construir_informe(edu, revisar, m_rubros, m_contratos,
                                            mapa_colores, exc, corte, src, prev)
    registrar_historial(corte, src, tot, len(edu), n_alertas)

    # Generar JSON para dashboard online
    plan = construir_plan(edu, ORDEN_COMPONENTE + sorted(set(d["componente"] for d in edu) - set(ORDEN_COMPONENTE)))
    color_por_componente = dict(COLOR_COMPONENTE)
    color_por_componente.update(leer_maestro(MAESTRO_PATH)[1])
    out_json = generar_json_dashboard(edu, tot, plan, color_por_componente, corte, SALIDAS_DIR)

    print("\nOK ->", out)
    print("  definitiva  : {:>18,.0f}".format(tot["definitiva"]))
    print("  comprometido: {:>18,.0f}  ({:.1%})".format(
        tot["comprometido"], tot["comprometido"] / tot["definitiva"]))
    print("  pagado      : {:>18,.0f}  ({:.1%})".format(
        tot["pagado"], tot["pagado"] / tot["definitiva"]))


if __name__ == "__main__":
    main()
