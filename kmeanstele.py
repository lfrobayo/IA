from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
import io
import logging

# Configuración básica de logs
logging.basicConfig(level=logging.INFO)

# TOKEN de tu bot de Telegram
TOKEN = '7608658409:AAEkkYt1vbtLhAwobxt7OhTt0fxI-YnbCzI'

# Datos de clientes
clientes = np.array([
    [1000, 200],
    [1200, 250],
    [1500, 300],
    [1800, 200],
    [2000, 220],
    [6000, 700],
    [6500, 800],
    [7000, 750],
    [7500, 700],
    [8000, 720],
    [11000, 1700],
    [11500, 1800],
    [12000, 1750],
    [12500, 1850],
    [13000, 1900]
])

# Creamos el modelo K-means
kmeans = KMeans(n_clusters=3, random_state=42)
kmeans.fit(clientes)

# Función comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Soy un bot que realiza segmentación de clientes usando K-means.\nUsa el comando /segmentar para ver los resultados.")

# Función comando /segmentar
async def segmentar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultado = "Segmentación de Clientes:\n\n"
    for i, label in enumerate(kmeans.labels_):
        resultado += f"Cliente {i+1}: Cluster {label}\n"

    await update.message.reply_text(resultado)

    # Crear gráfico
    plt.figure(figsize=(8, 6))
    plt.scatter(clientes[:, 0], clientes[:, 1], c=kmeans.labels_, cmap='rainbow', s=100)
    plt.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], color='black', marker='X', s=200)
    plt.xlabel('Ingresos Mensuales ($)')
    plt.ylabel('Gasto Promedio en Tienda ($)')
    plt.title('Segmentación de Clientes usando K-means')
    plt.grid(True)

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    await update.message.reply_photo(photo=InputFile(buf, filename="clusters.png"))


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("segmentar", segmentar))

    app.run_polling()


if __name__ == '__main__':
    main()
