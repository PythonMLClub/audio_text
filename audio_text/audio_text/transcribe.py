import os
import json
import pandas as pd
import pyodbc
import requests
import speech_recognition as sr
from pydub import AudioSegment
import time  # Import the time module

# Load the configuration from the JSON file
with open('config.json', 'r') as file:
    config = json.load(file)

server = config['SERVER']
database = config['DATABASE']
username = config['USERNAME']
password = config['PASSWORD']

connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};'

# Function to convert audio file to text
def convert_audio_to_text(audio_file):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(audio_file)
    wav_audio_file = "temp_audio.wav"
    audio.export(wav_audio_file, format="wav")

    with sr.AudioFile(wav_audio_file) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "Google Speech Recognition could not understand audio"
        except sr.RequestError as e:
            return f"Could not request results from Google Speech Recognition service; {e}"

# Function to download audio files and save them
def download_and_save_audio(url, filename):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Define audio_files_directory before using it
            audio_files_directory = 'audio_files/'
            os.makedirs(audio_files_directory, exist_ok=True)
            with open(os.path.join(audio_files_directory, filename), 'wb') as file:
                file.write(response.content)
            return True
        else:
            print(f"Failed to download: {filename} (Status code: {response.status_code})")
            return False
    except Exception as e:
        print(f"Failed to download: {filename} ({e})")
        return False

# Define audio_files_directory before using it
audio_files_directory = 'audio_files/'

# Define function to check and update transcripts
def check_and_update_transcripts():
    while True:
        # Establish connection inside the loop to get fresh data
        connection = pyodbc.connect(connection_string)
        cursor = connection.cursor()

        # Fetch the required columns
        query = "SELECT uniqueid, callrecordfilename FROM zoomcalllogs WHERE transcript IS NULL"
        df = pd.read_sql(query, connection)

        # Check if the DataFrame is empty
        if df.empty:
            print("No records with NULL transcripts found.")
        else:
            print(df)

            # Process each audio file one at a time
            for index, row in df.iterrows():
                uniqueid = row['uniqueid']
                callrecordfilename = row['callrecordfilename']

                if not callrecordfilename:
                    print(f"Unique ID {uniqueid} has an empty callrecordfilename.")
                    continue

                url = f"https://cap2.marketingepicenter.net/calllogs/{callrecordfilename}"
                audio_file_path = os.path.join(audio_files_directory, callrecordfilename)

                if not os.path.exists(audio_file_path):
                    if download_and_save_audio(url, callrecordfilename):
                        print("Processing ID", uniqueid)
                        print(f"Audio file downloaded: {callrecordfilename}")
                    else:
                        print(f"Failed to download audio file: {callrecordfilename}")
                        continue

                transcript_text = convert_audio_to_text(audio_file_path)
                transcript_text = transcript_text.replace("this call is being recorded if you do not wish to be recorded please hang up now", "")
                print(transcript_text)

                update_query = "UPDATE zoomcalllogs SET transcript = ? WHERE uniqueid = ?"
                cursor.execute(update_query, (transcript_text, uniqueid))
                connection.commit()

        # Close the cursor and connection inside the loop
        cursor.close()
        connection.close()

        print("Transcription update completed.")

        # Sleep for 1 second before checking again
        time.sleep(1)

# Call the function to continuously check and update transcripts
check_and_update_transcripts()
