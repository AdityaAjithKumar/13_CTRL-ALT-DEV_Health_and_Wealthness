import uuid

from flask import Flask, render_template, request, jsonify, url_for, send_from_directory
from flask_cors import CORS
import assemblyai as aai
import os
import google.generativeai as genai
from gtts import gTTS
from pymongo import MongoClient

MONGO_URI = "mongodb+srv://123gamein:123gamein@medai.vzynx.mongodb.net/?retryWrites=true&w=majority&appName=MedAi"
client = MongoClient(MONGO_URI)

# Database and collection
db = client["medai"]
patients_collection = db["patients"]

model = genai.GenerativeModel("gemini-1.5-flash")
chat = model.start_chat(
    history=[
        {"role": "user", "parts": "Hello"},
        {"role": "model", "parts": "Great to meet you. What would you like to know?"},
    ]
)
genai.configure(api_key="AIzaSyD8aiihB_7xMRrLD6tMeGFsmqJz2-xwGnE")
app = Flask(__name__)
CORS(app)  # Enable CORS

app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure the upload directory exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Replace with your AssemblyAI API key
aai.settings.api_key = "aee0ee7da850424197f64b231df65963"


def fetch_patient_details(tag_id):
    """
    Fetch patient details from MongoDB using the tag ID

    :param tag_id: The unique identifier for the patient
    :return: Patient details dictionary or None if not found
    """
    try:
        # Find patient by ID (assuming the ID is stored as an integer)
        patient = patients_collection.find_one({"id": tag_id})

        if patient:
            # Print detailed patient information
            print("\n--- Patient Details ---")
            print(f"ID: {patient.get('id', 'N/A')}")
            print(f"Name: {patient.get('Name', 'N/A')}")
            print(f"Age: {patient.get('Age', 'N/A')}")
            print(f"Blood Type: {patient.get('Blood Type', 'N/A')}")

            # Print Allergies
            print("Allergies:")
            for allergy in patient.get('Allergies', []):
                print(f"  - {allergy}")

            # Print Diseases
            print("Diseases:")
            for disease in patient.get('Any Diseases', []):
                print(f"  - {disease}")

            # Print Emergency Contact
            emergency_contact = patient.get('Emergency Contact', {})
            print("\nEmergency Contact:")
            print(f"  Name: {emergency_contact.get('Name', 'N/A')}")
            print(f"  Phone: {emergency_contact.get('Phone', 'N/A')}")
            print(f"  Referral Doctor: {emergency_contact.get('Referral Doctor', 'N/A')}")

            # Print Medications
            print("\nMedications:")
            for medication in patient.get('Medication', []):
                print(f"  - {medication}")

            return patient
        else:
            print(f"No patient found with ID: {tag_id}")
            return None

    except Exception as e:
        print(f"Error fetching patient details: {e}")
        return None
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/transcribe', methods=['POST'])
def transcribe():
    file = request.files.get('audio', None)

    if not file:
        return jsonify({"error": "Please provide an audio file."}), 400

    transcriber = aai.Transcriber()

    try:
        # Generate a unique filename for the uploaded audio
        upload_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_filename)
        file.save(file_path)

        # Upload the file to AssemblyAI
        with open(file_path, "rb") as audio_file:
            audio_url = transcriber.upload_file(audio_file)

        # Perform transcription
        transcript = transcriber.transcribe(audio_url)

        if transcript.status == aai.TranscriptStatus.error:
            return jsonify({"error": transcript.error}), 500

        # Get AI response
        ai_response = sendai(transcript.text)

        # Generate TTS audio
        tts = gTTS(ai_response)
        tts_filename = f"{uuid.uuid4()}.mp3"
        tts_path = os.path.join(app.config['UPLOAD_FOLDER'], tts_filename)
        tts.save(tts_path)

        # Create a URL for the TTS audio that will work with the send_from_directory route
        tts_url = f"/static/uploads/{tts_filename}"

        return jsonify({
            "transcription": transcript.text,
            "ai_response": ai_response,
            "tts_audio": tts_url
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def test_patient_fetch():
    # Example tag ID - replace with actual NFC tag ID
    tag_id = 1
    fetch_patient_details(tag_id)

def sendai(text):
    response = chat.send_message(text)
    print(response.text)
    return response.text



if __name__ == '__main__':
    test_patient_fetch()

    app.run(debug=True)
