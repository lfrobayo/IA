import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# Leer archivo
archivo = "Datos.xlsx"
df = pd.read_excel(archivo, sheet_name="Hidraulica")

# Reemplazar valores no válidos
df.replace(["s/d", "ND", "n.d", "...", ""], np.nan, inplace=True)

# Definir columnas relevantes
columnas_numericas = [
    "Promedio",
    "Reg.Hidrológica",
    "Escorrentía mm/año",
    "Prcp Mapa C mm/año",
    "Prcp Mapa D mm/año"
]
df = df[["Departamento"] + columnas_numericas].copy()

# Convertir a numérico y limpiar
for col in columnas_numericas:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df = df.dropna()
df["Departamento"] = df["Departamento"].str.strip().str.title()

# Escalado
X_scaled = StandardScaler().fit_transform(df[columnas_numericas])

# K-means clustering
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df["Cluster"] = kmeans.fit_predict(X_scaled)

# Clasificación según promedio general del cluster
media_por_cluster = df.groupby("Cluster")[columnas_numericas].mean().mean(axis=1)
orden = media_por_cluster.sort_values().index
etiquetas = {
    orden[0]: "No óptimo",
    orden[1]: "Variable",
    orden[2]: "Óptimo"
}
df["Clasificación Hidraulica"] = df["Cluster"].map(etiquetas)

# Guardar resultado
df_resultado = df[["Departamento", "Clasificación Hidraulica"]].copy()
df_resultado["Departamento"] = df_resultado["Departamento"].str.strip().str.title()
df_resultado.to_excel("Clasificación_Hidraulica.xlsx", index=False)

print("✅ Archivo 'Clasificación_Hidraulica.xlsx' generado correctamente.")

# Leer geojson del mapa de Colombia
mapa_colombia = gpd.read_file("Colombia.geo.json")
mapa_colombia["NOMBRE_DPT"] = mapa_colombia["NOMBRE_DPT"].str.strip().str.title()

# Hacer merge con los datos clasificados
mapa_colombia = mapa_colombia.merge(df_resultado, left_on="NOMBRE_DPT", right_on="Departamento", how="left")

# Ver departamentos sin datos
faltantes = mapa_colombia[mapa_colombia["Clasificación Hidraulica"].isna()]
if not faltantes.empty:
    print("⚠️ Departamentos sin datos:", faltantes["NOMBRE_DPT"].tolist())

# Colores personalizados (azules)
colores_azules = ["#a6cee3", "#1f78b4", "#08306b"]  # claro, medio, oscuro
cmap_personalizado = ListedColormap(colores_azules)

# Ordenar categorías para asignar bien los colores
categorias_ordenadas = ["No óptimo", "Variable", "Óptimo"]
mapa_colombia["Clasificación Hidraulica"] = pd.Categorical(
    mapa_colombia["Clasificación Hidraulica"],
    categories=categorias_ordenadas,
    ordered=True
)

# Crear y guardar el mapa
fig, ax = plt.subplots(1, 1, figsize=(12, 10))
mapa_colombia.plot(
    column="Clasificación Hidraulica",
    ax=ax,
    legend=True,
    legend_kwds={"title": "Clasificación Hidráulica"},
    cmap=cmap_personalizado,
    edgecolor="black",
    missing_kwds={"color": "lightgrey", "label": "Sin datos"}
)
ax.set_title("Clasificación Hidráulica por Departamento")
ax.axis("off")
plt.savefig("mapa_hidraulico.png", bbox_inches="tight", dpi=300)
plt.close()

print("🗺️ Mapa guardado como 'mapa_hidraulico.png'")