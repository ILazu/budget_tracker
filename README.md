
# Desglose Económico Mensual — Streamlit

Este proyecto crea un **dashboard web** para gestionar el presupuesto mensual del consejo estudiantil con:
- Un (1) archivo Excel **por año**: `desglose_económico_esc_teo.xlsx`
- Una hoja **por mes**, creada automáticamente al ingresar datos
- Registro de **donaciones** y **gastos** (solo *Comida y Meriendas*)
- **Gráficas** de pastel: (1) Saldo previo vs Donaciones, (2) Gastado vs Restante
- **QR** para compartir un enlace público en modo solo lectura

## Requisitos

```bash
pip install -r requirements.txt
```

## Uso local

```bash
streamlit run app.py
```

Esto abrirá el dashboard en tu navegador (por defecto en `http://localhost:8501`).

## Modo solo lectura / edición

- La app arranca por defecto en **modo solo lectura** (toggle arriba a la derecha).
- Para **habilitar edición** en producción, define un `ADMIN_CODE` en *Secrets* de Streamlit Cloud y compártelo solo con tesoreros/administradores.

## Deploy (gratuito) en Streamlit Community Cloud

1. Sube estos archivos a un repositorio en GitHub.
2. Ve a https://streamlit.io/cloud y crea una app apuntando a `app.py`.
3. En **Secrets** añade:
   ```
   ADMIN_CODE = "tu_codigo_secreto"
   ```
4. Copia la URL pública de tu app (por ejemplo, `https://tu-app.streamlit.app/`).
5. En el dashboard, pega esa URL en “URL pública del dashboard” y presiona **Generar QR**.
6. Descarga el QR y compártelo con los estudiantes para que **solo vean** las tablas y gráficas.

## Estructura del archivo Excel

- Archivo por año: `desglose_económico_esc_teo.xlsx`
- Hojas por mes: “Enero 2025”, “Febrero 2025”, etc.
- Cada hoja contiene dos tablas:
  - **Donaciones** (Fecha, Descripción, Monto)
  - **Gastos (Comida y Meriendas)** (Fecha, Descripción, Monto)

El **Saldo previo** de un mes se calcula automáticamente sumando/ restando desde enero:
`saldo_prev(m) = saldo_prev(enero) + Σ(donaciones) - Σ(gastos)` de los meses anteriores.

## Nota sobre el saldo inicial

En la barra lateral puedes indicar el **saldo previo de enero** (si empiezas a mitad de año con un remanente). Si ya tienes meses registrados, ese valor se ignora.

---

© Student Council Budget • Streamlit
