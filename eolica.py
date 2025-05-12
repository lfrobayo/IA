import pandas as pd
import geopandas as gpd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Cargar archivo
archivo = "Datos.xlsx"
df = pd.read_excel(archivo, sheet_name="Eolica")

# Eliminar columna innecesaria
if "Clase IEC" in df.columns:
    df = df.drop(columns=["Clase IEC"])

# Definir columnas clave
columnas = [
    "Departamento",
    "Prom. 1",
    "V viento (m/s)",
    "Densidad (W/m²)",
    "Prom. 2",
    "FC IEC-I",
    "FC IEC-II"
]
df = df[columnas].copy()

# Función para verificar y preguntar sobre valores no numéricos o vacíos
def verificar_y_preguntar(df, columna):
    for index, valor in df[columna].items():
        if pd.isna(valor):
            respuesta = input(f"Vacío en '{columna}', fila {index} ({df.loc[index, 'Departamento']}). ¿Eliminar? (s/n): ").lower()
            if respuesta == 's':
                return df.drop(index)
        else:
            try:
                float(valor)
            except (ValueError, TypeError):
                respuesta = input(f"No numérico ('{valor}') en '{columna}', fila {index} ({df.loc[index, 'Departamento']}). ¿Eliminar? (s/n): ").lower()
                if respuesta == 's':
                    return df.drop(index)
    return df

# Verificar y limpiar columnas numéricas
columnas_numericas = df.columns[1:]
for col in columnas_numericas:
    df = verificar_y_preguntar(df, col)
    if df is None:
        print("No quedan filas.")
        exit()

# Convertir y limpiar
for col in columnas_numericas:
    df[col] = pd.to_numeric(df[col], errors="coerce")
df["Departamento"] = df["Departamento"].str.strip().str.title()
df = df.dropna()

# Normalizar
X = df.drop("Departamento", axis=1)
X_scaled = StandardScaler().fit_transform(X)

# K-means clustering
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df["Cluster"] = kmeans.fit_predict(X_scaled)

# Asignar etiquetas según V viento
media_cluster = df.groupby("Cluster")["V viento (m/s)"].mean()
orden = media_cluster.sort_values(ascending=False).index.tolist()
etiquetas = {orden[0]: "Óptimo", orden[1]: "Variable", orden[2]: "No óptimo"}
df["Clasificación Eolica"] = df["Cluster"].map(etiquetas)

# Guardar resultados
df_resultado = df[["Departamento", "Clasificación Eolica"]].copy()
df_resultado.loc[:, "Departamento"] = df_resultado["Departamento"].str.strip().str.title()
df_resultado.to_excel("Clasificación_Eolica.xlsx", index=False)
print("✅ Archivo 'Clasificación_Eolica.xlsx' generado correctamente.")

# Cargar mapa de Colombia
mapa_colombia = gpd.read_file("Colombia.geo.json")

# Normalizar nombres del GeoDataFrame
mapa_colombia["NOMBRE_DPT"] = mapa_colombia["NOMBRE_DPT"].str.strip().str.title()

# Hacer merge para mapa
mapa_colombia = mapa_colombia.merge(df_resultado, left_on="NOMBRE_DPT", right_on="Departamento", how="left")

# Ver departamentos sin datos
faltantes = mapa_colombia[mapa_colombia["Clasificación Eolica"].isna()]
if not faltantes.empty:
    print("⚠️ Departamentos sin datos:", faltantes["NOMBRE_DPT"].tolist())

# Crear y guardar el mapa como imagen
fig, ax = plt.subplots(1, 1, figsize=(12, 10))
mapa_colombia.plot(
    column="Clasificación Eolica",
    ax=ax,
    legend=True,
    legend_kwds={"title": "Clasificación Eólica"},
    cmap="viridis",
    edgecolor="black",
    missing_kwds={"color": "lightgrey", "label": "Sin datos"}
)
ax.set_title("Clasificación Eólica por Departamento")
ax.axis("off")
plt.savefig("mapa_eolico.png", bbox_inches="tight", dpi=300)
plt.close()

print("🗺️ Mapa guardado como 'mapa_eolico.png'")
