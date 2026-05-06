# Consolidado Temporal de Indicadores ENAEX

Aplicación Streamlit para generar una base temporal mensual consolidada con indicadores provenientes de distintas fuentes públicas: SII, INE y MOP.

La app permite seleccionar años, consultar automáticamente las fuentes disponibles, consolidar la información por `Año`, `Mes` y `Fecha`, visualizar gráficos temporales y descargar archivos Excel completos o resumidos.

---

## Estructura del proyecto

```text
PROYECTOS-ENAEX/
│
├── README.md
├── requirements.txt
├── assets/
│   └── logo.svg
│
├── app_enaex_global/
│   └── app_enaex_global.py
│
├── app_consolidado_temporal/
│   └── app_consolidado_temporal.py
│
├── app_sii_dolar/
│   └── app_sii_dolar.py
│
├── app_sii_utm/
│   └── app_sii_utm.py
│
├── app_ine_ipc/
│   └── app_ine_ipc.py
│
├── app_ine_icl/
│   └── app_ine_icl.py
│
├── app_indice_polinomico_mop/
│   └── app_indice_polinomico_mop.py
│
└── app_sievo/
    └── app_sievo.py
