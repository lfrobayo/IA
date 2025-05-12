import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import telebot
from telebot import types
import os
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# TOKEN de tu bot de Telegram
TOKEN = '7608658409:AAEkkYt1vbtLhAwobxt7OhTt0fxI-YnbCzI' # Reemplaza con tu token real

# Inicializar el bot
bot = telebot.TeleBot(TOKEN)

# Rutas de archivos
DATOS_UNIFICADOS = "Datos_Unificados.xlsx"
RESULTADOS_KMEANS = "Clasificación_KMeans_Energia.xlsx"

# Variables globales
df_resultado = None
df_unificado = None
# Mapear valores numéricos a texto (centralizado para reusar)
mapa_valores = {1: "No óptimo", 2: "Variable", 3: "Óptimo"}

def realizar_analisis_kmeans():
    """Realiza el análisis K-means para los tres tipos de energía"""
    global df_resultado, df_unificado

    logger.info("Iniciando análisis K-means...")

    try:
        # Cargar datos unificados
        df = pd.read_excel(DATOS_UNIFICADOS)
        df_unificado = df.copy()

        # Columnas para análisis
        variables_base = [
            "Reg.Hid.", "Escorrentía mm/año", "Prcp C mm/año", "Prcp D mm/año",
            "PIB pc 2022 (COP)", "PIB pc 2022 (US$)", "Población 2025",
            "ICEE 2023 %", "IDC 2024", "Densidad 2025 hab/km²", "IDH",
            "Municipios", "Usuarios gas 2023"
        ]

        # Asegurar que todos los datos sean numéricos
        for col in variables_base:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Eliminar filas con valores faltantes
        df_limpio = df.dropna(subset=variables_base)

        # Guardamos el nombre del departamento
        departamentos = df_limpio["Departamento"].values

        # Escalar
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_limpio[variables_base])

        # Función para clusterizar por energía
        def clusterizar(X, departamentos, nombre_energia):
            # Aplicar K-means con 3 clusters
            kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X)

            # Calcular el centroide más favorable (mayor media para ese tipo de energía)
            # Necesitas asegurarte de que la columna numérica de la energía exista en df_limpio
            energia_num_col = f"{nombre_energia}_Num"
            if energia_num_col not in df_limpio.columns:
                 logger.error(f"Columna numérica '{energia_num_col}' no encontrada en los datos unificados.")
                 # Aquí podrías manejar el error, quizás lanzar una excepción o retornar None
                 return None # O manejar de otra forma

            df_temp = df_limpio[["Departamento", energia_num_col]].copy()
            df_temp["cluster"] = clusters
            medias = df_temp.groupby("cluster")[energia_num_col].mean().sort_values(ascending=False)

            # Asignar niveles (1=menor potencial, 3=mayor potencial)
            # El clúster con la media más alta obtiene el nivel 3, el siguiente 2, el último 1
            niveles = {int(cluster): nivel for nivel, cluster in enumerate(medias.index[::-1], start=1)} # Invertir para 1=bajo, 3=alto

            clasificacion = [niveles.get(cl, 'N/A') for cl in clusters] # Usar .get por seguridad

            return clasificacion

        # Calcular clasificación por cada tipo de energía
        df_resultado = pd.DataFrame({"Departamento": departamentos})

        # Asegúrate de que las columnas numéricas de energía existan antes de clusterizar
        energia_types = ["Solar", "Eolica", "Hidraulica"]
        for energia in energia_types:
             col_name = f"{energia}_KMeans"
             clasificacion = clusterizar(X_scaled, departamentos, energia)
             if clasificacion is not None:
                df_resultado[col_name] = clasificacion
             else:
                logger.error(f"No se pudo calcular la clasificación K-means para {energia}.")
                # Decide cómo manejar esto: podrías omitir la columna o rellenarla con N/A

        # Eliminar departamentos que no quedaron en df_limpio por NaNs antes de unir con clasificación
        # Esto asegura que df_resultado y df_limpio (o la versión original filtrada) coincidan
        # Una forma es re-crear df_resultado basado en df_limpio[departamentos]
        df_resultado_temp = pd.DataFrame({"Departamento": df_limpio["Departamento"].values})
        for col in df_resultado.columns:
            if col != "Departamento":
                # Unir por departamento para asegurar que coinciden las filas
                 df_resultado_temp = pd.merge(df_resultado_temp, df_resultado[[Departamento, col]], on="Departamento", how="left")

        df_resultado = df_resultado_temp.copy()

        # Ordenar alfabéticamente
        df_resultado = df_resultado.sort_values("Departamento").reset_index(drop=True) # Reset index after sorting

        # Guardar resultado
        df_resultado.to_excel(RESULTADOS_KMEANS, index=False)
        logger.info(f"✅ Clasificación por energía guardada en '{RESULTADOS_KMEANS}'")

        return df_resultado

    except FileNotFoundError:
        logger.error(f"Error: Archivo '{DATOS_UNIFICADOS}' no encontrado.")
        return None # Indicar fallo
    except Exception as e:
        logger.error(f"Error durante el análisis K-means: {str(e)}")
        return None # Indicar fallo


def cargar_o_analizar():
    """Carga resultados existentes o realiza el análisis si no existen"""
    global df_resultado, df_unificado

    # Intentar cargar datos unificados primero (necesario para obtener_resultados_departamento)
    try:
        df_unificado = pd.read_excel(DATOS_UNIFICADOS)
        logger.info(f"✅ Datos unificados cargados desde '{DATOS_UNIFICADOS}'")
    except FileNotFoundError:
        logger.error(f"Error: Archivo '{DATOS_UNIFICADOS}' no encontrado. No se pueden cargar datos.")
        df_unificado = None # Asegurarse de que es None si falla
        df_resultado = None # Si no hay datos unificados, tampoco habrá resultados
        return None # Indicar fallo

    # Intentar cargar resultados existentes
    try:
        df_resultado = pd.read_excel(RESULTADOS_KMEANS)
        logger.info(f"✅ Datos cargados desde '{RESULTADOS_KMEANS}'")
        # Pequeña validación: asegurarse de que los departamentos en resultado estén en unificados
        # Esto podría ser más robusto, pero es un inicio
        if df_unificado is not None and not set(df_resultado["Departamento"]).issubset(set(df_unificado["Departamento"])):
             logger.warning("Los departamentos en el archivo de resultados no coinciden con los datos unificados. Regenerando análisis.")
             df_resultado = realizar_analisis_kmeans() # Regenerar si hay inconsistencia
             if df_resultado is None: # Si la regeneración falla
                 return None
        elif df_resultado is None: # Si se cargó pero es None (ej. archivo vacío o corrupto)
             logger.warning("El archivo de resultados está vacío o corrupto. Regenerando análisis.")
             df_resultado = realizar_analisis_kmeans()
             if df_resultado is None: # Si la regeneración falla
                 return None


    except FileNotFoundError:
        # Si no existen, realizar análisis
        logger.warning("⚠️ No se encontraron resultados previos. Realizando análisis...")
        df_resultado = realizar_analisis_kmeans()
        if df_resultado is None: # Si el análisis falla
            return None

    # Si llegamos aquí, df_resultado debería estar cargado o calculado
    if df_resultado is not None:
        logger.info("Carga o análisis completado exitosamente.")
    else:
         logger.error("Error fatal: No se pudieron cargar ni generar los datos de resultados.")

    return df_resultado


def obtener_resultados_departamento(departamento):
    """Genera un mensaje con los resultados para un departamento específico"""
    global df_resultado, df_unificado

    # Verificar si tenemos resultados y datos unificados
    if df_resultado is None or df_unificado is None:
        # Intentar cargar/analizar si no están disponibles
        if cargar_o_analizar() is None:
             return "❌ Error: No se pudieron cargar los datos necesarios para el análisis."

    # Buscar departamento en resultados y datos unificados
    try:
        # Asegurarse de que la columna 'Departamento' existe antes de filtrar
        if "Departamento" not in df_resultado.columns or "Departamento" not in df_unificado.columns:
             return "❌ Error interno: Columna 'Departamento' no encontrada."

        fila_resultado = df_resultado[df_resultado["Departamento"].str.lower() == departamento.lower()]
        fila_unificada = df_unificado[df_unificado["Departamento"].str.lower() == departamento.lower()]

        if fila_resultado.empty or fila_unificada.empty:
            return f"No se encontraron resultados para {departamento}."

        # Tomar la primera fila encontrada (asumiendo nombres de departamento únicos)
        fila_resultado = fila_resultado.iloc[0]
        fila_unificada = fila_unificada.iloc[0]

    except Exception as e:
        logger.error(f"Error al buscar departamento {departamento}: {str(e)}")
        return f"❌ Error al buscar resultados para {departamento}."


    # Obtener clasificaciones
    # Usar .get para evitar KeyError si la columna no existe inesperadamente
    solar_original = fila_unificada.get("Solar", "N/A")
    solar_num = fila_unificada.get("Solar_Num", "N/A")
    solar_kmeans = fila_resultado.get("Solar_KMeans", "N/A")

    eolica_original = fila_unificada.get("Eolica", "N/A")
    eolica_num = fila_unificada.get("Eolica_Num", "N/A")
    eolica_kmeans = fila_resultado.get("Eolica_KMeans", "N/A")

    hidraulica_original = fila_unificada.get("Hidraulica", "N/A")
    hidraulica_num = fila_unificada.get("Hidraulica_Num", "N/A")
    hidraulica_kmeans = fila_resultado.get("Hidraulica_KMeans", "N/A")

    # Crear mensaje
    mensaje = f"📊 *Resultados para {departamento.title()}*\n\n" # Usar title() para capitalización consistente

    # Formatear secciones de energía
    def format_energy_section(energia_nombre, original, num, kmeans_num):
        text = f"*{energia_nombre}:*\n"
        text += f"• Clasificación original: {original}\n"
        text += f"• Valor numérico: {num}\n"
        # Usar el mapa_valores centralizado
        kmeans_text = mapa_valores.get(kmeans_num, kmeans_num) # Si kmeans_num no está en el mapa, muestra el número
        text += f"• Clasificación K-means: {kmeans_text}"
        if isinstance(kmeans_num, (int, float)):
             text += f" (Nivel {int(kmeans_num)})" # Mostrar nivel numérico también
        text += "\n"
        return text

    mensaje += format_energy_section("Energía Solar", solar_original, solar_num, solar_kmeans) + "\n"
    mensaje += format_energy_section("Energía Eolica", eolica_original, eolica_num, eolica_kmeans) + "\n"
    mensaje += format_energy_section("Energía Hidraulica", hidraulica_original, hidraulica_num, hidraulica_kmeans)


    return mensaje

#FUNCIÓN PARA LISTAR TOP N ---
def listar_top_departamentos(message, energia, n=5):
    """
    Lista los top N departamentos para una energía específica
    basado en la clasificación K-means (Nivel 3 > 2 > 1).
    """
    global df_resultado

    # Asegurar que los datos estén cargados
    if df_resultado is None:
        if cargar_o_analizar() is None:
            bot.send_message(message.chat.id, "❌ Error: No se pudieron cargar los datos para listar departamentos.")
            return

    # Nombre de la columna de clasificación K-means para la energía
    energia_col = f"{energia}_KMeans"

    # Verificar si la columna existe
    if energia_col not in df_resultado.columns:
        bot.send_message(message.chat.id, f"❌ Error interno: Columna de clasificación '{energia}' no encontrada.")
        return

    # Ordenar por la clasificación K-means (descendente) y luego por nombre de departamento (ascendente)
    df_sorted = df_resultado.sort_values(
        by=[energia_col, "Departamento"],
        ascending=[False, True] # Nivel 3 primero, luego 2, luego 1. Alfabético dentro de cada nivel.
    ).reset_index(drop=True) # Resetear índice para tomar el head correctamente

    # Seleccionar los top N departamentos
    top_n_df = df_sorted.head(n)

    # Construir el mensaje
    mensaje = f"🏆 *Top {len(top_n_df)} Departamentos para Energía {energia}*:\n\n" # Usar len(top_n_df) por si hay menos de N

    if top_n_df.empty:
        mensaje += "No se encontraron departamentos clasificados."
    else:
        # Usar el mapa_valores centralizado
        for index, row in top_n_df.iterrows():
            depto = row["Departamento"]
            nivel_num = row[energia_col]
            # Obtener el texto del nivel usando el mapa_valores
            nivel_texto = mapa_valores.get(nivel_num, nivel_num) # Si no encuentra el número, muestra el número tal cual

            mensaje += f"• {depto}: *{nivel_texto}* (Nivel {int(nivel_num) if pd.notna(nivel_num) else 'N/A'})\n"

    # Enviar el mensaje
    bot.send_message(message.chat.id, mensaje, parse_mode="Markdown")

def explicar_clasificacion_departamento(departamento):
    """
    Explica por qué un departamento recibió su clasificación para cada tipo de energía
    basado en los clusters K-means y las variables relevantes.
    """
    global df_resultado, df_unificado

    # Verificar si tenemos resultados y datos unificados
    if df_resultado is None or df_unificado is None:
        # Intentar cargar/analizar si no están disponibles
        if cargar_o_analizar() is None:
            return "❌ Error: No se pudieron cargar los datos necesarios para la explicación."

    try:
        # Imprimir información de depuración
        logger.info(f"Generando explicación para departamento: {departamento}")
        logger.info(f"Columnas en df_resultado: {df_resultado.columns.tolist()}")
        logger.info(f"Columnas en df_unificado: {df_unificado.columns.tolist()}")
        
        # Buscar departamento en resultados y datos unificados (con verificación)
        fila_resultado = df_resultado[df_resultado["Departamento"].str.lower() == departamento.lower()]
        fila_unificada = df_unificado[df_unificado["Departamento"].str.lower() == departamento.lower()]

        if fila_resultado.empty or fila_unificada.empty:
            return f"No se encontraron resultados para {departamento}."

        # Tomar la primera fila encontrada
        fila_resultado = fila_resultado.iloc[0]
        fila_unificada = fila_unificada.iloc[0]
        
        # Verificar las columnas de clasificación K-means
        columnas_kmeans = ["Solar_KMeans", "Eolica_KMeans", "Hidraulica_KMeans"]
        for col in columnas_kmeans:
            if col not in df_resultado.columns:
                logger.error(f"Columna {col} no encontrada en df_resultado")
                return f"❌ Error: Columna de clasificación {col} no encontrada en los resultados."
        
        # Imprimir los valores de clasificación para depuración
        logger.info(f"Valores de clasificación para {departamento}: "
                    f"Solar={fila_resultado.get('Solar_KMeans', 'N/A')}, "
                    f"Eolica={fila_resultado.get('Eolica_KMeans', 'N/A')}, "
                    f"Hidraulica={fila_resultado.get('Hidraulica_KMeans', 'N/A')}")

        # Variables base utilizadas para el análisis
        variables_base = [
            "Reg.Hid.", "Escorrentía mm/año", "Prcp C mm/año", "Prcp D mm/año",
            "PIB pc 2022 (COP)", "PIB pc 2022 (US$)", "Población 2025",
            "ICEE 2023 %", "IDC 2024", "Densidad 2025 hab/km²", "IDH",
            "Municipios", "Usuarios gas 2023"
        ]

        # Verificar qué variables están realmente disponibles en df_unificado
        variables_disponibles = [var for var in variables_base if var in df_unificado.columns]
        logger.info(f"Variables disponibles: {variables_disponibles}")

        # Variables específicas más relevantes por tipo de energía (usar solo las disponibles)
        vars_solar = [var for var in ["Prcp C mm/año", "Prcp D mm/año", "IDH", "ICEE 2023 %"] 
                      if var in variables_disponibles]
        vars_eolica = [var for var in ["Escorrentía mm/año", "Densidad 2025 hab/km²", "PIB pc 2022 (US$)"] 
                       if var in variables_disponibles]
        vars_hidraulica = [var for var in ["Reg.Hid.", "Escorrentía mm/año", "Prcp C mm/año", "Prcp D mm/año"] 
                           if var in variables_disponibles]
        
        # Obtener clasificaciones (con manejo seguro de tipos)
        try:
            solar_kmeans = int(fila_resultado.get("Solar_KMeans")) if pd.notna(fila_resultado.get("Solar_KMeans")) else None
        except (ValueError, TypeError):
            solar_kmeans = None
            
        try:
            eolica_kmeans = int(fila_resultado.get("Eolica_KMeans")) if pd.notna(fila_resultado.get("Eolica_KMeans")) else None
        except (ValueError, TypeError):
            eolica_kmeans = None
            
        try:
            hidraulica_kmeans = int(fila_resultado.get("Hidraulica_KMeans")) if pd.notna(fila_resultado.get("Hidraulica_KMeans")) else None
        except (ValueError, TypeError):
            hidraulica_kmeans = None
        
        # Preparar mensaje de explicación
        mensaje = f"🔍 *Explicación de Clasificación para {departamento.title()}*\n\n"
        
        # Función para formatear una explicación por tipo de energía
        def format_energy_explanation(energia_nombre, kmeans_nivel, variables_clave):
            nivel_texto = mapa_valores.get(kmeans_nivel, f"Nivel {kmeans_nivel}") if kmeans_nivel is not None else "No clasificado"
            texto = f"*{energia_nombre} - {nivel_texto}*:\n"
            
            # Explicar la clasificación según el nivel
            if kmeans_nivel is not None:
                if kmeans_nivel == 3:  # Óptimo
                    texto += "Este departamento presenta condiciones óptimas debido a:\n"
                elif kmeans_nivel == 2:  # Variable
                    texto += "Este departamento presenta condiciones variables debido a:\n"
                else:  # No óptimo
                    texto += "Este departamento presenta condiciones menos favorables debido a:\n"
                
                # Mostrar valores de variables clave para este departamento
                for var in variables_clave:
                    if var in fila_unificada and pd.notna(fila_unificada[var]):
                        valor = fila_unificada[var]
                        # Formatear el valor según su tipo
                        if isinstance(valor, (int, float)):
                            if abs(valor) >= 1000:
                                valor_fmt = f"{valor:,.0f}".replace(",", ".")  # Formato con separadores de miles
                            elif abs(valor) >= 1:
                                valor_fmt = f"{valor:.2f}"
                            else:
                                valor_fmt = f"{valor:.4f}"
                        else:
                            valor_fmt = str(valor)
                        texto += f"• {var}: {valor_fmt}\n"
                    else:
                        texto += f"• {var}: Dato no disponible\n"
                
                # Añadir una comparación con promedios nacionales
                texto += "\n*Comparación con promedios nacionales:*\n"
                for var in variables_clave:
                    if var in df_unificado.columns:
                        try:
                            # Convertir a numérico antes de calcular la media
                            valores_numericos = pd.to_numeric(df_unificado[var], errors='coerce')
                            promedio = valores_numericos.mean()
                            
                            if pd.notna(promedio) and promedio != 0:  # Evitar división por cero
                                valor_dep = pd.to_numeric(fila_unificada.get(var), errors='coerce')
                                
                                if pd.notna(valor_dep):
                                    porcentaje = ((valor_dep / promedio) - 1) * 100
                                    if porcentaje > 0:
                                        texto += f"• {var}: {porcentaje:.1f}% por encima del promedio\n"
                                    else:
                                        texto += f"• {var}: {abs(porcentaje):.1f}% por debajo del promedio\n"
                                else:
                                    texto += f"• {var}: No se puede calcular (valor no disponible)\n"
                            else:
                                texto += f"• {var}: No se puede calcular (promedio no disponible o cero)\n"
                        except Exception as e:
                            texto += f"• {var}: Error al calcular comparación: {str(e)}\n"
            else:
                # Si no hay nivel de clasificación, mostrar los datos disponibles de todas formas
                texto += "No se encontró clasificación para esta energía. Sin embargo, estos son los datos disponibles:\n\n"
                
                for var in variables_clave:
                    if var in fila_unificada and pd.notna(fila_unificada[var]):
                        valor = fila_unificada[var]
                        if isinstance(valor, (int, float)):
                            if abs(valor) >= 1000:
                                valor_fmt = f"{valor:,.0f}".replace(",", ".")
                            else:
                                valor_fmt = f"{valor:.2f}"
                        else:
                            valor_fmt = str(valor)
                        texto += f"• {var}: {valor_fmt}\n"
                
            return texto
        
        # Generar explicaciones para cada tipo de energía
        mensaje += format_energy_explanation("Energía Solar", solar_kmeans, vars_solar) + "\n"
        mensaje += format_energy_explanation("Energía Eólica", eolica_kmeans, vars_eolica) + "\n"
        mensaje += format_energy_explanation("Energía Hidráulica", hidraulica_kmeans, vars_hidraulica)
        
        # Añadir una nota sobre la metodología
        mensaje += "\n📊 *Nota metodológica:*\n"
        mensaje += "La clasificación se basa en un análisis de K-means que agrupa departamentos con características similares. "
        mensaje += "El nivel 3 (Óptimo) indica las mejores condiciones para aprovechamiento energético, "
        mensaje += "mientras que el nivel 1 (No óptimo) indica condiciones menos favorables."
        
        return mensaje
        
    except Exception as e:
        logger.error(f"Error al generar explicación para {departamento}: {str(e)}", exc_info=True)
        return f"❌ Error al generar explicación para {departamento}: {str(e)}"


# --- MANEJADORES DE COMANDOS TOP N ---

@bot.message_handler(commands=['solar'])
def handle_command_solar(message):
    """Maneja el comando /solar para listar los top 5 departamentos para energía solar."""
    logger.info(f"Comando /solar recibido de chat ID {message.chat.id}")
    listar_top_departamentos(message, "Solar", 5)

@bot.message_handler(commands=['eolica'])
def handle_command_eolica(message):
    """Maneja el comando /eolica para listar los top 5 departamentos para energía Eolica."""
    logger.info(f"Comando /eolica recibido de chat ID {message.chat.id}")
    listar_top_departamentos(message, "Eolica", 5)

@bot.message_handler(commands=['hidraulica'])
def handle_command_hidraulica(message):
    """Maneja el comando /hidraulica para listar los top 5 departamentos para energía Hidraulica."""
    logger.info(f"Comando /hidraulica recibido de chat ID {message.chat.id}")
    listar_top_departamentos(message, "Hidraulica", 5)

# --- MANEJADORES EXISTENTES ---

# Añadir un nuevo manejador de comando para la explicación
@bot.message_handler(commands=['explicar'])
def handle_command_explicar(message):
    """
    Muestra un teclado para seleccionar un departamento y ver la explicación detallada
    de su clasificación energética.
    """
    logger.info(f"Comando /explicar recibido de chat ID {message.chat.id}")
    
    # Asegurarse de que tenemos datos cargados
    if df_resultado is None:
        if cargar_o_analizar() is None:
            bot.send_message(message.chat.id, "❌ Error: No se pudieron cargar los datos para mostrar departamentos.")
            return
    
    # Crear teclado inline con departamentos
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    # Ordenar departamentos alfabéticamente
    departamentos = sorted(df_resultado["Departamento"].unique())
    
    # Crear botones para cada departamento
    botones = []
    for dep in departamentos:
        callback_data = f"exp_{dep}"
        if len(callback_data.encode('utf-8')) > 64:
            botones.append(types.InlineKeyboardButton(dep, callback_data=f"exp_{dep[:50]}"))
        else:
            botones.append(types.InlineKeyboardButton(dep, callback_data=callback_data))
    
    # Añadir botones al markup en filas de 2
    for i in range(0, len(botones), 2):
        row_buttons = botones[i:i+2]
        markup.row(*row_buttons)
    
    bot.send_message(message.chat.id,
                     "Selecciona un departamento para ver la explicación detallada de su clasificación energética:",
                     reply_markup=markup)

# Manejador para el callback de explicación
@bot.callback_query_handler(func=lambda call: call.data.startswith('exp_'))
def handle_explicacion_seleccionada(call):
    """Maneja la selección de un departamento para explicación desde el teclado inline"""
    logger.info(f"Callback query de explicación recibido: {call.data} de chat ID {call.message.chat.id}")
    
    # Extraer nombre del departamento del callback
    departamento_callback = call.data[4:]  # Eliminar 'exp_' del inicio
    
    # Buscar el nombre completo del departamento si se truncó el callback
    departamento_completo = departamento_callback
    if df_resultado is not None:
        match = df_resultado[df_resultado["Departamento"].str.startswith(departamento_callback)]
        if not match.empty:
            departamento_completo = match.iloc[0]["Departamento"]
        else:
            logger.warning(f"No se encontró coincidencia completa para callback: {departamento_callback}")
    
    # Obtener la explicación
    bot.send_chat_action(call.message.chat.id, 'typing')  # Mostrar "escribiendo..."
    explicacion = explicar_clasificacion_departamento(departamento_completo)
    
    # Enviar respuesta
    bot.send_message(call.message.chat.id, explicacion, parse_mode="Markdown")
    
    # Responder al callback para quitar el "cargando..."
    bot.answer_callback_query(call.id)

# Actualizar el mensaje de ayuda en handle_start para incluir el nuevo comando
@bot.message_handler(commands=['start'])
def handle_start(message):
    """Maneja el comando /start"""
    logger.info(f"Comando /start recibido de chat ID {message.chat.id}")
    bot.reply_to(message,
                 "🌞 *Bienvenido al Bot de Análisis Energético* 🌊\n\n"
                 "Este bot te permite consultar el potencial energético (solar, eólico e hidráulico) "
                 "de los departamentos de Colombia.\n\n"
                 "Puedes usar:\n"
                 "• /departamentos - Ver la lista de departamentos\n"
                 "• /solar - Ver los top 5 departamentos para energía solar\n"
                 "• /eolica - Ver los top 5 departamentos para energía eólica\n"
                 "• /hidraulica - Ver los top 5 departamentos para energía hidráulica\n"
                 "• /explicar - Ver explicación detallada de la clasificación\n"
                 "• /actualizar - Re-ejecutar el análisis de datos\n"
                 "• Escribir el nombre de un departamento para ver sus resultados.",
                 parse_mode="Markdown")

# Actualizar también el mensaje en handle_mensaje
@bot.message_handler(func=lambda message: True)
def handle_mensaje(message):
    """Maneja cualquier otro mensaje"""
    texto = message.text.strip()
    logger.info(f"Mensaje de texto recibido: '{texto}' de chat ID {message.chat.id}")

    # Intentar cargar datos si no están listos
    if df_resultado is None:
        if cargar_o_analizar() is None:
             bot.send_message(message.chat.id, "❌ Error: No se pudieron cargar los datos para buscar departamentos.")
             return

    # Buscar el departamento por nombre (insensible a mayúsculas/minúsculas)
    if "Departamento" not in df_resultado.columns:
         bot.reply_to(message, "❌ Error interno: Columna 'Departamento' no encontrada en los datos.")
         return

    departamentos_lower = df_resultado["Departamento"].str.lower().tolist()

    if texto.lower() in departamentos_lower:
        # Encontrar el nombre del departamento con la capitalización correcta
        departamento_encontrado = df_resultado[df_resultado["Departamento"].str.lower() == texto.lower()].iloc[0]["Departamento"]
        resultado_mensaje = obtener_resultados_departamento(departamento_encontrado)
        bot.send_message(message.chat.id, resultado_mensaje, parse_mode="Markdown")
        return

    # Si no es un departamento, mostrar mensaje de ayuda
    bot.reply_to(message,
                 "No entiendo ese mensaje. Por favor, usa uno de los comandos o escribe el nombre completo de un departamento.\n\n"
                 "Puedes usar:\n"
                 "• /departamentos - Ver la lista de departamentos\n"
                 "• /solar - Ver los top 5 para solar\n"
                 "• /eolica - Ver los top 5 para eólica\n"
                 "• /hidraulica - Ver los top 5 para hidráulica\n"
                 "• /explicar - Ver explicación detallada de la clasificación\n"
                 "• /actualizar - Re-ejecutar el análisis",
                 parse_mode="Markdown")
    # Crear teclado inline con departamentos
    markup = types.InlineKeyboardMarkup(row_width=2)

    # Ordenar departamentos alfabéticamente
    departamentos = sorted(df_resultado["Departamento"].unique())

    # Crear botones para cada departamento
    botones = []
    for dep in departamentos:
        # El callback_data debe ser único y no muy largo
        # Limitación de 64 bytes en callback_data. dep_NombreDepartamento puede ser largo.
        # Podrías usar un ID o abreviatura si los nombres son muy largos
        # Para nombres de departamentos colombianos, dep_NombreDepartamento debería estar bien.
        callback_data = f"dep_{dep}"
        if len(callback_data.encode('utf-8')) > 64:
             logger.warning(f"Callback data demasiado larga para {dep}: {len(callback_data.encode('utf-8'))} bytes")
             # Considerar una estrategia alternativa, ej: dep_ID
             botones.append(types.InlineKeyboardButton(dep, callback_data=f"dep_{dep[:50]}")) # Truncate as a fallback
        else:
             botones.append(types.InlineKeyboardButton(dep, callback_data=callback_data))


    # Añadir botones al markup en filas de 2
    # Implementación de filas mejorada
    for i in range(0, len(botones), 2):
        row_buttons = botones[i:i+2]
        markup.row(*row_buttons) # Usa * para desempaquetar la lista como argumentos separados


    bot.send_message(message.chat.id,
                     "Selecciona un departamento para ver su análisis energético:",
                     reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('dep_'))
def handle_departamento_seleccionado(call):
    """Maneja la selección de un departamento desde el teclado inline"""
    logger.info(f"Callback query recibido: {call.data} de chat ID {call.message.chat.id}")
    # Extraer nombre del departamento del callback
    departamento_callback = call.data[4:]  # Eliminar 'dep_' del inicio

    # Buscar el nombre completo del departamento si se truncó el callback
    departamento_completo = departamento_callback # Asumir que es el nombre completo inicialmente
    if df_resultado is not None:
         # Buscar en los departamentos cargados si hay una coincidencia que empiece con el callback data
         # Esto ayuda si truncaste el callback_data
         match = df_resultado[df_resultado["Departamento"].str.startswith(departamento_callback)]
         if not match.empty:
              departamento_completo = match.iloc[0]["Departamento"] # Usar el nombre completo del DataFrame
         else:
             logger.warning(f"No se encontró coincidencia completa para callback: {departamento_callback}")


    # Obtener los resultados
    resultado = obtener_resultados_departamento(departamento_completo)

    # Enviar respuesta
    bot.send_message(call.message.chat.id, resultado, parse_mode="Markdown")

    # Responder al callback para quitar el "cargando..."
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['actualizar'])
def handle_actualizar(message):
    """Actualiza el análisis K-means"""
    logger.info(f"Comando /actualizar recibido de chat ID {message.chat.id}")
    bot.send_message(message.chat.id, "⏳ Actualizando análisis K-means...")

    try:
        result = realizar_analisis_kmeans()
        if result is not None:
             bot.send_message(message.chat.id, "✅ Análisis actualizado correctamente.")
        else:
             bot.send_message(message.chat.id, "❌ El análisis no se pudo completar. Revisa los logs.")
    except Exception as e:
        logger.error(f"Error al actualizar análisis: {str(e)}", exc_info=True) # Logea la excepción completa
        bot.send_message(message.chat.id, f"❌ Error inesperado al actualizar: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_mensaje(message):
    """Maneja cualquier otro mensaje"""
    texto = message.text.strip()
    logger.info(f"Mensaje de texto recibido: '{texto}' de chat ID {message.chat.id}")

    # Intentar cargar datos si no están listos
    if df_resultado is None:
        if cargar_o_analizar() is None:
             bot.send_message(message.chat.id, "❌ Error: No se pudieron cargar los datos para buscar departamentos.")
             return

    # Buscar el departamento por nombre (insensible a mayúsculas/minúsculas)
    # Asegurarse de que la columna 'Departamento' existe
    if "Departamento" not in df_resultado.columns:
         bot.reply_to(message, "❌ Error interno: Columna 'Departamento' no encontrada en los datos.")
         return

    departamentos_lower = df_resultado["Departamento"].str.lower().tolist()

    if texto.lower() in departamentos_lower:
        # Encontrar el nombre del departamento con la capitalización correcta del DataFrame
        departamento_encontrado = df_resultado[df_resultado["Departamento"].str.lower() == texto.lower()].iloc[0]["Departamento"]
        resultado_mensaje = obtener_resultados_departamento(departamento_encontrado)
        bot.send_message(message.chat.id, resultado_mensaje, parse_mode="Markdown")
        return

    # Si no es un departamento, mostrar mensaje de ayuda o las opciones
    bot.reply_to(message,
                 "No entiendo ese mensaje. Por favor, usa uno de los comandos o escribe el nombre completo de un departamento.\n\n"
                 "Puedes usar:\n"
                 "• /departamentos - Ver la lista de departamentos\n"
                 "• /solar - Ver los top 5 para solar\n"
                 "• /eolica - Ver los top 5 para Eolica\n"
                 "• /hidraulica - Ver los top 5 para Hidraulica\n"
                 "• /actualizar - Re-ejecutar el análisis",
                 parse_mode="Markdown")


if __name__ == "__main__":
    logger.info("Iniciando bot de Telegram para análisis energético...")

    # Cargar datos al inicio
    if cargar_o_analizar() is None:
         logger.error("El bot no pudo iniciar debido a errores al cargar/analizar los datos.")
    else:
        # Iniciar el bot
        logger.info("Bot listo. Iniciando polling...")
        # Usa infinity_polling que es más robusto frente a errores de conexión
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logger.error(f"Error en el polling del bot: {str(e)}", exc_info=True)