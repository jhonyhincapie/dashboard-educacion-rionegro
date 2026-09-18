# ANÁLISIS: INFORME VIEJO (15_07) vs PRESUPUESTO NUEVO (31_08)

## 1. ESTRUCTURA DEL INFORME VIEJO (07-15)

### Hoja: `0715SEGUMIENTO`
- **Filas:** 44
- **Columnas:** 15
- **Encabezados (Fila 2):**
  - Programa | Proyecto | Contratos | Fuente | Ppto. Definitivo | Reservado CDP | Comprometido RP | Obligado OPS | Pagado | ...

### Estructura de datos (Filas 3+):
- **Por Proyecto:** Agrupa rubros por proyecto (ej: "020103 Fortalecimiento de Infra", "020104 Fortalecimiento de la E")
- **Por Contrato:** Detalla cada contrato dentro del proyecto
- **Por Fuente:** Clasificación por origen del presupuesto (SGP Educación, R. Propios, CRÉDITO, etc.)
- **Totales:** Fila resumen al final

### Colores Identificados:
- **7 colores distintos** utilizados para codificación (necesita análisis RGB exacto)
- Probablemente: Amarillo, Verde, Azul, Rojo, Naranja, Gris para diferentes estados/categorías

---

## 2. PRESUPUESTO COMPLETO (15_07_2026)

### Archivo: `Presupuesto de egreso a 15_07_2026.xls`
- **Hoja:** "Presupuesto de egreso a 15_07_2"
- **Filas:** 2,596
- **Columnas:** 51

### Encabezados relevantes:
- `ano`, `cons_ppt`, `codigo_padre`, `codigo`, `final`
- `fondo`, `descripcion_fondo`, `descripcion`
- `codigo_fuente`, `descripcion_fuente`
- `tot_ppto`, `tot_reserv`, `tot_crp`, `tot_ops`, `tot_pag`

### Estructura de datos:
- Cada fila = un rubro detallado
- Jerárquico: `codigo_padre` + `codigo` = código completo
- **1,777 rubros totales** encontrados

---

## 3. RUBROS PRESENTES EN INFORME VIEJO

### Ejemplo de proyectos/rubros extraídos (primeras 20 líneas):
1. **020103** - Fortalecimiento de Infra (WPR - EDESO)
2. **020103** - Fortalecimiento de Infra (vacío)
3. **020103** - Ciudadela Educativa Eta (EDESO)
4. **020104** - Fortalecimiento de la E (RIO 4.0 Corporacion Gilberto)
5. **020104** - Fortalecimiento de la E (Union temporal UDA-IDA)
6. **020101** - VF Fortalecimiento (Equide y Union temporal IE)
7. Fortalecimiento Programa de Bi (comfenalco y Colombo)
8. **020102** - Formulación e implement (Equide)
9. **PRESTACIÓN DEL SERVICIO** (Nomina docente)
10. **PRESTACIÓN DEL SERVICIO** - Conectividad (Eso Rionegro)
... y más

### Categorías principales visibles:
- **Proyectos de infraestructura** (020103, 020104)
- **Formulación** (020102)
- **Viabilidad Futura** (VF)
- **Prestación del Servicio** (Nómina docente)
- **Calidad Educativa** (SGP Ed. Calidad MT)
- **Fortalecimiento** (Diversos programas)

---

## 4. COMPARACIÓN CIFRAS

### Informe Viejo (15_07_2026):
- Título: "SEGUIMIENTO JULIO 1 AL 15 DE JULIO DE 2026"
- Fecha de corte: **15 de julio de 2026**

### Presupuesto Nuevo (31_08_2026):
- Fecha de corte: **31 de agosto de 2026**

**Diferencia temporal:** 47 días (puedes haber nuevas transacciones, modificaciones, etc.)

---

## 5. DIFERENCIAS POTENCIALES IDENTIFICADAS

### ❌ **A VERIFICAR:**

1. **Período diferente:** 15_07 vs 31_08
   - Puede haber nuevos compromisos, obligaciones, pagos
   - Nuevos contratos registrados
   - Cancelaciones o reducciones

2. **Estructura de clasificación:**
   - Informe viejo: agrupa por PROYECTO + CONTRATO
   - Presupuesto completo: agrupa por RUBRO (código jerárquico)
   - **Falta identificar la relación PROYECTO ↔ RUBRO**

3. **Fuentes de presupuesto:**
   - Informe viejo menciona: SGP Educación, R. Propios, CRÉDITO IDEA 2025
   - Presupuesto completo: también incluye fondos (1.2.x, 1.3.x) y tipología
   - **¿Hay diferencia en clasificación de fuentes?**

4. **Rubros faltantes o añadidos:**
   - Informe viejo tiene 20+ proyectos visibles
   - Presupuesto completo tiene 1,777 rubros
   - **¿El informe viejo muestra solo rubros con movimiento?**
   - **¿Hay rubros en Hacienda sin movimiento que se excluyen del viejo?**

5. **Vigencias futuras (VF):**
   - Informe viejo menciona "VF Fortalecimiento..."
   - Presupuesto nuevo identifica vigencias futuras con CDP -YYYYNNN
   - **¿Cómo se clasificaban antes?**

---

## 6. PALETA DE COLORES PARA CODIFICAR (NECESITA CONFIRMACIÓN)

### Colores detectados en informe viejo (7 total):
- [ ] **Amarillo** = ?
- [ ] **Verde** = ?
- [ ] **Azul** = ?
- [ ] **Rojo** = ?
- [ ] **Naranja** = ?
- [ ] **Gris** = ?
- [ ] **Blanco/Sin color** = ?

**Probable significado:**
- Estados de ejecución (Pendiente, En curso, Completado, Alerta)
- Tipos de proyecto (Infraestructura, Servicios, Otros)
- Riesgo o prioridad
- Fuente de presupuesto

---

## SIGUIENTE PASO:

📋 **Necesitamos que confirmes:**

1. ¿Cuál es la **paleta de colores exacta** y su significado?
2. ¿El informe viejo **muestra TODOS los rubros** o solo los que tienen movimiento?
3. ¿Hay **rubros nuevos en 31_08** que no estaban en 15_07?
4. ¿Las **cifras debe ser idénticas** para el mismo período (15_07) o pueden variar?
5. ¿Hay **reajustes, traslados o reducciones** entre ambas fechas?

