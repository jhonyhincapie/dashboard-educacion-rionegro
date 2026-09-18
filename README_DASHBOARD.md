# Dashboard Presupuestal Ejecutivo - Secretaría de Educación

Dashboard dinámico, interactivo y online para visualizar la ejecución presupuestal de la Secretaría de Educación de Rionegro.

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│  PASO 1: Extractor Python (tu máquina)                  │
│  • Genera Excel (auditoría)                              │
│  • Genera JSON (datos dinámicos)                         │
│  • Se ejecuta: python extractor_educacion.py             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  PASO 2: Backend Flask (tu máquina + Cloudflare Tunnel) │
│  • Lee JSON más reciente                                 │
│  • Sirve API en http://localhost:5000                    │
│  • Se expone públicamente con Cloudflare Tunnel          │
│  • Se ejecuta: python backend.py                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  PASO 3: Dashboard React (Vercel)                        │
│  • Consumidor de la API                                  │
│  • Gráficos animados, accordion, filtros                │
│  • Se deployea en: https://dashboard-educacion.vercel.app
└─────────────────────────────────────────────────────────┘
```

## 🚀 Instalación y Uso

### PASO 1: Extractor Python

El extractor ya está configurado para generar JSON. Solo ejecuta:

```bash
cd SECRETARIA_EDUCACION
python extractor_educacion.py "entradas/Presupuesto de egreso a 15_09_2026.xls"
```

Esto genera:
- `informes/Seguimiento Presupuestal Educacion a 15_09_2026.xlsx`
- `informes/seguimiento_15_09_2026.json` ⭐ (nuevo)

### PASO 2: Backend Flask

#### Requisitos

```bash
pip install flask flask-cors
```

#### Ejecutar backend

```bash
cd SECRETARIA_EDUCACION
python backend.py
```

Salida esperada:
```
🚀 Backend iniciado
📁 Leyendo informes de: .../informes
🌐 Servidor en: http://localhost:5000
📊 Dashboard API: http://localhost:5000/api/presupuesto/latest
```

**Prueba el API en tu navegador:**
- http://localhost:5000/health (healthcheck)
- http://localhost:5000/api/presupuesto/latest (datos JSON)
- http://localhost:5000/api/presupuesto/lista (lista de cortes)

### PASO 3: Exponer con Cloudflare Tunnel

El backend está en tu máquina local. Para que el dashboard React (online) pueda acceder, usa Cloudflare Tunnel (gratis, no requiere puerto abierto).

#### Instalar Cloudflare Tunnel

1. **Descargar e instalar cloudflared:**
   - Windows: `choco install cloudflared` (si tienes Chocolatey)
   - O descargar de: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/

2. **Autenticar:**
   ```bash
   cloudflared login
   ```
   Se abre tu navegador, autentíficate con tu cuenta de Cloudflare (crea una si no tienes, es gratis).

3. **Crear un túnel named:**
   ```bash
   cloudflared tunnel create dashboard-edu-rionegro
   ```
   Guarda el token que genera.

4. **Ejecutar el túnel:**
   ```bash
   cloudflared tunnel run --url http://localhost:5000 dashboard-edu-rionegro
   ```
   O usa el config file (más adelante).

Salida esperada:
```
2024-XX-XX 12:34:56.789Z  INF +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
2024-XX-XX 12:34:56.789Z  INF | Cloudflare Tunnel running                               |
2024-XX-XX 12:34:56.789Z  INF +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
2024-XX-XX 12:34:56.789Z  INF |URL: https://dashboard-edu-rionegro.cfargotunnel.com      |
2024-XX-XX 12:34:56.789Z  INF +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
```

**Guarda esta URL:** `https://dashboard-edu-rionegro.cfargotunnel.com` (o la que te genere)

### PASO 4: Dashboard React en Vercel

#### 1. Preparar repositorio Git

```bash
cd dashboard
git init
git add .
git commit -m "Initial commit: Dashboard React"
```

#### 2. Crear repositorio en GitHub

- Ve a https://github.com/new
- Crea un repo: `dashboard-educacion-rionegro`
- Sigue las instrucciones para hacer push

```bash
git remote add origin https://github.com/TU_USUARIO/dashboard-educacion-rionegro.git
git branch -M main
git push -u origin main
```

#### 3. Deployar en Vercel

- Ve a https://vercel.com
- Click "New Project"
- Conecta tu cuenta de GitHub
- Selecciona el repo `dashboard-educacion-rionegro`
- **Environment Variables:**
  - Nombre: `REACT_APP_API_BASE`
  - Valor: `https://dashboard-edu-rionegro.cfargotunnel.com`
  - Click "Add"
- Click "Deploy"

Espera a que termine. Vercel te dará una URL como:
```
https://dashboard-educacion-rionegro.vercel.app
```

¡Listo! Ya tienes el dashboard online.

---

## 📊 Flujo de Actualización

Cada vez que quieras actualizar los datos:

1. **Descarga el presupuesto más reciente** de Hacienda a `SECRETARIA_EDUCACION/entradas/`
2. **Ejecuta el extractor:**
   ```bash
   python extractor_educacion.py "entradas/Presupuesto de egreso a DD_MM_YYYY.xls"
   ```
3. **Backend sigue corriendo:**
   - Lee automáticamente el JSON más reciente
   - Sirve los datos actualizados
4. **Dashboard se actualiza:**
   - Recarga automáticamente cada 5 minutos
   - O el usuario refresca la página manualmente

---

## 🔧 APIs Disponibles

El backend Flask sirve estos endpoints:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/health` | GET | Healthcheck |
| `/api/presupuesto/latest` | GET | Datos más recientes (JSON) |
| `/api/presupuesto/lista` | GET | Lista de todos los cortes |
| `/api/presupuesto/<corte>` | GET | Datos de un corte específico |

Ejemplo: `/api/presupuesto/15_09_2026`

---

## 🎨 Features del Dashboard

✅ **Tarjetas KPI** — 5 indicadores principales con animaciones  
✅ **Brechas de Ejecución** — 3 tarjetas con visualización de gaps  
✅ **Gráficos Animados** — Barras, líneas, donas (Recharts)  
✅ **Búsqueda de Rubros** — Filtrar por nombre o cons_ppt  
✅ **Filtro por Componente** — Seleccionar componentes específicos  
✅ **Accordion Expandible** — Drill-down Componente → Subgrupo → Rubro  
✅ **Modo Oscuro** — Toggle para tema dark  
✅ **Responsive** — Funciona en móvil, tablet, desktop  
✅ **Actualización Automática** — Cada 5 minutos  
✅ **Tabla Interactiva** — Rubros dentro de cada componente  

---

## 🛠️ Troubleshooting

### Dashboard dice "No se pudo conectar al servidor"

**Verificar:**
1. Backend Flask está corriendo: `python backend.py`
2. Cloudflare Tunnel está activo
3. URL en Vercel env var es correcta

**Solución:**
```bash
# Probar acceso a API manualmente
curl https://dashboard-edu-rionegro.cfargotunnel.com/health

# Debería retornar: {"status": "ok", ...}
```

### Error: "Module not found: axios" (React)

**Solución:**
```bash
cd dashboard
npm install
```

### Backend dice "No se encontraron datos presupuestales"

**Verificar:**
```bash
# El archivo JSON existe en informes/
ls -la SECRETARIA_EDUCACION/informes/*.json

# Si no existe, ejecuta el extractor:
python extractor_educacion.py "entradas/Presupuesto de egreso a DD_MM_YYYY.xls"
```

---

## 📝 Notas

- **Backend local + Frontend online**: Este setup es ideal para mantener tus datos seguros en tu máquina mientras ofreces visualización pública.
- **Cloudflare Tunnel gratis**: No requiere tarjeta de crédito, es de Cloudflare (confiable).
- **React en Vercel gratis**: Unlimited deployments, HTTPS automático, CDN global.
- **Datos actualizados**: El dashboard siempre muestra el corte más reciente disponible.

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que el JSON se generó: `informes/seguimiento_DD_MM_YYYY.json`
2. Prueba el API manualmente en tu navegador
3. Revisa logs del backend (`python backend.py`) y del Tunnel (`cloudflared tunnel run ...`)

---

**Versión:** 1.0.0  
**Última actualización:** 2026-09-18  
**Desarrollado con:** Python, Flask, React, Recharts
