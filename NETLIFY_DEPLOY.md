# Publicar Dashboard a Netlify

## Archivos listos para publicar

La carpeta `publicar/` contiene:
- ✅ `index.html` - Dashboard interactivo con pestaña Presupuesto y Contratos
- ✅ `datos.json` - Datos presupuestales (corte 15 de septiembre 2026)
- ✅ `contratos.json` - 22 contratos con cruce por CDP y verificación en "cdps"
- ✅ `_headers` - Configuración Netlify (no cachear, noindex)
- ✅ `assets/` - Logo de Rionegro

## Método 1: Drag & Drop en Netlify (más fácil)

1. Abrir https://app.netlify.com/drop
2. Arrastrar la carpeta `publicar/` al área de drop
3. ¡Listo! Netlify genera un URL temporal

## Método 2: Conectar repositorio Git (recomendado)

### Paso 1: Inicializar repositorio (si no existe)
```bash
cd RIONEGRO_EDUCACION_AI
git init
git add publicar/
git commit -m "Publicar dashboard con cruce por cdps"
git branch -M main
```

### Paso 2: Crear repositorio en GitHub
1. Ir a https://github.com/new
2. Nombre: `rionegro-dashboard-educacion`
3. Crear repositorio vacío (sin README)

### Paso 3: Conectar con Git
```bash
git remote add origin https://github.com/TU_USUARIO/rionegro-dashboard-educacion.git
git push -u origin main
```

### Paso 4: Conectar GitHub a Netlify
1. Abrir https://app.netlify.com
2. Click "New site from Git"
3. Seleccionar GitHub
4. Buscar y seleccionar `rionegro-dashboard-educacion`
5. Build command: (dejar vacío)
6. Publish directory: `publicar`
7. Click "Deploy site"

## Configuración Netlify

El archivo `_headers` ya está configurado con:
- **Cache-Control**: no-store (no cachear, actualizar siempre)
- **X-Robots-Tag**: noindex, nofollow (no indexar en Google)

Si quieres cambiar esto (indexar en Google):
- Editar `publicar/_headers`
- Cambiar a: `X-Robots-Tag: index, follow`
- Redeploy

## Actualizar después de cambios

### Con Drag & Drop
- Generar nuevos datos: `python SECRETARIA_EDUCACION/publicar_dashboard.py`
- Arrastrar carpeta `publicar/` a https://app.netlify.com/drop

### Con Git
```bash
# Generar datos
cd SECRETARIA_EDUCACION
python publicar_dashboard.py

# Publicar cambios
cd ..
git add publicar/
git commit -m "Actualizar dashboard: [descripcion de cambios]"
git push
# Netlify redeploy automáticamente
```

## Automatización (opcional)

Para hacer que los datos se actualicen automáticamente cada día:

1. Crear archivo `.github/workflows/update-dashboard.yml` en el repositorio
2. Configurar GitHub Actions para ejecutar `python publicar_dashboard.py`
3. Push automático de cambios

Ejemplo de workflow:
```yaml
name: Update Dashboard
on:
  schedule:
    - cron: '0 6 * * *'  # 6 AM diariamente
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install openpyxl xlrd
      - run: cd SECRETARIA_EDUCACION && python publicar_dashboard.py
      - run: git config user.email "bot@example.com"
      - run: git config user.name "Dashboard Bot"
      - run: git add publicar/ && git commit -m "Auto-update dashboard" && git push
```

## Datos públicos vs privados

La versión publicada (archivo `publicar/contratos.json`) oculta:
- ✅ Nombres de contratistas
- ❌ Números de contrato (VISIBLES - son públicos)
- ❌ CDP y CRP (VISIBLES - son del presupuesto público)
- ✅ Responsables (no incluidos)

Para cambiar este comportamiento, editar `SECRETARIA_EDUCACION/publicar_dashboard.py`:
- Línea 10: cambiar `OCULTAR_CONTRATISTAS_EN_PUBLICO = False`

## URL esperado en Netlify

Una vez publicado, tendrás:
- URL: `https://[nombre-aleatorio].netlify.app`
- Dashboard: `https://[nombre-aleatorio].netlify.app/`
- Datos presupuesto: `https://[nombre-aleatorio].netlify.app/datos.json`
- Datos contratos: `https://[nombre-aleatorio].netlify.app/contratos.json`

Para un dominio personalizado:
1. En Netlify: "Site settings" → "Domain management"
2. Agregar dominio personalizado (ej: `dashboard-educacion.rionegro.gov.co`)
3. Configurar DNS según indicaciones de Netlify

## Soporte

- Netlify Help: https://docs.netlify.com
- Problemas de build: Ver logs en "Deploys" → Click en deploy → "Deploy log"
- Preguntas sobre datos: Ver archivo `CRUCE_POR_CDPS.md`
