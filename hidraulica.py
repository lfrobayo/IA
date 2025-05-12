import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

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
df_resultado = df[["Departamento", "Clasificación Hidraulica"]]
df_resultado.to_excel("Clasificación_Hidraulica.xlsx", index=False)

print("✅ Archivo 'Clasificación_Hidraulica.xlsx' generado correctamente.")