import streamlit as st
import speech_recognition as sr
import google.generativeai as genai
from pydub import AudioSegment
import tempfile
import os
import json

count=0
j=0
data_list=[]

# Configure Gemini API
gemini_api_key=st.secrets['gemini_api_key']
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

# Streamlit UI
st.title("🩺 Doctor-Patient Audio Analyzer")
uploaded_file = st.file_uploader("Upload an audio file (WAV/MP3/M4A)", type=["wav", "mp3", "m4a"])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_input:
        temp_input.write(uploaded_file.read())
        input_path = temp_input.name

    # Convert audio to 16-bit PCM WAV mono
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_output:
        output_path = temp_output.name
        try:
            sound = AudioSegment.from_file(input_path)
            sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            sound.export(output_path, format="wav")
            st.success("✅ Audio converted to supported format.")
        except Exception as e:
            st.error(f"❌ Failed to process audio: {e}")
            st.stop()

    recognizer = sr.Recognizer()
    with sr.AudioFile(output_path) as source:
        audio = recognizer.record(source)

    try:
        with st.spinner("🎧 Transcribing audio..."):
            text = recognizer.recognize_google(audio)
            st.markdown("### 🗣 Transcribed Text:")
            st.write(text)

        # Gemini analysis button
        if st.button("🧠 Analyze Symptoms with Gemini"):
            prompt = f'''From the following doctor-patient conversation:\n{text}.
                    "Extract and return the response in valid JSON format with the following keys:\n"
                    " - symptoms (as a list of strings)\n"
                    " - symptom_duration (string)\n"
                    " - medication (as a list of strings)\n"
                    " - healing_time (string)\n\n"
                    "If the language is not English, translate it first before extracting.'''
            response = model.generate_content(prompt)
            analysis_result = response.text

            st.markdown("### 🤖 Gemini Analysis:")
            st.write(analysis_result)
            for i in analysis_result:
                if i=="**":
                    count+=1
                    if(count%2==0):

                        data_list.append()

            # Generate JSON
            output_json={
                "Transcript":text,
                "gemini_analysis":analysis_result
            }

            json_output = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w', encoding='utf-8')
            json.dump(output_json, json_output, ensure_ascii=False, indent=4)
            json_output.close()

            with open(json_output.name, "rb") as f:
                st.download_button(
                    label="📄 Download Analysis as json",
                    data=f,
                    file_name="doctor_patient_analysis.json",
                    mime="application/json"
                )
                st.caption("💡 After downloading, open the file and press Ctrl+P to print if needed.")


    except sr.UnknownValueError:
        st.error("⚠️ Could not understand the audio.")
    except sr.RequestError as e:
        st.error(f"⚠️ Speech Recognition error: {e}")

    os.remove(input_path)
    os.remove(output_path)
