#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Servidor local del dashboard. /datos.json se regenera desde el Excel en cada consulta.
Uso: python servidor_dashboard.py [ruta_excel]   (por defecto: el corte mas reciente en informes/)"""
import http.server
import json
import os
import socketserver
import sys
import webbrowser

import extractor_contratos as extc
import extractor_dashboard as ext

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("EXCEL_PATH")
PORT = int(os.environ.get("PORT_DASH", 8080))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=RAIZ, **k)

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta in ("/datos.json", "/contratos.json"):
            try:
                datos = ext.extraer(EXCEL) if ruta == "/datos.json" else extc.extraer_contratos()
                body = json.dumps(datos, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
            except Exception as e:
                body = json.dumps({"error": str(e)}, ensure_ascii=False).encode("utf-8")
                self.send_response(500)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"Dashboard: http://localhost:{PORT}/dashboard_ejecutivo.html")
        print(f"Excel: {EXCEL or ext.excel_mas_reciente()}")
        if os.environ.get("NO_BROWSER") != "1":
            webbrowser.open(f"http://localhost:{PORT}/dashboard_ejecutivo.html")
        httpd.serve_forever()
