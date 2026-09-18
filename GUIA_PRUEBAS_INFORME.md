# 📋 GUÍA DE PRUEBAS - INFORME GERENCIAL V1

---

## PASO 1: ABRIR EL INFORME

### Archivo a revisar:
```
C:\Users\jhincapie\OneDrive - Municipio de Rionegro\Escritorio\EDUCACIÓN\2026\RIONEGRO_EDUCACION_AI\SECRETARIA_EDUCACION\informes\
→ Seguimiento Presupuestal Educacion a 15_07_2026.xlsx
```

### Cómo abrirlo:
1. **Doble clic** en el archivo
2. Espera a que Excel lo cargue completamente
3. Ve a la hoja **EJECUTIVO** (primera pestaña)

---

## PASO 2: REVISAR LA HOJA EJECUTIVO

### 2.1 - Encabezado (Filas 1-3)
- [ ] Título: "SEGUIMIENTO PRESUPUESTAL — SECRETARIA DE EDUCACION DE RIONEGRO"
- [ ] Corte: "15/07/2026"
- [ ] Fuente: Muestra el archivo y fecha de generación

### 2.2 - Tarjetas de Resumen (Filas 5-9)
Revisa estas 4 tarjetas en la parte superior:
```
PRESUPUESTO DEFINITIVO    COMPROMETIDO (RP)    OBLIGADO (OPS)    PAGADO
$217,398,575,793          $134,063,202,417     $XX,XXX,XXX,XXX   $XX,XXX,XXX,XXX
(base 100%)               61.7%                XX%               XX%
```

**Validación:**
- ✅ Definitivo = $217,398,575,793 (debe ser exacto)
- ✅ Comprometido = $134,063,202,417 (61.7%)
- ✅ % Pagado: ?% (espera el valor)
- ⚠️ **Si los números no coinciden:** ¡ALERTA! Reporta la diferencia

### 2.3 - Brecha de Ejecución (Filas 11-13)
```
Sin reservar (Definitivo - Reservado)     = $XX,XXX,XXX,XXX
Sin comprometer (Reservado - Comprometido) = $XX,XXX,XXX,XXX
Sin obligar (Comprometido - Obligado)     = $XX,XXX,XXX,XXX
```

**Validación:**
- [ ] Sin reservar + Comprometido = Definitivo ✓
- [ ] Sin comprometer + Comprometido = Reservado ✓
- [ ] Sin obligar + Obligado = Comprometido ✓

---

## PASO 3: TABLA "SEGUIMIENTO POR COMPONENTE"

Esta es la **tabla más importante** — revisa cuidadosamente:

### Estructura (Filas 15+):
| Componente | Ppto. Definitivo | Reservado | Comprometido | Obligado | Pagado | %Comp | %Pag | Sin Reservar | Sin Comprometer | Sin Obligar |

### 3.1 - Verificar COLORES por Componente

**Amarillo oscuro** = Prestación del Servicio (PS):
- [ ] Nombre debe decir "SGP Prestacion del Servicio"
- [ ] Fondo de fila AMARILLO
- [ ] Ejemplo cifra: $89,671,325,461 (aprox)

**Verde oscuro** = Calidad Matrícula:
- [ ] Nombre debe decir "SGP Calidad-Matricula"
- [ ] Fondo de fila VERDE
- [ ] Debe tener cifras

**Naranja** = Calidad Gratuidad:
- [ ] Nombre debe decir "SGP Calidad-Gratuidad"
- [ ] Fondo de fila NARANJA
- [ ] Debe tener cifras

**Azul oscuro** = SGP y PAE:
- [ ] "Alimentacion Escolar (PAE)" → AZUL
- [ ] "SGP Proposito General" → AZUL
- [ ] Fondo de fila AZUL

**Gris** = Otras fuentes:
- [ ] "Recursos Propios / Libre Destinacion" → GRIS
- [ ] "Recursos de Credito" → GRIS
- [ ] "Estampillas" → GRIS
- [ ] "Otras fuentes" → GRIS
- [ ] Fondo de fila GRIS CLARO

### 3.2 - Verificar CÁLCULOS por Componente

Para **cada fila** de componente, validar:

```
[A] % Comp = Comprometido / Definitivo
    Ejemplo: Si Comp=$134B y Def=$217B → 61.7% ✓

[B] % Pag = Pagado / Definitivo
    Ejemplo: Si Pag=$64B y Def=$217B → 29.6% ✓

[C] Sin Reservar = Definitivo - Reservado
    Deben ser cifras positivas (no negativas)

[D] Sin Comprometer = Reservado - Comprometido
    Deben ser cifras positivas

[E] Sin Obligar = Comprometido - Obligado
    Deben ser cifras positivas
```

**Checklist de validación:**

Para cada componente:
- [ ] Definitivo ≥ 0
- [ ] Reservado ≤ Definitivo
- [ ] Comprometido ≤ Reservado
- [ ] Obligado ≤ Comprometido
- [ ] Pagado ≤ Obligado
- [ ] % Comp está entre 0% y 100%
- [ ] % Pag está entre 0% y 100%

### 3.3 - TOTAL GENERAL (última fila de la tabla)

```
TOTAL EDUCACIÓN | $217,398,575,793 | $XX,XXX | $134,063,202,417 | $XX,XXX | $XX,XXX | 61.7% | XX% | $XX | $XX | $XX
```

**Validación CRÍTICA:**
- [ ] TOTAL Definitivo = Suma de todos componentes
- [ ] TOTAL Comprometido = Suma de todos componentes
- [ ] TOTAL Obligado = Suma de todos componentes
- [ ] TOTAL Pagado = Suma de todos componentes
- [ ] TOTAL % Comp = TOTAL Comprometido / TOTAL Definitivo
- [ ] TOTAL % Pag = TOTAL Pagado / TOTAL Definitivo

---

## PASO 4: REVISAR HOJA "SEGUIMIENTO"

Esta hoja muestra **cada rubro individualmente**:

### 4.1 - Estructura
- [ ] Debe haber **130 filas** de rubros (+ 1 encabezado + 1-2 totales)
- [ ] Cada rubro tiene: Componente | Código | Proyecto | Fondo | Fuente | Def | Reserv | Comp | Obl | Pag | %Comp | %Pag | ...

### 4.2 - Validación de colores
- [ ] Los colores de componente se repiten aquí también
- [ ] Cada rubro tiene el color correcto según su componente

### 4.3 - Totales de hoja
- [ ] Última fila debe ser "TOTAL" con sumas
- [ ] TOTAL Definitivo = $217,398,575,793 (debe coincidir con EJECUTIVO)

---

## PASO 5: REVISAR HOJA "CONTRATOS"

### 5.1 - Número de contratos
- [ ] Debe haber **8 filas** del CDP-CRP (2 EQUIDE + 5 SIN_CODIGO + 1 CORPOASES)
- [ ] + Cualquier contrato manual que hayas agregado

### 5.2 - Datos de cada contrato
Para cada contrato, verificar:
- [ ] Nro Contrato: debe tener valor
- [ ] Contratista: EQUIDE, CORPOASES, ESO RIONEGRO, etc.
- [ ] cons_ppt: código de referencia
- [ ] Valor Contrato: cifra positiva
- [ ] Comprometido: <= Valor Contrato
- [ ] Pagado: <= Comprometido
- [ ] % Ejecución: Pagado / Valor Contrato

### 5.3 - Sección "CONCILIACIÓN RUBRO vs CONTRATOS"
Debe mostrar:
```
cons_ppt | Proyecto/Rubro | Comprometido Rubro | Suma Contratos | Diferencia | Nota
```

- [ ] Para cada rubro: Diferencia = Comprometido Rubro - Suma Contratos
- [ ] Si Diferencia > 0: Nota dice "Faltan contratos"
- [ ] Si Diferencia = 0: Nota dice "OK"

---

## PASO 6: COMPARACIÓN CON INFORME VIEJO

### Abre AMBOS archivos lado a lado:

**Informe VIEJO:**
```
C:\Users\jhincapie\Downloads\07-15 Seguimiento al presupuesto para claude.xlsx
```

**Informe NUEVO:**
```
C:\Users\jhincapie\OneDrive\...\Seguimiento Presupuestal Educacion a 15_07_2026.xlsx
```

### 6.1 - Comparar CIFRAS TOTALES

| Concepto | Viejo | Nuevo | Diferencia | ¿OK? |
|----------|-------|-------|------------|------|
| Ppto. Definitivo | $217.4B | $217.4B | $0 | ✓ |
| Comprometido | $134.1B | $134.1B | $0 | ✓ |
| Pagado | $64.3B? | $64.3B? | ? | ? |

**Si hay diferencia > $1M:**
- 🔴 **ALERTA** → Reporta la cifra diferente y dónde la viste

### 6.2 - Comparar COMPONENTES

Verifica que en ambos informes aparezcan los mismos componentes con cifras similares:
- [ ] Prestación del Servicio (Nómina): $89.7B (aprox)
- [ ] Calidad Matrícula: $XX.XB
- [ ] Calidad Gratuidad: $XX.XB
- [ ] PAE: $XX.XB
- [ ] Otros: ...

---

## PASO 7: VALIDACIÓN DE COLORES

Abre el archivo nuevo y revisa:

| Componente | Color Esperado | Color Real | ¿Coincide? |
|-----------|----------------|-----------|-----------|
| Prestación del Servicio | Amarillo Oscuro (FFD966) | ? | [ ] |
| Calidad-Matrícula | Verde Oscuro (70AD47) | ? | [ ] |
| Calidad-Gratuidad | Naranja (FFC000) | ? | [ ] |
| PAE / SGP General | Azul Oscuro (4472C4) | ? | [ ] |
| Otras Fuentes | Gris (E7E6E6) | ? | [ ] |

**Si los colores NO coinciden:**
- Anota cuál es diferente
- Envía screenshot

---

## PASO 8: REPORTAR RESULTADOS

### Si TODO ESTÁ OK:
```
✅ Informe validado correctamente:
   - Cifras coinciden con presupuesto Hacienda
   - Colores aplicados correctamente
   - Cálculos validados (gaps, %, totales)
   - 130 rubros + 8 contratos presentes
   → Listo para Fase 2 (gráficos)
```

### Si HAY PROBLEMAS:
```
❌ Problemas encontrados:

1. CIFRAS:
   - Componente XYZ tiene diferencia de $XXX
   - Ubicación: [Hoja / Fila]
   
2. COLORES:
   - Componente XYZ debería ser [color] pero aparece [color]
   
3. CÁLCULOS:
   - Fila XYZ: % Comp no cuadra (muestra XX%, debería ser YY%)
   
4. DATOS:
   - Faltan rubros / Sobran rubros
   - Faltan contratos
   - ...

→ [Adjunta screenshot]
```

---

## RÁPIDO: CHECKLIST DE 2 MINUTOS

Si tienes prisa, revisa SOLO esto:

- [ ] Abre archivo → Hoja EJECUTIVO
- [ ] TOTAL Definitivo = $217,398,575,793 ✓
- [ ] TOTAL Comprometido = $134,063,202,417 ✓
- [ ] Tabla POR COMPONENTE visible con colores ✓
- [ ] 5-6 componentes con cifras (Amarillo, Verde, Naranja, Azul, Gris) ✓
- [ ] TOTAL row al final con valores ✓
- [ ] Hoja SEGUIMIENTO tiene 130+ rubros ✓
- [ ] Hoja CONTRATOS tiene 8 contratos ✓

**Si todos esos puntos = ✓ → Informe funciona correctamente**

---

## CONTACTO PARA REPORTES

Cuando termines las pruebas, envía:

```
PRUEBAS COMPLETADAS - [DD/MM/YYYY]

RESULTADO GENERAL: ✅ OK / ⚠️ PROBLEMAS MENORES / ❌ PROBLEMAS CRÍTICOS

DETALLES:
[Copia el checklist completado de arriba]

OBSERVACIONES:
[Cualquier nota adicional]

CAPTURAS/ARCHIVOS:
[Adjunta screenshots si hay problemas]
```

