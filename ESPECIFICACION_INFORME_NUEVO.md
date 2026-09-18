# ESPECIFICACIÓN: INFORME GERENCIAL AUTOMATIZADO
## Base: Presupuesto 15_07_2026

---

## 1. PALETA DE COLORES (Codificación por Componente)

| Color | Componente | Subtipos |
|-------|-----------|----------|
| **Amarillo Oscuro** | Prestación del Servicio (PS) | Nómina docente, personal administrativo |
| **Amarillo Claro** | RF/RB de Prestación del Servicio | Rendimientos Financieros o Recursos Balance |
| **Azul Oscuro** | SGP, PNG, PAE | Calidad Matrícula, Calidad Gratuidad |
| **Azul Claro** | RF/RB de SGP, PNG, PAE | Rendimientos o Recursos de Balance |
| **Verde Oscuro** | Calidad Matrícula | Mejora de cobertura/calidad |
| **Verde Claro** | RF/RB de Calidad Matrícula | Rendimientos o Recursos de Balance |
| **Naranja** | Calidad Gratuidad | Programas de gratuidad |
| **Rosado** | Primera Infancia | Programas PIE |

---

## 2. MAPEO DE DATOS: HACIENDA → INFORME

### Origen: `Presupuesto de egreso a DD_MM_YYYY.xls`

| Valor en Informe | Columna en Hacienda | Fórmula |
|------------------|---------------------|---------|
| **Ppto. Definitivo** | `tot_ppto` | Directo |
| **Reservado CDP** | `tot_reserv` | Directo |
| **Comprometido RP** | `tot_crp` | Directo |
| **Obligado OPS** | `tot_ops` | Directo |
| **Pagado** | `tot_pag` | Directo |
| **Sin reservar** | `tot_ppto - tot_reserv` | Gap 1 |
| **Sin comprometer** | `tot_reserv - tot_crp` | Gap 2 |
| **Sin obligar** | `tot_crp - tot_ops` | Gap 3 |
| **% Comp** | `tot_crp / tot_ppto` | Porcentaje ejecución |
| **% Pag** | `tot_pag / tot_ppto` | Porcentaje pago |

### Filtros aplicados:
- ✅ `final = 'S'` (solo filas finales)
- ✅ NO incluir "CIERRE DE RESERVAS"
- ✅ `codigo_rubro` comienza con `02.01` (Educación)
- ✅ MOSTRAR TODOS los rubros (incluso sin movimiento)

### Clasificación por Componente:
- Usar `descripcion_fuente` para mapear a componente
- Si es "PRESTACION" → Amarillo
- Si es "SGP" + "EDUCACION" → Azul
- Si es "MATRICULA" → Verde
- Si es "GRATUIDAD" → Naranja
- Etc.

---

## 3. ESTRUCTURA DEL INFORME NUEVO

### **HOJA 1: EJECUTIVO** (Gerencial - TOTALES por Componente)

#### Encabezado:
```
SEGUIMIENTO PRESUPUESTAL — SECRETARIA DE EDUCACION DE RIONEGRO
Corte: DD/MM/YYYY
Fuente: Presupuesto de egreso [archivo] | Generado: [fecha] | Rubros: [cantidad]
```

#### Tabla de TOTALES POR COMPONENTE:
| Componente | Ppto. Definitivo | Reservado | Comprometido | % Comp | Pagado | % Pag | Sin Reservar | Sin Comprometer | Responsable |
|-----------|:----:|:----:|:----:|:---:|:---:|:---:|:---:|:---:|--------|
| **Amarillo Oscuro** SGP Prestación Servicio | $XXX | $XXX | $XXX | 71% | $XXX | 42% | $XXX | $XXX | [Nombre] |
| **Azul Oscuro** SGP Calidad-Matrícula | $XXX | $XXX | $XXX | XX% | $XXX | XX% | $XXX | $XXX | [Nombre] |
| **Verde Oscuro** Calidad-Gratuidad | $XXX | $XXX | $XXX | XX% | $XXX | XX% | $XXX | $XXX | [Nombre] |
| Naranja PAE | $XXX | $XXX | $XXX | XX% | $XXX | XX% | $XXX | $XXX | [Nombre] |
| Rosado Primera Infancia | $XXX | $XXX | $XXX | XX% | $XXX | XX% | $XXX | $XXX | [Nombre] |
| **TOTAL EDUCACIÓN** | **$217.4B** | **$165.0B** | **$154.8B** | **71.2%** | **$92.1B** | **42.4%** | **$52.4B** | **$10.1B** | --- |

#### Gráficos:
- Brecha de ejecución (barras: Sin reservar, Sin comprometer, Sin obligar)
- Participación por Componente (pie chart)
- Avance de ejecución (línea: %Comp, %Pag)

#### Alertas:
- 🔴 Rubros sin comprometer (umbral: < 10%)
- 🟡 Rubros con brecha alta
- 🟢 Rubros completamente ejecutados

---

### **HOJA 2: SEGUIMIENTO** (Detalle por Rubro)

#### Tabla: Cada rubro de Educación en una fila
| Componente | Código Rubro | Proyecto/Rubro | Fondo | Fuente | Definit | Reserv | Compromet | Obligado | Pagado | %Comp | %Pag | Sin Reservar | Sin Comprometer | Sin Obligar | Responsable | Observación |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|--------|--------|
| [Color] | 02.01.2.3.1.xxx | Nomina Docentes | 1.2.1 | SGP PS | $89.7B | $42.3B | $42.3B | $42.3B | $XX | 47% | 47% | $47.4B | $0 | $0 | Juan | --- |
| [Color] | 02.01.2.3.2.xxx | Infraestructura | 1.2.2 | SGP PS | $11.5B | $11.5B | $10.3B | $1.2B | $XX | 90% | 10% | $0 | $1.2B | $9.1B | Maria | ⚠️ Alerta |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

#### Subtotales por Componente:
Al final de cada grupo de componente, fila de SUBTOTAL.

#### TOTAL GENERAL al final.

---

### **HOJA 3: CONTRATOS** (Integración CDP-CRP)

#### Tabla: Cada contrato en una fila
| Nro Contrato | Contratista | Objeto | cons_ppt | Proyecto/Rubro | Componente | Fuente | Valor Contrato | Comprometido | Obligado | Pagado | %Ejec | CDP | Vig Futura | Estado | Supervisor | Observación |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 2024-001 | EQUIDE | Infraestructura | 3726 | Infraestructura IE | Prestación | SGP | $500M | $400M | $400M | $200M | 50% | 20241412 | 2024 | En curso | Juan | --- |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

#### CONCILIACIÓN RUBRO vs CONTRATOS:
| cons_ppt | Proyecto / Rubro | Comprometido Rubro (Hacienda) | Suma de Contratos | Diferencia | Nota |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 3726 | Nomina Docente | $42.3B | $42.3B | $0 | ✅ OK |
| 6640 | Infraestructura | $11.5B | $8.9B | $2.6B | ⚠️ Faltan contratos |

---

## 4. ORDEN Y AGRUPACIÓN

### Orden de Componentes en el informe:
1. **Amarillo Oscuro** - Prestación del Servicio (PS)
2. **Azul Oscuro** - SGP Educación (sin especificidad)
3. **Verde Oscuro** - Calidad Matrícula
4. **Azul Claro** - SGP Calidad-Gratuidad
5. **Naranja** - PAE
6. **Rosado** - Primera Infancia
7. **Gris/Otros** - Otras fuentes

### Dentro de cada Componente:
- Ordenar por `codigo_rubro` (ascendente)

### Vigencias Futuras (VF):
- Se marcan en la columna "Vig Futura" con el año (2024, 2025, etc.)
- Se agrupan al final de cada componente
- Se colorean ligeramente diferente (tonos más claros)

---

## 5. CÁLCULOS ESPECIALES

### Brecha de Ejecución:
```
Sin reservar = Definitivo - Reservado
Sin comprometer = Reservado - Comprometido  
Sin obligar = Comprometido - Obligado
```

### Porcentajes:
```
% Comprometido = Comprometido / Definitivo
% Pagado = Pagado / Definitivo
% Ejecución Contrato = Pagado / Valor Contrato
```

### Alertas Automáticas:
- 🔴 CRÍTICA: Sin comprometer > 50% del Definitivo
- 🟡 ALTA: Sin comprometer entre 20-50%
- 🟢 OK: Sin comprometer < 20%

---

## 6. ENTRADA DE DATOS

### Archivo obligatorio:
- `Presupuesto de egreso a DD_MM_YYYY.xls` (en carpeta `entradas\`)

### Archivos opcionales (enriquecimiento):
- `seguimiento_manual_educacion.xlsx` → RUBROS, CONTRATOS (manual)
- `Seguimiento CDP-CRP...xlsx` → CONTRATOS automáticos (vigencias futuras)
- `maestro_rubros_educacion.xlsx` → INCLUSIONES, EXCLUSIONES, REGLA_BASE

---

## 7. SALIDA (DELIVERABLE)

### Archivo generado:
- `Seguimiento Presupuestal Educacion a DD_MM_YYYY.xlsx`
- Ubicación: `informes\`
- 3 hojas: EJECUTIVO | SEGUIMIENTO | CONTRATOS
- Colores: Codificación por componente
- Totales: Automáticos con fórmulas

### Complementos:
- `historial_corridas.csv` → Registro de cada generación
- Carpeta `informes\` abre automáticamente tras generación

---

## 8. TIMELINE DE IMPLEMENTACIÓN

| Fase | Tarea | Duración | Estatus |
|------|-------|----------|---------|
| **1** | Adaptar extractor a paleta de colores | 2-3h | ⏳ Por hacer |
| **2** | Crear hoja EJECUTIVO (totales por componente) | 3-4h | ⏳ Por hacer |
| **3** | Validar cálculos de GAPs y porcentajes | 1-2h | ⏳ Por hacer |
| **4** | Integrar CDP-CRP en hoja CONTRATOS | 2-3h | ✅ Parcial (done) |
| **5** | Agregar gráficos y formateo visual | 2-3h | ⏳ Por hacer |
| **6** | Alertas automáticas | 1-2h | ⏳ Por hacer |
| **7** | Testing con datos reales (15_07 vs 31_08) | 2-3h | ⏳ Por hacer |
| **TOTAL** | | ~15-20h | ⏳ |

---

## 9. CHECKLIST DE VALIDACIÓN

Cuando el informe esté listo, verificar:

- [ ] Hoja EJECUTIVO muestra totales correctos por componente
- [ ] Cifras de Definitivo, Reservado, Comprometido, Obligado, Pagado coinciden con Hacienda
- [ ] % Comp y % Pag son correctos
- [ ] GAPs (Sin reservar, Sin comprometer, Sin obligar) suman correctamente
- [ ] Colores se aplican correctamente según componente
- [ ] Vigencias futuras (VF) se marcan con año (2024, 2025, etc.)
- [ ] Hoja SEGUIMIENTO muestra TODOS los rubros (130 de Educación)
- [ ] Hoja CONTRATOS muestra 8 contratos CDP-CRP + contratos manuales
- [ ] CONCILIACIÓN rubro vs contratos es correcta
- [ ] Totales GENERALES coinciden en todas las hojas
- [ ] .bat genera informe sin errores
- [ ] Informe abre carpeta `informes\` automáticamente

