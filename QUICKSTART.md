# 🚀 INICIO RÁPIDO - Dashboard Online

**5 pasos para tener el dashboard funcionando en 15 minutos**

---

## ✅ PASO 1: Generar JSON (1 min)

Ejecuta el extractor para generar los datos:

```bash
cd SECRETARIA_EDUCACION
python extractor_educacion.py "entradas/Presupuesto de egreso a 15_09_2026.xls"
```

**Verifica que se creó:**
```bash
ls -la informes/seguimiento_15_09_2026.json
```

---

## ✅ PASO 2: Instalar Flask (1 min)

```bash
pip install flask flask-cors
```

---

## ✅ PASO 3: Correr Backend (3 min)

**Terminal 1: Backend Python**

```bash
cd SECRETARIA_EDUCACION
python backend.py
```

Verás:
```
🚀 Backend iniciado
🌐 Servidor en: http://localhost:5000
📊 Dashboard API: http://localhost:5000/api/presupuesto/latest
```

**Prueba que funciona:**
Abre en tu navegador: http://localhost:5000/health

Deberías ver:
```json
{"status": "ok", "timestamp": "2026-09-18T..."}
```

---

## ✅ PASO 4: Exponer con Cloudflare Tunnel (5 min)

**Terminal 2: Cloudflare Tunnel**

### 4a. Instalar cloudflared

**Windows:**
```bash
# Opción 1: con Chocolatey
choco install cloudflared

# Opción 2: descargar manualmente
# https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
```

**Mac/Linux:**
```bash
# Mac:
brew install cloudflare/cloudflare/cloudflared

# Linux:
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
chmod +x cloudflared-linux-amd64
sudo mv cloudflared-linux-amd64 /usr/local/bin/cloudflared
```

### 4b. Crear túnel

```bash
cloudflared login
```
Se abre tu navegador → autentíficate con Cloudflare (o crea cuenta gratis)

### 4c. Crear named tunnel

```bash
cloudflared tunnel create dashboard-edu
```

Te mostrará algo como:
```
Tunnel UUID: 12345678-1234-1234-1234-123456789012
Tunnel credentials file saved at: ...
```

### 4d. Ejecutar el túnel

```bash
cloudflared tunnel run --url http://localhost:5000 dashboard-edu
```

**Guarda esta URL (aparecerá en los logs):**
```
https://dashboard-edu-<ID>.cfargotunnel.com
```

Ejemplo: `https://dashboard-edu-xyz.cfargotunnel.com`

---

## ✅ PASO 5: Deployar Dashboard en Vercel (5 min)

### 5a. Preparar repositorio Git

```bash
cd dashboard
git init
git add .
git commit -m "Initial commit"
```

### 5b. Crear repo en GitHub

1. Ve a https://github.com/new
2. Nombre: `dashboard-educacion-rionegro`
3. Crea el repo (sin README)
4. Copia el comando `git remote add origin ...`

```bash
git remote add origin https://github.com/TU_USUARIO/dashboard-educacion-rionegro.git
git branch -M main
git push -u origin main
```

### 5c. Deployar en Vercel

1. Ve a https://vercel.com/new
2. Click "Continue with GitHub"
3. Conecta tu GitHub
4. Selecciona repo `dashboard-educacion-rionegro`
5. **Environment Variables:**
   - Nombre: `REACT_APP_API_BASE`
   - Valor: `https://dashboard-edu-xyz.cfargotunnel.com` (la URL de tu túnel)
   - Click "Add"
6. Click "Deploy"

**Espera a que termine (2-3 minutos)**

Vercel te dará una URL como:
```
https://dashboard-educacion-rionegro.vercel.app
```

¡**YA ESTÁ ONLINE!** 🎉

---

## 🧪 Verificación Final

1. **Abre el dashboard:**
   ```
   https://dashboard-educacion-rionegro.vercel.app
   ```

2. **Debería ver:**
   - ✅ 5 tarjetas KPI con números
   - ✅ 3 tarjetas de Brechas
   - ✅ Gráficos animados
   - ✅ Lista de componentes expandibles
   - ✅ Búsqueda y filtros

3. **Si no ve datos:**
   - Verifica que Backend sigue corriendo (Terminal 1)
   - Verifica que Cloudflare Tunnel está activo (Terminal 2)
   - Revisa la URL de API en Vercel env variables

---

## 📊 Actualizar Datos

Cada vez que quieras actualizar:

```bash
# 1. Descarga nuevo presupuesto a: entradas/Presupuesto de egreso a DD_MM_YYYY.xls
# 2. Ejecuta:
python extractor_educacion.py "entradas/Presupuesto de egreso a DD_MM_YYYY.xls"

# 3. Backend automáticamente sirve el JSON más reciente
# 4. Refresca el dashboard (o espera 5 min para auto-reload)
```

---

## ⚠️ Mantener Servicios Activos

Para que funcione 24/7:

- **Backend:** Mantén la Terminal 1 abierta o usa algo como `screen` / `tmux` en Linux
- **Cloudflare Tunnel:** Mantén la Terminal 2 abierta o configura autostart

**Alternativa:** Si tu máquina apaga, ejecuta estos comandos al iniciar:

```bash
# Terminal 1
cd /ruta/a/SECRETARIA_EDUCACION && python backend.py

# Terminal 2
cloudflared tunnel run --url http://localhost:5000 dashboard-edu
```

---

## 🆘 Si algo falla

### "No se puede conectar al servidor"

```bash
# Verifica que backend está activo
curl http://localhost:5000/health

# Verifica que cloudflare está activo (debería tener logs activos en Terminal 2)
```

### "Módulo no encontrado: axios"

```bash
cd dashboard
npm install
```

### "No se encontraron datos"

```bash
# Verifica que el JSON existe
ls -la SECRETARIA_EDUCACION/informes/seguimiento_*.json

# Si no, ejecuta el extractor
python extractor_educacion.py "entradas/Presupuesto de egreso a 15_09_2026.xls"
```

---

## 📞 Resumen de URLs

| Servicio | URL | Ubicación |
|----------|-----|-----------|
| **Backend** | http://localhost:5000 | Tu máquina (local) |
| **API** | https://dashboard-edu-xyz.cfargotunnel.com | Cloudflare Tunnel |
| **Dashboard** | https://dashboard-educacion-rionegro.vercel.app | Vercel (online) |

---

## ✨ Listo!

Ya tienes un **dashboard presupuestal profesional, dinámico y online** 🎉

- Datos siempre actualizados
- Accesible desde cualquier lugar
- Gráficos interactivos
- Búsqueda y filtros
- Modo oscuro

**Próximas mejoras (opcional):**
- Exportar a PDF desde el dashboard
- Histórico de cortes (comparar fechas)
- Alertas por email
- Integración con Slack

---

**¿Preguntas?** Revisa `README_DASHBOARD.md` para documentación completa.
