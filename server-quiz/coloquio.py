from flask import Flask, request, Response
from google import genai
from dotenv import load_dotenv
import os
import re
import time

# Cargar la API Key desde el archivo .env
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("No se encontró GEMINI_API_KEY en el archivo .env")

# Configurar Gemini
client = genai.Client(api_key=API_KEY)

# Modelos a probar, en orden. Si el primero falla, pasa al siguiente.
MODELOS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]

app = Flask(__name__)


def generar(instruccion):
    ultimo_error = None
    for modelo in MODELOS:
        for intento in range(2):
            try:
                inicio = time.time()
                resultado = client.models.generate_content(
                    model=modelo,
                    contents=instruccion
                )
                print(f"{modelo} tardó:", round(time.time() - inicio, 2), "segundos")
                return resultado.text
            except Exception as e:
                ultimo_error = e
                print(f"Falló {modelo} (intento {intento + 1}):", e)
                time.sleep(1)
    raise ultimo_error


@app.route("/preguntar", methods=["POST"])
def preguntar():
    datos = request.get_json(silent=True) or {}

    pregunta_actual = datos.get("preguntaActual", "")
    respuesta_actual = datos.get("respuestaActual", "")
    pregunta_usuario = datos.get("preguntaIA", "")

    if not pregunta_actual or not respuesta_actual or not pregunta_usuario:
        return Response(
            "Faltan datos para responder.",
            status=400,
            mimetype="text/plain"
        )

    instruccion = f"""
    Sos un asistente de un juego de preguntas y respuestas.

    Pregunta del juego: {pregunta_actual}
    Respuesta correcta: {respuesta_actual}

    Consulta del jugador: {pregunta_usuario}

    Ayudá al jugador con una pista breve y clara.
    No reveles directamente la respuesta correcta.
    Respondé en español, en UNA sola oración corta de máximo 20 palabras.
    """

    try:
        respuesta = generar(instruccion) or "No pude generar una pista."
        respuesta = re.split(r'(?<=[.!?])\s', respuesta.strip())[0]
        return Response(respuesta, mimetype="text/plain")

    except Exception as error:
        print("Error:", error)
        return Response(
            "Hubo un problema al consultar la IA.",
            status=500,
            mimetype="text/plain"
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)