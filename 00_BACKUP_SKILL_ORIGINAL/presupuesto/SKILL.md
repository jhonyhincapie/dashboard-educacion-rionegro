---
name: presupuesto
description: Usar SIEMPRE que el usuario trabaje en presupuesto, finanzas, SGP (Sistema General de Participaciones), nómina docente/administrativa, aportes patronales, gastos de funcionamiento o inversión, CDP, RP, PAC, cierre de vigencia, cuentas maestras, o cualquier tema de administración de recursos de la Secretaría de Educación. Activar también con "presupuesto educativo", "recursos del sector educativo", "tipología educativa", "calidad educativa SGP", "tramitar presupuesto", "tramitar CDP", "clasificar gasto", "tipología por alumno", "aportes docentes", o cuando el usuario suba o mencione un documento presupuestal, informe de ejecución, o acto administrativo relacionado con recursos educativos. Activar incluso si la petición parece general (ej. "¿en qué se puede usar este recurso?") pero está enmarcada en el contexto de la Secretaría de Educación.
---

# Presupuesto — Secretaría de Educación

Skill puramente **conceptual y procedimental**. Su objetivo es que Claude
aplique correctamente la lógica, clasificación y trámites que definen las
guías del Ministerio de Educación Nacional para la administración de los
recursos del sector educativo — **nunca cifras, porcentajes ni valores en
pesos**, porque esos varían cada año y por entidad y no son el objeto de
esta skill.

Fuentes, en orden de prioridad:

1. `references/guia_men_2017_actualizacion.md` — actualización 2017 de la
   Guía No. 8. **Úsala primero.** Incorpora la Ley 1176 de 2007, el
   Decreto 1075 de 2015 (DUR Educación) y mecanismos que no existían en
   2004: Cuentas Maestras, FUT, SIFSE, Calidad-gratuidad separada de
   Calidad-matrícula, medidas de monitoreo y control, PAE, FONPET.
2. `references/estructura_guia_men_2004.md` — versión original de 2004.
   Úsala para lo que la actualización de 2017 no cubre (p. ej. el detalle
   fino del Anexo 1 de clasificación de nómina) o como contraste. Si las
   dos versiones difieren en estructura o trámite, prevalece la de 2017.

Lee el archivo de referencia relevante siempre que trabajes en algo de esta
skill — no la resumas de memoria.

## Regla central: solo conceptos, nunca cifras

Esta skill responde con: qué es cada recurso o rubro, cómo se llama, en qué
se puede y en qué NO se puede usar, qué requisitos y trámite sigue, qué
norma lo regula, y qué distingue a un concepto de otro (p. ej. Calidad-
matrícula vs. Calidad-gratuidad, o servicios personales asociados a la
nómina vs. servicios personales indirectos).

Esta skill **no** da: porcentajes de aportes, valores de tipología, tablas
salariales, montos de SGP, ni ningún número que dependa del año o del
presupuesto vigente de la entidad.

Si el usuario pide una cifra:
- No la busques ni la inventes como parte de esta skill.
- Responde el concepto que sí puedes dar: qué determina esa cifra, quién la
  fija (MEN, MinHacienda, DNP, decreto anual, etc.) y dónde se publica
  normalmente — sin dar el número.
- Si el usuario insiste en el número exacto, es una tarea aparte de
  búsqueda de información actual, no algo que esta skill deba resolver por
  defecto.

## Cómo trabajar según el tipo de tarea

### 1. Clasificar o explicar un concepto presupuestal
("¿esto es gasto de funcionamiento o de inversión?", "¿en qué rubro va este
pago?", "explícame qué es la cuota de administración", "¿qué es una cuenta
maestra?", "¿en qué se puede usar Calidad-matrícula?")

- Usa primero `guia_men_2017_actualizacion.md`; si el concepto no está ahí,
  usa `estructura_guia_men_2004.md`.
- Responde con la clasificación, la definición, los usos permitidos y
  prohibidos, y la norma que lo sustenta — sin mencionar montos.
- Si la pregunta coincide con alguno de los 20 temas del Anexo 1 de
  preguntas frecuentes de la guía 2017 (índice en la sección 10 de esa
  referencia), vale la pena releer esa pregunta específica en el PDF
  original antes de responder — son respuestas oficiales del MEN a casos
  concretos, no conviene generalizar desde otra sección.

### 2. Redactar un documento (informe de ejecución, acto administrativo,
memoria justificativa de modificación presupuestal, oficio)

- Sigue la estructura y el orden que describen las guías: componentes
  obligatorios, orden de prioridad del SGP, requisitos de una modificación
  presupuestal (exposición de motivos, justificación legal/económica,
  concepto previo de planeación si afecta inversión, CDP).
- Si el documento involucra cuentas del SGP-Educación, habla en términos de
  las 3 cuentas maestras (nómina / no-nómina / cancelaciones o Calidad-
  matrícula según el tipo de entidad) — no de las cuentas únicas que
  describía la guía de 2004.
- Si el usuario tiene activas las skills `bpms-rionegro`,
  `derechos-peticion-ica-rionegro` o `analizador-factura-saimyr`, ten en
  cuenta que esas cubren trámites tributarios (ICA) — son un dominio
  distinto al de presupuesto educativo (SGP). No mezclar la normativa de
  una con la otra.
- Deja los espacios de cifras (valores, porcentajes, fechas de decreto
  anual) como campos a completar por el usuario, en vez de rellenarlos con
  números de la guía o inventados.

### 3. Aplicar la normativa a un caso concreto (¿puedo pagar X con estos
recursos?, ¿qué trámite sigue esta modificación?, ¿a qué cuenta va este
giro?)

- Identifica primero de qué componente del SGP-Educación se trata
  (Prestación del servicio, Calidad-matrícula, Calidad-gratuidad,
  Cancelaciones, Alimentación escolar, recursos propios, etc.) — la
  respuesta cambia completamente según el componente.
- Aplica las listas de usos permitidos/prohibidos de la guía correspondiente
  tal cual están (son reglas, no cifras: por ejemplo, Calidad-matrícula
  nunca puede pagar gastos de personal, aseo/vigilancia, viáticos ni
  pruebas ICFES).
- Si el caso no encaja claramente en ninguna categoría, dilo explícitamente
  en vez de forzar una clasificación.

## Errores a evitar

- Dar cualquier porcentaje, valor en pesos, tabla salarial o cifra de
  distribución del SGP — ni de la guía ni de memoria ni buscado — porque el
  usuario ya indicó que esto no debe hacerlo esta skill.
- No distinguir el régimen del docente: Decreto-Ley 2277 de 1979 (antiguo)
  vs. Decreto-Ley 1278 de 2002 (nuevo) tienen reglas y trámites distintos
  aunque esta skill no dé sus tablas salariales.
- Mezclar terminología: "ARP" (guía 2004) hoy es "ARL"; "FNPSM" hoy es
  "FOMAG" — usa el término vigente al redactar documentos actuales, aunque
  cites la guía como fuente histórica.
- Confundir Calidad-matrícula oficial con Calidad-gratuidad — tienen
  fórmulas de distribución, cuentas maestras y usos permitidos distintos.
- Asumir que un trámite se resuelve solo con normativa nacional cuando
  depende del Estatuto de Presupuesto Municipal de Rionegro o del Plan de
  Desarrollo vigente (normativa local, no está en esta skill salvo que el
  usuario la suba).
