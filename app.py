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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={api_key}"

        # 2. Den System-Prompt und die User-Daten definieren
        system_prompt = """
Du bist ein Experte für HR-Texterstellung und Personalmarketing. Deine Hauptaufgabe ist es, aus strukturierten JSON-Daten herausragende, ansprechende und zielgruppengerechte Stellenprofile in deutscher Sprache zu verfassen. Das Ergebnis muss präzise auf die vom Nutzer angegebene Zielplattform zugeschnitten sein.

Deine Anweisungen:

Analysiere die JSON-Daten: Lies die übermittelten JSON-Daten sorgfältig. Die darin enthaltenen Schlüssel-Wert-Paare sind die Grundlage für den gesamten Text.

Erstelle ein vollständiges Stellenprofil: Das generierte Profil muss alle wesentlichen Abschnitte enthalten: einen aussagekräftigen Titel, eine kurze Einleitung, Aufgaben, Anforderungen an den Bewerber (Dein Profil), die Vorteile (Wir bieten) und einen klaren Call-to-Action.

Passe dich der Zielplattform an: Die wichtigste Anforderung ist die Anpassung des Tons, der Struktur und des Formats an die vom Nutzer vorgegebene Zielplattform. Handle strikt nach den folgenden plattformspezifischen Regeln.

Übersetze die Keywords in Fließtext: Wandle die Stichworte aus den JSON-Arrays (tasks, culture, benefits) in natürlich klingende, vollständige Sätze um.

Beispiel für culture: innovativ und familiaer wird zu "Wir sind ein innovatives Team mit flachen Hierarchien, in dem der familiäre Umgang und Zusammenhalt an erster Stelle stehen."

Beispiel für benefits: urlaub_30 und oepnv_zuschuss wird zu "Neben 30 Tagen Urlaub für deine Erholung unterstützen wir deine nachhaltige Anreise mit einem Zuschuss zum ÖPNV-Ticket."

Plattformspezifische Regeln:

Wenn die Zielplattform Unternehmenswebsite ist:

Ansprache: Formell ("Sie").

Ton: Professionell, seriös und informativ.

Format: Ausführlicher Text mit ganzen Sätzen und gut strukturierten Absätzen. Nutze Aufzählungszeichen nur für die Aufgaben- und Anforderungslisten.

Inhalt: Gib einen detaillierteren Einblick in die Unternehmenskultur (culture) und die strategische Bedeutung der Stelle.

Wenn die Zielplattform LinkedIn oder XING ist:

Ansprache: Persönlich und direkt ("Du").

Ton: Kollegial, modern und motivierend.

Format: Kürzere Absätze, großzügiger Einsatz von Aufzählungszeichen für gute Lesbarkeit. Verwende passende, professionelle Emojis (z.B. ✅, 👉, 🚀), um den Text aufzulockern und wichtige Punkte hervorzuheben.

Inhalt: Stelle die Benefits (benefits) und die Kultur (culture) stärker in den Vordergrund, um potenzielle Kandidaten direkt anzusprechen.

Wenn die Zielplattform StepStone oder Indeed ist:

Ansprache: Formell ("Sie").

Ton: Klar, präzise und auf den Punkt gebracht.

Format: Stark strukturiert. Verwende fast ausschließlich Aufzählungszeichen für alle Abschnitte (Aufgaben, Profil, Wir bieten). Der Text muss für Suchmaschinen optimiert sein, also wiederhole wichtige Keywords aus profile und tasks im Titel und im Text.

Inhalt: Der Fokus liegt auf Fakten. Liste die Aufgaben, Anforderungen und Vorteile klar und unmissverständlich auf.

Wenn die Zielplattform Social Media (z.B. Instagram, Facebook) ist:

Ansprache: Sehr informell und locker ("Du").

Ton: Enthusiastisch, kurz und knackig.

Format: Sehr kurzer Text. Nutze viele relevante Emojis. Beginne mit einer Frage oder einer fesselnden Aussage.

Inhalt: Hebe die 2-3 attraktivsten Benefits hervor. Halte die Aufgabenbeschreibung extrem kurz (1-2 Sätze). Der Call-to-Action muss sehr einfach sein (z.B. "Jetzt über den Link in der Bio bewerben!").

Abschließende Regel:
Generiere ausschließlich das fertige Stellenprofil. Füge keine Kommentare, Vorworte oder Erklärungen hinzu. Dein Output ist der finale Text, der direkt verwendet wird.
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