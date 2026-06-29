import streamlit as st
import pandas as pd
import os

CARPETA = "Base de datos"
HOJA = None

st.set_page_config(page_title="LEONIS PRO", page_icon="🦁", layout="wide")

st.title("🦁 LEONIS PRO")
st.caption("Tu asistente de ventas")

archivos = [a for a in os.listdir(CARPETA) if a.endswith(".xlsx")]
archivo_seleccionado = st.selectbox("📂 Base de datos activa", archivos)

ARCHIVO_EXCEL = os.path.join(CARPETA, archivo_seleccionado)

if "cotizacion" not in st.session_state:
    st.session_state.cotizacion = []


@st.cache_data
def cargar_datos(archivo):
    df = pd.read_excel(
        archivo,
        sheet_name=0
        header=3
    )

    df = df[["CÓDIGO", "CODIGO", "PRES.", "DESCRIPCIÓN", "P LISTA"]]

    for col in ["CÓDIGO", "CODIGO", "PRES.", "DESCRIPCIÓN"]:
        df[col] = df[col].fillna("").astype(str).replace("nan", "")

    familia_actual = ""
    productos = []

    for _, fila in df.iterrows():
        codigo = fila["CÓDIGO"].strip()
        descripcion = fila["DESCRIPCIÓN"].strip()
        precio = fila["P LISTA"]

        if pd.isna(precio):
            if codigo != "":
                familia_actual = codigo
            productos.append("")
            continue

        if familia_actual and descripcion:
            producto = f"{familia_actual} - {descripcion}"
        else:
            producto = descripcion

        productos.append(producto)

    df["PRODUCTO"] = productos
    df = df.dropna(subset=["P LISTA"])
    df = df[df["PRODUCTO"].str.strip() != ""]

    return df


def calcular_precio(precio_lista, medio, mayoreo, pago_cdo, promocion):
    precio = precio_lista * 1.16
    precio *= (1 - medio / 100)
    precio *= (1 - mayoreo / 100)
    precio *= (1 - pago_cdo / 100)
    precio *= (1 - promocion / 100)
    return round(precio, 2)


def agregar_producto(producto):
    for item in st.session_state.cotizacion:
        if item["clave"] == producto["clave"] and item["sap"] == producto["sap"]:
            item["cantidad"] += producto["cantidad"]
            item["total"] = item["cantidad"] * item["precio"]
            return

    st.session_state.cotizacion.append(producto)


def generar_mensaje(cotizacion):
    total_general = sum(item["total"] for item in cotizacion)

    lineas = [
        "Buenas tardes.",
        "",
        "Le comparto la cotización solicitada:",
        ""
    ]

    for item in cotizacion:
        lineas.append(f"• {item['producto']} - {item['presentacion']}")
        lineas.append(f"  {item['cantidad']} × ${item['precio']:,.2f} = ${item['total']:,.2f}")
        lineas.append("")

    lineas.append(f"TOTAL: ${total_general:,.2f}")
    lineas.append("")
    lineas.append("Quedo atento a sus comentarios.")
    lineas.append("")
    lineas.append("*Sujeto a cambio sin previo aviso.*")

    return "\n".join(lineas)


df = cargar_datos(ARCHIVO_EXCEL)

st.divider()

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    medio = st.number_input("Medio mayoreo", value=25.0)

with c2:
    mayoreo = st.number_input("Mayoreo", value=5.0)

with c3:
    pago_cdo = st.number_input("Pago cdo", value=5.0)

with c4:
    promocion = st.number_input("Promoción", value=0.0)

with c5:
    cantidad = st.number_input("Cantidad", min_value=1, value=1)

busqueda = st.text_input("🔎 Escribe una clave, SAP o descripción")

if busqueda:
    texto = busqueda.upper().strip()

    resultados = df[
        df["CÓDIGO"].str.upper().str.contains(texto, na=False)
        |
        df["CODIGO"].str.upper().str.contains(texto, na=False)
        |
        df["PRODUCTO"].str.upper().str.contains(texto, na=False)
    ]

    if resultados.empty:
        st.warning("No encontré productos con esa búsqueda.")
    else:
        for i, fila in resultados.iterrows():
            precio_lista = float(fila["P LISTA"])
            precio_neto = calcular_precio(precio_lista, medio, mayoreo, pago_cdo, promocion)
            total = precio_neto * cantidad

            st.divider()
            st.subheader(f"🛢️ {fila['PRODUCTO']}")

            info, precios = st.columns(2)

            with info:
                st.write(f"📦 **Presentación:** {fila['PRES.']}")
                st.write(f"🔢 **Clave:** {fila['CÓDIGO']}")
                st.write(f"🏷️ **SAP:** {fila['CODIGO']}")

            with precios:
                st.markdown("### 💰 Precio neto")
                st.markdown(f"# ${precio_neto:,.2f}")
                st.write(f"💵 **Precio lista:** ${precio_lista:,.2f}")
                st.write(f"📦 **Cantidad:** {cantidad}")
                st.markdown(f"## Total: ${total:,.2f}")

                if st.button("➕ Agregar a cotización", key=f"agregar_{i}"):
                    producto = {
                        "producto": fila["PRODUCTO"],
                        "presentacion": fila["PRES."],
                        "clave": fila["CÓDIGO"],
                        "sap": fila["CODIGO"],
                        "cantidad": cantidad,
                        "precio": precio_neto,
                        "total": total,
                    }

                    agregar_producto(producto)
                    st.success("Producto agregado.")


st.divider()
st.header("🧾 Cotización")

if not st.session_state.cotizacion:
    st.info("Aún no has agregado productos.")
else:
    total_general = 0

    for idx, item in enumerate(st.session_state.cotizacion):
        col_a, col_b, col_c = st.columns([5, 3, 1])

        with col_a:
            st.write(f"🛢️ **{item['producto']}**")
            st.caption(f"{item['presentacion']} | Clave: {item['clave']} | SAP: {item['sap']}")

        with col_b:
            nueva_cantidad = st.number_input(
                "Cantidad",
                min_value=1,
                value=int(item["cantidad"]),
                key=f"cantidad_cot_{idx}"
            )

            item["cantidad"] = nueva_cantidad
            item["total"] = item["cantidad"] * item["precio"]

            st.write(f"{item['cantidad']} × ${item['precio']:,.2f} = **${item['total']:,.2f}**")

        with col_c:
            if st.button("❌", key=f"eliminar_{idx}"):
                st.session_state.cotizacion.pop(idx)
                st.rerun()

        total_general += item["total"]

    st.markdown("---")
    st.markdown(f"## TOTAL: ${total_general:,.2f}")

    mensaje = generar_mensaje(st.session_state.cotizacion)

    st.text_area("📲 Copia este mensaje para WhatsApp", mensaje, height=260)
    st.caption("Selecciona el texto, copia y pega en WhatsApp.")

    if st.button("🗑 Vaciar cotización"):
        st.session_state.cotizacion = []
        st.rerun()

st.divider()
st.caption("Desarrollado por Iván Hernández • con ChatGPT")