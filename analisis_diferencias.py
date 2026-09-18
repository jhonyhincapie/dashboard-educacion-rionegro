# -*- coding: utf-8 -*-
"""Compara informe viejo vs presupuesto completo de Hacienda"""
import os
from openpyxl import load_workbook
import xlrd

# Archivos
informe_viejo = r"C:\Users\jhincapie\Downloads\07-15 Seguimiento al presupuesto para claude.xlsx"
presupuesto = r"C:\Users\jhincapie\OneDrive - Municipio de Rionegro\Escritorio\EDUCACIÓN\2026\PRUEBAS DE PRESUPUESTO\Presupuesto de egreso a 15_07_2026.xls"

print("="*80)
print("ANALISIS: INFORME VIEJO vs PRESUPUESTO COMPLETO")
print("="*80)

# 1. LEER INFORME VIEJO
print("\n[1] INFORME VIEJO (07-15):")
print("-" * 80)
wb_viejo = load_workbook(informe_viejo)
print(f"Hojas: {wb_viejo.sheetnames}")

for sheet_name in wb_viejo.sheetnames:
    ws = wb_viejo[sheet_name]
    print(f"\n  Hoja '{sheet_name}': {ws.max_row} filas, {ws.max_column} columnas")
    if ws.max_row > 1:
        header = [str(ws.cell(1, c).value or "") for c in range(1, min(10, ws.max_column + 1))]
        print(f"    Encabezados: {header}")

# 2. LEER PRESUPUESTO COMPLETO
print("\n\n[2] PRESUPUESTO COMPLETO (15_07_2026):")
print("-" * 80)
wb_pres = xlrd.open_workbook(presupuesto)
print(f"Hojas: {wb_pres.sheet_names()}")
sh = wb_pres.sheet_by_index(0)
H = [str(sh.cell_value(0, c)).strip() for c in range(sh.ncols)]
print(f"  Hoja principal: {sh.nrows} filas, {sh.ncols} columnas")
print(f"  Encabezados (primeros 15): {H[:15]}")

# 3. ANALIZAR RUBROS EN INFORME VIEJO
print("\n\n[3] RUBROS EN INFORME VIEJO:")
print("-" * 80)
ws_segu = wb_viejo[wb_viejo.sheetnames[0]]
if ws_segu:
    rubros_viejo = {}
    for r in range(2, min(50, ws_segu.max_row + 1)):
        cons = str(ws_segu.cell(r, 1).value or "").strip()
        nombre = str(ws_segu.cell(r, 2).value or "").strip()
        if cons:
            rubros_viejo[cons] = nombre
    print(f"Total rubros encontrados: {len(rubros_viejo)}")
    print("Primeros 10:")
    for i, (cons, nom) in enumerate(list(rubros_viejo.items())[:10]):
        print(f"  {cons:10s} | {nom[:50]}")

# 4. ANALIZAR RUBROS EN PRESUPUESTO COMPLETO
print("\n\n[4] RUBROS EN PRESUPUESTO COMPLETO (Hacienda):")
print("-" * 80)
C = {h: H.index(h) for h in set(H)}
PAD_idx = C.get("codigo_padre")
COD_idx = [i for i, h in enumerate(H) if h == "codigo"][0] if "codigo" in H else None
CONS_idx = C.get("cons_ppt")
DESC_idx = [i for i, h in enumerate(H) if h == "descripcion"][0] if "descripcion" in H else None

rubros_hacienda = {}
for r in range(1, sh.nrows):
    if str(sh.cell_value(r, C.get("final", 0))) != "S":
        continue
    if "CIERRE" in str(sh.cell_value(r, DESC_idx or 0)).upper():
        continue
    cons = str(int(float(sh.cell_value(r, CONS_idx)))) if CONS_idx else ""
    if cons:
        full_cod = str(sh.cell_value(r, PAD_idx)) + str(sh.cell_value(r, COD_idx))
        desc = str(sh.cell_value(r, DESC_idx)).strip() if DESC_idx else ""
        rubros_hacienda[cons] = {"codigo": full_cod, "nombre": desc}

print(f"Total rubros 02.01 en Hacienda: {len(rubros_hacienda)}")
print("Primeros 10:")
for i, (cons, d) in enumerate(list(rubros_hacienda.items())[:10]):
    print(f"  {cons:10s} | {d['codigo']:30s} | {d['nombre'][:40]}")

# 5. COMPARAR
print("\n\n[5] DIFERENCIAS:")
print("-" * 80)
print("Rubros EN INFORME VIEJO pero NO en Hacienda 2026:")
for cons in sorted(rubros_viejo.keys()):
    if cons not in rubros_hacienda:
        print(f"  {cons:10s} | {rubros_viejo[cons][:60]}")
