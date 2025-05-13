import pandas as pd
import geopandas as gpd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# Cargar archivo Excel
archivo = "Datos.xlsx"
df = pd.read_excel(archivo, sheet_name="Solar")

# Variables adicionales normalizadas
variables_cualitativas = [
    "Norm. Indice de polvo",
    "Norm. Disponibilidad",
    "Norm. Adapta",
    "Norm. Conflictos",
]

# Columnas a usar
columnas = [
    "Departamento",
    "Irradiación Promedio (kWh/m²/día)",
    "Horas Solares Pico (HSP)",
    "Temperatura Promedio Anual (°C)",
    "Irradiación en Plano Inclinado (POA) (kWh/m²/año)",
    "Índice de Polvo Acumulado Anual (g/m²/mes)",
    "Irradiación solar prom.† (kWh/m²·día)"
] + variables_cualitativas

# Filtrar y limpiar
df = df[columnas].dropna()
df["Departamento"] = df["Departamento"].str.strip().str.title()

# Normalizar valores numéricos
X = df.drop("Departamento", axis=1)
X_scaled = StandardScaler().fit_transform(X)

# K-means con 3 clusters
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df["Cluster"] = kmeans.fit_predict(X_scaled)

# Mapear etiquetas según irradiación promedio
media_por_cluster = df.groupby("Cluster")["Irradiación Promedio (kWh/m²/día)"].mean()
orden_clusters = media_por_cluster.sort_values(ascending=False).index.tolist()
etiquetas = {orden_clusters[0]: "Óptimo", orden_clusters[1]: "Variable", orden_clusters[2]: "No óptimo"}
df["Clasificación Solar"] = df["Cluster"].map(etiquetas)

# Guardar resultado
df_resultado = df[["Departamento", "Clasificación Solar"]]
df_resultado.to_excel("Clasificación_Solar.xlsx", index=False)
print("✅ Archivo 'Clasificación_Solar.xlsx' generado correctamente.")

# Cargar mapa de Colombia
mapa_colombia = gpd.read_file("Colombia.geo.json")

# Normalizar nombres del GeoDataFrame
mapa_colombia["NOMBRE_DPT"] = mapa_colombia["NOMBRE_DPT"].str.strip().str.title()

# Hacer merge para mapa
mapa_colombia = mapa_colombia.merge(df_resultado, left_on="NOMBRE_DPT", right_on="Departamento", how="left")

# Ver departamentos sin datos
faltantes = mapa_colombia[mapa_colombia["Clasificación Solar"].isna()]
if not faltantes.empty:
    print("⚠️ Departamentos sin datos:", faltantes["NOMBRE_DPT"].tolist())

# Crear y guardar el mapa como imagen con colores de naranja a rojo
colores = ["#FFA07A", "#FF4500", "#8B0000"]  # Naranja claro, naranja oscuro, rojo oscuro
cmap = ListedColormap(colores)

fig, ax = plt.subplots(1, 1, figsize=(12, 10))
mapa_colombia.plot(
    column="Clasificación Solar",
    ax=ax,
    legend=True,
    legend_kwds={"title": "Clasificación Solar"},
    cmap=cmap,
    edgecolor="black",
    missing_kwds={"color": "lightgrey", "label": "Sin datos"}
)
ax.set_title("Clasificación Solar por Departamento")
ax.axis("off")
plt.savefig("mapa_solar.png", bbox_inches="tight", dpi=300)
plt.close()
print("🗺️ Mapa guardado como 'mapa_solar.png'")