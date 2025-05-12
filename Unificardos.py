import pandas as pd

# Cargar archivos
solar = pd.read_excel("Clasificación_Solar.xlsx")
eolica = pd.read_excel("Clasificación_Eolica.xlsx")
hidraulica = pd.read_excel("Clasificación_Hidraulica.xlsx")
maestra = pd.read_excel("Datos.xlsx")  # Donde está la hoja maestra

# Normalizar nombres de departamentos
for df in [solar, eolica, hidraulica, maestra]:
    df["Departamento"] = df["Departamento"].str.strip().str.title()

# Eliminar columna 'Numero' si existe
if "Numero" in maestra.columns:
    maestra = maestra.drop(columns=["Numero"])

# Renombrar columnas de clasificación para evitar conflictos
solar = solar.rename(columns={"Clasificación Solar": "Solar"})
eolica = eolica.rename(columns={"Clasificación Eolica": "Eolica"})
hidraulica = hidraulica.rename(columns={"Clasificación Hidraulica": "Hidraulica"})

# Unir todo por Departamento
df_unido = maestra.merge(solar, on="Departamento", how="left")\
                  .merge(eolica, on="Departamento", how="left")\
                  .merge(hidraulica, on="Departamento", how="left")

# Función para convertir las clasificaciones a valores numéricos
def convertir_a_numerico(valor):
    if pd.isna(valor):
        return None
    
    valor = str(valor).strip().lower()
    if "no óptimo" in valor or "no optimo" in valor:
        return 1
    elif "variable" in valor:
        return 2
    elif "óptimo" in valor or "optimo" in valor:
        return 3
    else:
        return None  # Para casos no previstos

# Crear columnas con equivalencias numéricas
df_unido["Solar_Num"] = df_unido["Solar"].apply(convertir_a_numerico)
df_unido["Eolica_Num"] = df_unido["Eolica"].apply(convertir_a_numerico)
df_unido["Hidraulica_Num"] = df_unido["Hidraulica"].apply(convertir_a_numerico)

# Obtener todas las columnas originales (antes de agregar las numéricas)
columnas_originales = list(df_unido.columns)[:-3]  # Excluir las 3 columnas numéricas recién agregadas
nuevas_columnas = []

# Reorganizar colocando cada columna numérica junto a su columna original
for col in columnas_originales:
    nuevas_columnas.append(col)
    if col == "Solar":
        nuevas_columnas.append("Solar_Num")
    elif col == "Eolica":
        nuevas_columnas.append("Eolica_Num")
    elif col == "Hidraulica":
        nuevas_columnas.append("Hidraulica_Num")

# Reordenar el DataFrame
df_unido = df_unido[nuevas_columnas]

# Guardar archivo unificado
df_unido.to_excel("Datos_Unificados.xlsx", index=False)
print("✅ Archivo 'Datos_Unificados.xlsx' creado con éxito.")
print("✅ Se agregaron columnas de equivalencia numérica: 1=No óptimo, 2=Variable, 3=Óptimo")