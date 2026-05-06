## Fuentes oficiales de datos

El portal consulta información desde fuentes públicas oficiales de Chile. Cada aplicación descarga, procesa y consolida datos desde las siguientes fuentes:

| Fuente | Institución | App asociada | Datos obtenidos | URL / patrón utilizado |
|---|---|---|---|---|
| Dólar observado | Servicio de Impuestos Internos, SII | Dólar SII / Consolidado Temporal | Dólar promedio mensual, último valor observado, último día observado | https://www.sii.cl/valores_y_fechas/dolar/dolar{anio}.htm |
| UTM / UTA / IPC valor puntos | Servicio de Impuestos Internos, SII | UTM SII / Consolidado Temporal | UTM, UTA, IPC valor puntos, variaciones mensuales y acumuladas | https://www.sii.cl/valores_y_fechas/utm/utm{anio}.htm |
| IPC General | Instituto Nacional de Estadísticas, INE | IPC INE / Consolidado Temporal | Índice IPC, variación mensual, variación acumulada, variación 12 meses | https://www.ine.gob.cl/estadisticas-por-tema/precios-e-inflacion/indice-de-precios-al-consumidor |
| ICL | Instituto Nacional de Estadísticas, INE | ICL INE / Consolidado Temporal | Índice de Remuneraciones y Costos Laborales, variaciones mensuales y anuales | https://www.ine.gob.cl/estadisticas-por-tema/mercado-laboral/remuneraciones-y-costos-laborales |
| Reajuste polinómico | Ministerio de Obras Públicas, MOP | MOP Reajuste Polinómico / Consolidado Temporal | IPC MOP, índice de remuneraciones, petróleo diésel, dólar observado, petróleo diésel refinería Concón | https://planeamiento.mop.gob.cl/indices-y-precios-para-calculo-del-reajuste-polinomico/ |
| Savings Bridge | Datos pegados por usuario | Savings Bridge | Conceptos y valores USD ingresados manualmente desde Excel | No usa fuente externa; el usuario pega la tabla en la app |

---

## Detalle de fuentes por aplicación

### Dólar SII

La app consulta el dólar observado desde el Servicio de Impuestos Internos.

Patrón utilizado:

https://www.sii.cl/valores_y_fechas/dolar/dolar{anio}.htm

Ejemplo:

https://www.sii.cl/valores_y_fechas/dolar/dolar2025.htm

Datos extraídos:

- Dolar promedio SII
- Dolar ultimo observado SII
- Dolar ultimo dia observado

La app busca la tabla que contiene día, meses abreviados y una fila de promedio.

---

### UTM SII

La app consulta la tabla anual de UTM desde el Servicio de Impuestos Internos.

Patrón utilizado:

https://www.sii.cl/valores_y_fechas/utm/utm{anio}.htm

Ejemplo:

https://www.sii.cl/valores_y_fechas/utm/utm2025.htm

Datos extraídos:

- UTM
- UTA
- IPC valor puntos SII
- UTM variacion mensual
- UTM variacion acumulado
- UTM variacion 12 meses

La app busca una tabla compatible que contenga referencias a Mes, UTM, UTA e IPC.

---

### IPC INE

La app consulta el IPC General desde el Instituto Nacional de Estadísticas.

Página principal:

https://www.ine.gob.cl/estadisticas-por-tema/precios-e-inflacion/indice-de-precios-al-consumidor

Archivo Excel directo usado como primera opción:

https://www.ine.gob.cl/docs/default-source/%C3%ADndice-de-precios-al-consumidor/cuadros-estadisticos/base-anual-2023_100/series-de-tiempo/ipc-xls.xlsx?sfvrsn=5b901f39_70

Archivo base usado como respaldo:

https://www.ine.gob.cl/docs/default-source/%C3%ADndice-de-precios-al-consumidor/cuadros-estadisticos/base-anual-2023_100/series-de-tiempo/ipc-xls.xlsx

Datos extraídos:

- IPC INE indice
- IPC INE variacion mensual
- IPC INE variacion acumulada
- IPC INE variacion 12 meses

La app intenta descargar primero la URL directa, luego la URL base sin `sfvrsn` y finalmente busca automáticamente enlaces Excel en la página oficial del INE.

---

### ICL INE

La app consulta el Índice de Remuneraciones y Costos Laborales desde el Instituto Nacional de Estadísticas.

Página principal:

https://www.ine.gob.cl/estadisticas-por-tema/mercado-laboral/remuneraciones-y-costos-laborales

Archivo Excel directo usado como primera opción:

https://www.ine.gob.cl/docs/default-source/sueldos-y-salarios/cuadros-estadisticos/ir-icl-base-anual-2023-100/series-base-2023/tabulado_icl.xlsx?sfvrsn=43d76e7c_50

Archivo base usado como respaldo:

https://www.ine.gob.cl/docs/default-source/sueldos-y-salarios/cuadros-estadisticos/ir-icl-base-anual-2023-100/series-base-2023/tabulado_icl.xlsx

Datos extraídos:

- ICL INE indice
- ICL INE variacion mensual
- ICL INE variacion acumulada
- ICL INE variacion 12 meses

La app intenta descargar primero la URL directa, luego la URL base sin `sfvrsn` y finalmente busca automáticamente enlaces Excel en la página oficial del INE.

---

### MOP Reajuste Polinómico

La app consulta archivos Excel publicados por el Ministerio de Obras Públicas.

Página principal:

https://planeamiento.mop.gob.cl/indices-y-precios-para-calculo-del-reajuste-polinomico/

Datos extraídos:

- MOP indice precios consumidor
- MOP indice remuneraciones
- MOP petroleo diesel
- MOP dolar observado
- MOP petroleo diesel refineria concon

La app busca enlaces a archivos `.xls` o `.xlsx`, detecta año y mes desde el nombre del archivo y luego busca los conceptos dentro de la planilla.

---

### Savings Bridge

La app Savings Bridge no consulta una fuente externa. El usuario pega manualmente una tabla copiada desde Excel.

Columnas esperadas:

- Concepto
- Valor_USD

La app procesa esos datos y genera un gráfico tipo Savings Bridge.
