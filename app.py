import os
import json
import traceback
import requests # NEU: Wir verwenden diese Bibliothek für den API-Aufruf
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# HINWEIS: Wir importieren 'google.generativeai' nicht mehr
# import google.generativeai as genai 

load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://457a7b04-6a7b-4126-8aef-96f516543fb3.dev35.app-preview.com"}})

@app.route('/api/generate-posting', methods=['POST'])
def handle_job_posting_request():
    try:
        form_data = request.json
        if not form_data:
            return jsonify({"error": "No data received"}), 400

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return jsonify({"error": "API key was not found in the .env file."}), 500
        
        # --- NEUE METHODE FÜR DEN API-AUFRUF ---

        # 1. Die URL für die Gemini REST API zusammenbauen
        url = f"url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}""

        # 2. Den System-Prompt und die User-Daten definieren
        system_prompt = """
        Gehe in die Funktion eines erfahrenen Personalberaters. Deine Aufgabe ist es, aus den unten stehenden Rohdaten im JSON-Format eine perfekte und ansprechende Stellenbeschreibung zu erstellen.
        Bitte befolge bei der Ausgabe exakt die folgende Struktur:
        **Übersicht über den Arbeitgeber:**
        Formuliere 4-5 Sätze, die das Unternehmen basierend auf den Kultur-Attributen beschreiben.
        **Tätigkeitsbeschreibung:**
        Erstelle eine passende Oberkategorie für die Tätigkeit (z.B. "E-Commerce Management", "Vertrieb & Marketing"). Liste darunter 4-8 aussagekräftige Stichpunkte auf.
        **Charakterprofil des idealen Kandidaten:**
        Beschreibe die Persönlichkeit des perfekten Kandidaten in einem kurzen Absatz.
        **Anforderungsprofil:**
        Liste 3-6 klare Stichpunkte auf, die die notwendigen Qualifikationen beschreiben.
        **Unsere Benefits:**
        Liste alle im "benefits"-Array angegebenen Vorteile in einer ansprechenden Form auf.
        Halte den gesamten Text in einer professionellen, aber authentischen Sprache.
        """
        formatted_user_data = json.dumps(form_data, indent=4, ensure_ascii=False)
        final_prompt = f"{system_prompt}\n\n--- Rohdaten des Kunden ---\n{formatted_user_data}"

        # 3. Den "Payload" (die Daten) im für die REST API erforderlichen Format erstellen
        payload = {
            "contents": [{
                "parts": [{
                    "text": final_prompt
                }]
            }]
        }

        # 4. Die Anfrage mit der 'requests'-Bibliothek senden
        response = requests.post(url, json=payload)
        response.raise_for_status()  # This will raise an error for bad responses (4xx or 5xx)

        # 5. Die Antwort der API auspacken
        data = response.json()
        result_text = data['candidates'][0]['content']['parts'][0]['text']

        return jsonify({"ergebnis": result_text})

    except requests.exceptions.HTTPError as http_err:
        # Spezieller Fehler für fehlgeschlagene HTTP-Anfragen
        print(f"--- HTTP Error Occurred ---")
        print(f"Status Code: {http_err.response.status_code}")
        print(f"Response: {http_err.response.text}")
        traceback.print_exc()
        print("---------------------------")
        return jsonify({"error": f"An API error occurred: {http_err.response.text}"}), 500
    except Exception as e:
        print("--- AN EXCEPTION OCCURRED ---")
        traceback.print_exc()
        print("-----------------------------")
        return jsonify({"error": "An internal server error occurred."}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)