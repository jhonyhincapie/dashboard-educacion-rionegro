#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend Flask para Dashboard Presupuestal Educación
Sirve la API que alimenta el dashboard React online.

Uso:
    python backend.py

    Luego accesible en:
    - http://localhost:5000/api/presupuesto/latest (JSON datos)
    - http://localhost:5000/health (healthcheck)

Para producción con Cloudflare Tunnel:
    cloudflare tunnel run <tunnel-name>
"""

import os
import json
import glob
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Habilitar CORS para que el frontend React (en Vercel) pueda hacer requests

BASE = os.path.dirname(os.path.abspath(__file__))
INFORMES_DIR = os.path.join(BASE, "informes")


def obtener_json_mas_reciente():
    """Lee la carpeta de informes y retorna el JSON más reciente."""
    patron = os.path.join(INFORMES_DIR, "seguimiento_*.json")
    archivos = glob.glob(patron)

    if not archivos:
        return None, None

    # Ordenar por fecha de modificación (más reciente primero)
    archivo_mas_reciente = max(archivos, key=os.path.getmtime)

    try:
        with open(archivo_mas_reciente, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return datos, os.path.basename(archivo_mas_reciente)
    except Exception as e:
        print(f"ERROR al leer {archivo_mas_reciente}: {e}")
        return None, None


@app.route("/health", methods=["GET"])
def health():
    """Healthcheck endpoint."""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()}), 200


@app.route("/api/presupuesto/latest", methods=["GET"])
def presupuesto_latest():
    """Retorna el JSON más reciente del presupuesto."""
    datos, nombre_archivo = obtener_json_mas_reciente()

    if datos is None:
        return jsonify({
            "error": "No se encontraron datos presupuestales",
            "mensaje": "Ejecuta el extractor para generar los archivos de presupuesto"
        }), 404

    # Agregar metadata
    datos["_metadata"] = {
        "archivo": nombre_archivo,
        "timestamp_lectura": datetime.now().isoformat(),
        "fuente": "Secretaría de Educación - Rionegro"
    }

    return jsonify(datos), 200


@app.route("/api/presupuesto/lista", methods=["GET"])
def presupuesto_lista():
    """Retorna una lista de todos los cortes disponibles."""
    patron = os.path.join(INFORMES_DIR, "seguimiento_*.json")
    archivos = glob.glob(patron)

    cortes = []
    for archivo in sorted(archivos, reverse=True):  # Más recientes primero
        nombre = os.path.basename(archivo)
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                datos = json.load(f)
            corte = datos.get("corte", "")
            cortes.append({
                "archivo": nombre,
                "corte": corte,
                "fecha_generacion": datos.get("fecha_generacion", ""),
                "path": archivo,
            })
        except Exception:
            pass

    return jsonify({"cortes": cortes}), 200


@app.route("/api/presupuesto/<corte>", methods=["GET"])
def presupuesto_por_corte(corte):
    """Retorna el JSON de un corte específico."""
    patron = os.path.join(INFORMES_DIR, f"seguimiento_{corte}.json")

    if not os.path.exists(patron):
        return jsonify({"error": "Corte no encontrado"}), 404

    try:
        with open(patron, "r", encoding="utf-8") as f:
            datos = json.load(f)
        datos["_metadata"] = {
            "archivo": os.path.basename(patron),
            "timestamp_lectura": datetime.now().isoformat(),
        }
        return jsonify(datos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def inicio():
    """Página de bienvenida con documentación de la API."""
    return jsonify({
        "api": "Dashboard Presupuestal Educación - Rionegro",
        "version": "1.0.0",
        "endpoints": {
            "GET /health": "Healthcheck",
            "GET /api/presupuesto/latest": "Últimos datos presupuestales (JSON)",
            "GET /api/presupuesto/lista": "Lista de cortes disponibles",
            "GET /api/presupuesto/<corte>": "Datos de un corte específico (ej: 15_09_2026)",
        },
        "ejemplo": "/api/presupuesto/15_09_2026",
    }), 200


if __name__ == "__main__":
    # Verificar que la carpeta de informes existe
    if not os.path.exists(INFORMES_DIR):
        print(f"ADVERTENCIA: Carpeta {INFORMES_DIR} no existe")
        os.makedirs(INFORMES_DIR, exist_ok=True)

    # Correr en modo desarrollo (cambiar debug=False en producción)
    print(f"\n🚀 Backend iniciado")
    print(f"📁 Leyendo informes de: {INFORMES_DIR}")
    print(f"🌐 Servidor en: http://localhost:5000")
    print(f"📊 Dashboard API: http://localhost:5000/api/presupuesto/latest")
    print(f"\nPara exponer con Cloudflare Tunnel:")
    print(f"   cloudflare tunnel run --url http://localhost:5000 dashboard-edu\n")

    app.run(host="0.0.0.0", port=5000, debug=True)
