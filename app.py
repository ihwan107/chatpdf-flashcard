import streamlit as st
import os
import json
# Menggunakan SDK Resmi Google untuk otentikasi mutakhir token AQ
from google import genai
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Flashcard & Chat Mandiri AI", page_icon="🃏", layout="wide")

# Fungsi Inti: Memanggil Gemini AI menggunakan SDK Resmi Google
def call_gemini_api(prompt_text, api_key):
    try:
        # Inisialisasi Client resmi Google dengan API Key Anda
        client = genai.Client(api_key=api_key)
        # Memanggil model standar paling stabil
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt_text,
        )
        return response.text
    except Exception as e:
        return f"Gagal terhubung dengan Gemini AI: {str(e)}"

# Fungsi Pembuat Flashcard Otomatis
def generate_flashcards(text_input, api_key):
    prompt = f"""
    Berdasarkan teks materi berikut, buatkan 3 flashcard belajar yang paling penting dalam bentuk JSON Array murni.
    Format hasil wajib berupa JSON seperti contoh ini:
    [
      {{"pertanyaan": "Apa definisi X?", "jawaban": "Definisi X adalah Y"}},
      {{"pertanyaan": "Kapan Z terjadi?", "jawaban": "Z terjadi pada tahun W"}}
    ]
    Teks Materi: {text_input[:4000]}
    """
    raw_ans = call_gemini_api(prompt, api_key)
    try:
        clean_ans = raw_ans.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_ans)
    except:
        return [
            {"pertanyaan": "Materi berhasil dibaca!", "jawaban": "Silakan ajukan pertanyaan langsung di Ruang Chat."},
            {"pertanyaan": "Bagaimana cara kerja sistem ini?", "jawaban": "Sistem membaca teks yang Anda tempel di panel kiri."}
        ]

# --- PANEL SAMPING (SIDEBAR) ---
with st.sidebar:
    st.title("📂 Input Materi")
    st.subheader("Tempel Teks Anda")
    user_text = st.text_area("Tempel (Paste) teks materi dokumen Anda di sini:", height=250)
    
    if user_text:
        st.success("Teks materi berhasil disimpan di memori!")
        st.write("---")
        st.subheader("🃏 Fitur Belajar Aktif")
        if st.button("✨ Buat Flashcard Otomatis"):
            with st.spinner("AI sedang merangkum..."):
                api_key = os.getenv("GOOGLE_API_KEY")
                st.session_state.flashcards = generate_flashcards(user_text, api_key)
                st.session_state.current_card_index = 0
                st.session_state.show_answer = False

# --- AREA UTAMA ---
st.title("📄 Aplikasi Asisten Belajar & Flashcard Mandiri")
tab1, tab2 = st.tabs(["💬 Ruang Chat", "🃏 Ruang Flashcard"])

with tab1:
    st.subheader("Tanya Jawab Materi")
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if user_question := st.chat_input("Tanyakan sesuatu tentang materi Anda..."):
        with st.chat_message("user"):
            st.write(user_question)
        st.session_state.messages.append({"role": "user", "content": user_question})
        
        if user_text:
            with st.spinner("AI sedang berpikir..."):
                api_key = os.getenv("GOOGLE_API_KEY")
                full_prompt = f"Konteks Materi:\n{user_text[:4000]}\n\nPertanyaan: {user_question}"
                ai_response = call_gemini_api(full_prompt, api_key)
        else:
            ai_response = "Silakan tempel teks materi Anda terlebih dahulu pada kotak di panel sebelah kiri."
            
        with st.chat_message("assistant"):
            st.write(ai_response)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})

with tab2:
    st.subheader("Uji Hafalan Anda dengan Flashcard AI")
    if "flashcards" in st.session_state and st.session_state.flashcards:
        cards = st.session_state.flashcards
        idx = st.session_state.current_card_index
        st.info(f"**KARTU KE-{idx + 1} DARI {len(cards)}**")
        st.markdown(f"### ❓ Pertanyaan:\n*{cards[idx]['pertanyaan']}*")
        st.write("---")
        
        if st.session_state.show_answer:
            st.success(f"### 💡 Jawaban:\n{cards[idx]['jawaban']}")
        else:
            st.write("*(Pikirkan jawaban Anda di dalam hati...)*")
            
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Balik Kartu / Lihat Jawaban"):
                st.session_state.show_answer = not st.session_state.show_answer
                st.rerun()
        with col2:
            if st.button("➡️ Kartu Berikutnya") and idx < len(cards) - 1:
                st.session_state.current_card_index += 1
                st.session_state.show_answer = False
                st.rerun()
        with col3:
            if st.button("⬅️ Kartu Sebelumnya") and idx > 0:
                st.session_state.current_card_index -= 1
                st.session_state.show_answer = False
                st.rerun()
    else:
        st.warning("Belum ada flashcard. Tempel teks materi Anda lalu klik tombol '✨ Buat Flashcard Otomatis' di panel samping!")
