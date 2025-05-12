import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

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
