import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# === 1. Cargar datos unificados ===
df = pd.read_excel("Datos_Unificados.xlsx")

# === 2. Columnas para análisis (sin clasificaciones originales) ===
variables_base = [
    "Reg.Hid.", "Escorrentía mm/año", "Prcp C mm/año", "Prcp D mm/año",
    "PIB pc 2022 (COP)", "PIB pc 2022 (US$)", "Población 2025",
    "ICEE 2023 %", "IDC 2024", "Densidad 2025 hab/km²", "IDH",
    "Municipios", "Usuarios gas 2023"
]

# === 3. Asegurar que todos los datos sean numéricos ===
for col in variables_base:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# === 4. Eliminar filas con valores faltantes en esas columnas ===
df_limpio = df.dropna(subset=variables_base)

# Guardamos el nombre del departamento
departamentos = df_limpio["Departamento"].values

# === 5. Escalar ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_limpio[variables_base])

# === 6. Función para clusterizar por energía ===
def clusterizar(X, departamentos, nombre_energia):
    # Aplicar K-means con 3 clusters
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X)
    
    # Calcular el centroide más favorable (mayor media para ese tipo de energía)
    df_temp = df_limpio[["Departamento", f"{nombre_energia}_Num"]].copy()
    df_temp["cluster"] = clusters
    medias = df_temp.groupby("cluster")[f"{nombre_energia}_Num"].mean().sort_values(ascending=False)
    
    # Asignar niveles
    niveles = {int(cluster): nivel for nivel, cluster in enumerate(medias.index, start=1)}
    clasificacion = [niveles[cl] for cl in clusters]
    
    return clasificacion

# === 7. Calcular clasificación por cada tipo de energía ===
df_resultado = pd.DataFrame({"Departamento": departamentos})
df_resultado["Solar_KMeans"] = clusterizar(X_scaled, departamentos, "Solar")
df_resultado["Eolica_KMeans"] = clusterizar(X_scaled, departamentos, "Eolica")
df_resultado["Hidraulica_KMeans"] = clusterizar(X_scaled, departamentos, "Hidraulica")

# === 8. Ordenar alfabéticamente ===
df_resultado = df_resultado.sort_values("Departamento")

# === 9. Guardar resultado ===
df_resultado.to_excel("Clasificación_KMeans_Energia.xlsx", index=False)
print("✅ Clasificación por energía guardada en 'Clasificación_KMeans_Energia.xlsx'")