# -*- coding: utf-8 -*-
"""
EXTRACTOR V2 — INFORME GERENCIAL AUTOMATIZADO
Base: extractor_educacion.py + Paleta de 8 colores + Hoja Ejecutivo
"""

# Paleta de colores RGB (para openpyxl)
COLORES = {
    "amarillo_oscuro": "FFD966",      # Prestación del Servicio
    "amarillo_claro": "FFEB9C",        # RF/RB de Prestación
    "azul_oscuro": "4472C4",           # SGP Educación
    "azul_claro": "B4C7E7",            # RF/RB de SGP
    "verde_oscuro": "70AD47",          # Calidad Matrícula
    "verde_claro": "C6EFCE",           # RF/RB de Calidad
    "naranja": "FFC000",               # Calidad Gratuidad
    "rosado": "F8CBAD",                # Primera Infancia
    "gris": "E7E6E6",                  # Otras fuentes
}

# Mapeo: Componente → Color
MAPA_COLORES_COMPONENTE = {
    "SGP Prestacion del Servicio": "amarillo_oscuro",
    "Rendimientos Financieros PS": "amarillo_claro",
    "Recursos Balance PS": "amarillo_claro",

    "SGP Calidad-Matricula": "verde_oscuro",
    "Rendimientos Financieros Matricula": "verde_claro",
    "Recursos Balance Matricula": "verde_claro",

    "SGP Calidad-Gratuidad": "naranja",

    "Alimentacion Escolar (PAE)": "azul_oscuro",
    "SGP Proposito General": "azul_oscuro",

    "Primera Infancia": "rosado",

    "Recursos Propios / Libre Destinacion": "gris",
    "Recursos de Credito": "gris",
    "Estampillas": "gris",
    "Otras fuentes": "gris",
    "(sin fuente)": "gris",
}

# NUEVO: Orden de Componentes según especificación
ORDEN_COMPONENTE_V2 = [
    "SGP Prestacion del Servicio",
    "Rendimientos Financieros PS",
    "Recursos Balance PS",

    "SGP Calidad-Matricula",
    "Rendimientos Financieros Matricula",
    "Recursos Balance Matricula",

    "SGP Calidad-Gratuidad",

    "Alimentacion Escolar (PAE)",
    "SGP Proposito General",

    "Primera Infancia",

    "Recursos Propios / Libre Destinacion",
    "Recursos de Credito",
    "Estampillas",
    "Otras fuentes",
    "(sin fuente)",
]

def agrupar_por_componente(edu):
    """
    Agrupa rubros por componente y calcula totales.

    Retorna: {
        "componente_name": {
            "color": "amarillo_oscuro",
            "rubros": [list de rubros],
            "totales": {
                "definitiva": XXX,
                "reservado": XXX,
                "comprometido": XXX,
                "obligado": XXX,
                "pagado": XXX,
            },
            "gaps": {
                "sin_reservar": XXX,
                "sin_comprometer": XXX,
                "sin_obligar": XXX,
            },
            "porcentajes": {
                "comp": 0.71,
                "pag": 0.42,
            }
        }
    }
    """
    by_comp = {}

    for d in edu:
        comp = d.get("componente", "(sin fuente)")

        if comp not in by_comp:
            by_comp[comp] = {
                "color": MAPA_COLORES_COMPONENTE.get(comp, "gris"),
                "rubros": [],
                "totales": {
                    "definitiva": 0,
                    "reservado": 0,
                    "comprometido": 0,
                    "obligado": 0,
                    "pagado": 0,
                }
            }

        by_comp[comp]["rubros"].append(d)

        for key in ["definitiva", "reservado", "comprometido", "obligado", "pagado"]:
            by_comp[comp]["totales"][key] += d.get(key, 0)

    # Calcular gaps y porcentajes
    for comp, info in by_comp.items():
        tot = info["totales"]
        def_ = tot["definitiva"]

        info["gaps"] = {
            "sin_reservar": def_ - tot["reservado"],
            "sin_comprometer": tot["reservado"] - tot["comprometido"],
            "sin_obligar": tot["comprometido"] - tot["obligado"],
        }

        info["porcentajes"] = {
            "comp": (tot["comprometido"] / def_) if def_ else 0,
            "pag": (tot["pagado"] / def_) if def_ else 0,
        }

    return by_comp


def _rgb(hex_color):
    """Convierte hex a RGB para openpyxl"""
    from openpyxl.styles import PatternFill
    return PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")


# USO EN INFORME:
# by_comp = agrupar_por_componente(edu)
# for comp_name in ORDEN_COMPONENTE_V2:
#     if comp_name in by_comp:
#         info = by_comp[comp_name]
#         color = COLORES[info["color"]]
#         # Agregar fila a hoja EJECUTIVO con color y totales

print("✅ Módulo de colores y agrupación por componente cargado")
print(f"   Colores disponibles: {len(COLORES)}")
print(f"   Componentes mapeados: {len(MAPA_COLORES_COMPONENTE)}")
