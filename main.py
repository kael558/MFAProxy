import base64
import time

import flask
from flask import Flask, send_file, request
from flask_cors import CORS
from pydub import AudioSegment
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
import os
import subprocess
import openai
from dotenv import load_dotenv
import requests
from textgrid import textgrid_parse, get_comparison

load_dotenv()

openai.api_key = os.environ.get('OPENAI_API_KEY')
app = Flask(__name__)
CORS(app)



@app.route('/whisper', methods=['POST'])
def whisper_api():
    audio = request.json['audio'].replace('data:audio/webm;base64,', '')
    decoded_data = base64.b64decode(audio)

    with open('tmp/audio.webm', 'wb') as f:
        f.write(decoded_data)
    audio_file = open('tmp/audio.webm', "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript



@app.route('/completions', methods=['POST'])
def completion_api():
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=request.json['messages']
    )
    return completion

def tts(text, voice_id, filename):
    CHUNK_SIZE = 1024
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'audio/mpeg',
        'xi-api-key': os.environ.get('ELEVENLABS_API_KEY')
    }

    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.15,
            "similarity_boost": 1
        }
    }

    response = requests.post(url, json=data, headers=headers)
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)

@app.route('/tts', methods=['POST'])
def tts_api():
    tts(request.json['text'], request.json['voice_id'], 'tmp/output.mp3')
    return send_file('tmp/output.mp3', as_attachment=True)


@app.route('/sentence', methods=['POST'])
def sentence_api():
    # sentence_id, sentence, voice_id, audio
    print(request.json['sentence_id'], request.json['sentence'], request.json['voice_id'])
    sentence_id = request.json['sentence_id']

    # Bot stuff
    tts(request.json['sentence'], request.json['voice_id'], f'inputs/file_{sentence_id}_bot.wav')
    with open(f'inputs/file_{sentence_id}_bot.txt', 'w') as f:
        f.write(request.json['sentence'])

    # User stuff
    audio = request.json['audio'].replace('data:audio/webm;base64,', '')
    decoded_data = base64.b64decode(audio)

    with open(f'inputs/file_{sentence_id}_user.webm', 'wb') as f:
        f.write(decoded_data)
        f.close()

    audio_file = open(f'inputs/file_{sentence_id}_user.webm', "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)

    with open(f'inputs/file_{sentence_id}_user.txt', 'w') as f:
        f.write(transcript.text)

    subprocess.call(['ffmpeg', '-i', f'inputs/file_{sentence_id}_user.webm', '-c:a', 'pcm_f32le',
                     f'inputs/file_{sentence_id}_user.wav'])

    return "success"


@app.route('/finish', methods=['POST'])
def finish_api():
    sentence_ids = request.json['sentence_ids']
    print(sentence_ids)

    # Delete all .webm files
    for sentence_id in sentence_ids:
        if os.path.exists(f'inputs/file_{sentence_id}_user.webm'):
            os.remove(f'inputs/file_{sentence_id}_user.webm')
        #os.remove(f'inputs/file_{sentence_id}_bot.webm')

    # Run MFA
    subprocess.call(['run_mfa.bat'], shell=True)
    #subprocess.call(['./run_mfa.sh']) # for linux

    # Wait for the output file to be created
    while not os.path.exists(f'outputs/file_0_user.TextGrid'):
        print('waiting for MFA to finish')
        time.sleep(10)

    print('MFA finished')
    time.sleep(10)

    results = {}
    for sentence_id in sentence_ids:
        j1, j2 = get_comparison(f'outputs/file_{sentence_id}_user.TextGrid', f'outputs/file_{sentence_id}_bot.TextGrid')
        results[sentence_id] = (j1, j2)
    print(results)

    return results

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')



"""
user chooses 10 sentences
 - says sentence, sends to openai (transcribes and saves audio + transcript)
 - finish (sends all audio + transcripts to openai)
 


user says sentence ->
 transcribes sentence
 
 
 




UPLOAD_FOLDER = "/path/to/your/upload/directory"
PROCESSED_FOLDER = "/path/to/your/processed/directory"
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'flac'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class AudioProcessing(Resource):
    def post(self):
        if 'file' not in request.files:
            return {"error": "No file part in the request."}, 400

        file = request.files['file']
        folder_id = request.form.get('folder_id', None)  # Get folder_id from form-data

        if folder_id is None:
            return {"error": "No 'folder_id' provided in request."}, 400

        if file.filename == '':
            return {"error": "No file selected for uploading."}, 400

        if file and allowed_file(file.filename):
            folder_path = os.path.join(BASE_DIRECTORY, folder_id)

            # Check if folder_id is valid (i.e., folder exists)
            if not os.path.exists(folder_path):
                return {"error": "Invalid 'folder_id'. No such folder exists."}, 400

            filename = secure_filename(file.filename)
            filepath = os.path.join(folder_path, filename)  # Save the file to the specified folder
            file.save(filepath)

            # Call your command line here.
            text_filename = filename.rsplit('.', 1)[0] + '.txt'
            text_filepath = os.path.join(folder_path, text_filename)
            command = f'your-command {filepath} > {text_filepath}'
            subprocess.run(command, shell=True)
            import subprocess

            return_code = subprocess.call(["python", "--version"])

            if return_code == 0:

                print("Command executed successfully.")

            else:

                print("Command failed with return code", return_code)

            # If the text file was created successfully, send it back
            if os.path.exists(text_filepath):
                return send_file(text_filepath, as_attachment=True)

        else:
            return {"error": "Allowed file types are wav, mp3, flac."}, 400


BASE_DIRECTORY = "/path/to/your/base/directory"  # Base directory
class CreateDirectory(Resource):
    def post(self):
        folder_id = request.json.get('id', None)

        if folder_id is None:
            return {"error": "No 'id' provided in request."}, 400

        folder_path = os.path.join(BASE_DIRECTORY, folder_id)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            return {"message": f"Folder '{folder_id}' created successfully."}
        else:
            return {"error": f"Folder '{folder_id}' already exists."}, 400

"""
"""
 const res = await fetch(`${base_url}/tts/${voiceId}/stream`, {
            method: 'POST',
            headers: {  
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Credentials': true,
     
            },
            body: JSON.stringify({
                "text": text,
                "voice_settings": {
                    "stability": 0.15,
                    "similarity_boost": 1
                },
                "optimize_streaming_latency": 4
            })
        });

        if (!res.ok) {
            throw new Error('bad status code: ' + res.status);
        }

        const json = await res.json();
        console.log(json);
        return json.choices[0].text;
"""

# api.add_resource(OpenAPILLM, '/openai_llm')
# api.add_resource(OpenAPITranscribe, '/openai_transcribe')
# api.add_resource(ElevenLabs, '/elevenlabs')


