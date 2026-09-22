# Cruce de Contratos por Columna "cdps" de Hacienda

## Resumen

Se implementó verificación de contratos contra la columna "cdps" del reporte de Hacienda. Esta columna contiene todos los números de CDP asociados a cada rubro presupuestal.

## Datos

- **Columna "cdps" en Hacienda**: 1.168 CDP únicos
- **Líneas de contrato cruzadas**: 54 totales
  - **40 líneas (74.1%)**: CDP verificado en columna "cdps" → cruce directo contra Hacienda
  - **14 líneas (25.9%)**: CDP no en "cdps" → fallback a código presupuestal

## CRP por método de cruce

| Método | Monto | % del CRP |
|--------|-------|----------|
| **ok** (CDP en cdps) | $56.318.866.250 | 56.8% |
| **ok_codigo** (fallback a código) | $29.346.872.200 | 29.6% |
| **vigencia_futura** | $13.141.714.369 | 13.3% |
| **sin_cdp** | $266.149.845 | 0.3% |

## Cambios técnicos

### 1. `extractor_contratos.py`

#### Nueva función: `_mapa_cdps_hacienda(path)`
- Lee la columna "cdps" directamente del reporte de Hacienda
- Construye mapa: CDP → [(cons_ppt, tail), ...]
- Cacheado para eficiencia

#### Mejoría: Campo `en_cdps` en cada línea
- Indica si el CDP fue verificado en la columna "cdps" de Hacienda
- `True`: CDP existe en "cdps" → cruce verificado contra Hacienda
- `False`: CDP no está en "cdps" → probablemente de vigencia anterior, usa fallback a código

#### Diagnóstico
- Imprime: cantidad de CDP únicos en columna "cdps"
- Imprime: porcentaje de líneas con CDP en "cdps"
- Useful para debugging de cruces fallidos

### 2. `dashboard_ejecutivo.html` (pestaña Contratos)

#### Mejoras visuales

**Badges actualizados:**
- `ok`: Ahora con checkmark (✓) para indicar verificación en "cdps"
- `ok_codigo`: Mantiene color dorado para fallback a código
- Agrupa visual: Verde verificado vs Dorado fallback

**Tabla de detalles:**
- Pequeño label "(en cdps)" junto al badge de estado
- Muestra si cada CDP individual fue verificado en Hacienda

**Aviso mejorado:**
- Explica la verificación de "cdps"
- Muestra porcentaje de CDP verificados
- Contexto sobre vigencias anteriores

## Por qué algunos CDP no están en "cdps"

Los CDP del archivo CDP-CRP que no aparecen en la columna "cdps" de Hacienda 2026 son:
1. **De vigencias anteriores**: CDP "93" de 2024-2025 no es lo mismo que CDP "93" de 2026
2. **Números reinician cada año**: Sistema de Hacienda asigna nuevos números anualmente
3. **Archivo CDP-CRP en SharePoint**: Fuente independiente, puede estar desfasado

Solución implementada: Fallback a **código presupuestal**, verificado y marcado explícitamente.

## Cómo verificar

```bash
cd SECRETARIA_EDUCACION
python extractor_contratos.py 2>&1 | grep -E "(debug|resumen)"
```

Resultado esperado:
```
debug: columna 'cdps' de Hacienda contiene 1168 CDP únicos
resumen: 40/54 líneas con CDP en columna 'cdps' (74.1%)
```

## Próximos pasos opcionales

1. **Sincronizar en tiempo real**: Conectar archivo SharePoint de CDP-CRP para actualizaciones automáticas
2. **Validación de CDP**: Crear rutina que detecte CDP de "vigencias futuras" vs "anteriores" automáticamente
3. **Dashboard mejorado**: Mostrar mapa visual de CDP por rubro

## Notas

- ✅ Cambios solo en pestaña de Contratos (presupuesto intacto)
- ✅ Todos los campos "en_cdps" se guardan en JSON
- ✅ Compatible con publicación a Netlify
- ✅ Diagnóstico detallado en stderr para debugging
