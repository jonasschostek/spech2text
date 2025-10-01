import streamlit as st
import sqlite3
from datetime import datetime
import json
from typing import Dict, Any

# ==============================================================================
# 1. HELFERFUNKTIONEN
# ==============================================================================

def generate_pdf_simple(interview_data):
    """Generiert ein einfaches HTML-Dokument, das als PDF gedruckt werden kann."""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Interview #{interview_data.get('id', 'N/A')}</title>
        <style>
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
            }}
            body {{
                font-family: Arial, sans-serif; max-width: 800px;
                margin: 0 auto; padding: 20px; line-height: 1.6;
            }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            .metadata {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .metadata p {{ margin: 5px 0; }}
            .transcription {{
                background: #ffffff; border: 1px solid #ddd;
                padding: 20px; border-radius: 5px;
                white-space: pre-wrap; word-wrap: break-word; margin: 20px 0;
            }}
            .notes {{
                background: #fff9e6; border-left: 4px solid #ffc107;
                padding: 15px; margin: 20px 0;
            }}
            .footer {{
                margin-top: 50px; padding-top: 20px;
                border-top: 1px solid #ddd; text-align: center;
                color: #666; font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <h1>Interview-Transkription #{interview_data.get('id', 'N/A')}</h1>
        <div class="metadata">
            <h2>Interview-Details</h2>
            <p><strong>Datum:</strong> {interview_data.get('date', 'N/A')}</p>
            <p><strong>Interviewer:</strong> {interview_data.get('interviewer', 'N/A')}</p>
            <p><strong>Interviewte Person:</strong> {interview_data.get('interviewee_info', 'N/A')}</p>
            <p><strong>Erstellt am:</strong> {interview_data.get('created_at', 'N/A')}</p>
        </div>
        <h2>Transkription</h2>
        <div class="transcription">
            {interview_data.get('transcription', 'Keine Transkription vorhanden')}
        </div>
        {f'''<h2>Notizen</h2><div class="notes">{interview_data.get('notes')}</div>''' if interview_data.get('notes') else ''}
        <div class="footer">
            <p>Wildvogelpflegestation - Besucherbefragung</p>
            <p>OST - Ostschweizer Fachhochschule</p>
            <p>Generiert am: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
        </div>
        <div class="no-print" style="margin-top: 30px; text-align: center;">
            <button onclick="window.print()" style="padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 5px; cursor: pointer;">
                🖨️ Drucken / Als PDF speichern
            </button>
        </div>
    </body>
    </html>
    """
    return html_content

def create_speech_interface(initial_text=""):
    """Erstellt die HTML/JS-Schnittstelle mit finalen Bugfixes."""
    escaped_text = json.dumps(initial_text)
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.jsdelivr.net/gh/streamlit/streamlit/frontend/src/lib/streamlit.js"></script>
        <style>
            body {{ margin: 0; font-family: sans-serif; }}
            .controls button {{
                background: #f0f2f6; color: #333; padding: 12px 20px;
                border: 1px solid #ccc; border-radius: 8px; font-size: 16px;
                cursor: pointer; margin: 5px; transition: background-color 0.2s;
            }}
            .controls button:hover {{ background-color: #e6e8eb; }}
            .controls button:disabled {{ cursor: not-allowed; opacity: 0.6; }}
            #startBtn {{ border-color: #4CAF50; }}
            #stopBtn {{ border-color: #f44336; }}
            #status {{ font-weight: bold; }}
            .transcript-display {{
                border: 1px solid #ddd; border-radius: 8px; padding: 10px;
                min-height: 80px; background: #fff; 
                white-space: pre-wrap; word-wrap: break-word;
            }}
        </style>
    </head>
    <body>
        <div style="padding: 10px; border-radius: 10px;">
            <div style="text-align: center; margin-bottom: 15px;">
                <span id="status">🎤 Bereit</span>
            </div>
            <div class="controls" style="text-align: center; margin-bottom: 20px;">
                <button onclick="start()" id="startBtn">▶️ Start</button>
                <button onclick="stop()" id="stopBtn" disabled>⏹️ Stop</button>
            </div>
            <label style="font-weight: bold; display: block; margin-bottom: 5px;">🗣️ Live-Transkription:</label>
            <div id="final" class="transcript-display"></div>
            <div id="interim" style="color: #666; font-style: italic; margin-top: 5px;"></div>
        </div>

        <script>
            Streamlit.setComponentReady();
            let rec = null;
            let active = false;
            let baseTranscript = {escaped_text};
            document.getElementById('final').textContent = baseTranscript;

            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
                const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
                rec = new SR();
                rec.continuous = true;
                rec.interimResults = true;
                rec.lang = 'de-CH';

                rec.onstart = () => {{
                    active = true;
                    document.getElementById('status').innerHTML = '🔴 Aufnahme...';
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                }};

                rec.onresult = (event) => {{
                    let interim_transcript = '';
                    let final_transcript = baseTranscript;

                    // VERBESSERTE LOGIK: Baue das Transkript bei jedem Durchlauf komplett neu auf.
                    // Das verhindert zuverlässig die Duplikation auf Android.
                    for (let i = 0; i < event.results.length; ++i) {{
                        let segment = event.results[i][0].transcript;
                        if (event.results[i].isFinal) {{
                            final_transcript += segment.trim() + ' ';
                        }} else {{
                            interim_transcript += segment;
                        }}
                    }}
                    
                    document.getElementById('final').textContent = final_transcript;
                    document.getElementById('interim').textContent = interim_transcript;
                    Streamlit.setComponentValue({{ text: final_transcript }});
                }};

                rec.onerror = (e) => {{
                    console.error("Speech Recognition Error:", e.error);
                    if (e.error === 'not-allowed') {{
                        alert('Bitte den Mikrofon-Zugriff im Browser erlauben!');
                        document.getElementById('status').innerHTML = '❌ Kein Mikrofon-Zugriff';
                    }}
                }};
                
                rec.onend = () => {{
                    baseTranscript = document.getElementById('final').textContent; // Update base text
                    if (active) {{
                        rec.start();
                    }} else {{
                        document.getElementById('status').innerHTML = '✅ Gestoppt';
                        document.getElementById('startBtn').disabled = false;
                        document.getElementById('stopBtn').disabled = true;
                    }}
                }};
            }} else {{
                document.getElementById('status').innerHTML = '❌ Browser nicht unterstützt';
                document.getElementById('startBtn').disabled = true;
            }}
            
            function start() {{ if (rec) rec.start(); }}
            function stop() {{ if (rec) {{ active = false; rec.stop(); }} }}
        </script>
    </body>
    </html>
    """

# ==============================================================================
# 2. DATENBANK-FUNKTIONEN
# ==============================================================================

def init_database():
    try:
        conn = sqlite3.connect('interviews.db')
        cursor = conn.cursor()
        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='interviews'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                CREATE TABLE interviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, interview_date TEXT NOT NULL,
                    interviewer TEXT, interviewee_info TEXT, transcription TEXT,
                    notes TEXT, metadata TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"DB Fehler: {e}")
        return False

def save_interview(interview_data: Dict[str, Any]) -> int:
    conn = sqlite3.connect('interviews.db')
    cursor = conn.cursor()
    date_str = interview_data.get('date').isoformat()
    cursor.execute('''
        INSERT INTO interviews (interview_date, interviewer, interviewee_info, transcription, notes, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        date_str, interview_data.get('interviewer', ''), interview_data.get('interviewee_info', ''),
        interview_data.get('transcription', ''), interview_data.get('notes', ''),
        json.dumps(interview_data.get('metadata', {}))
    ))
    interview_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return interview_id

def update_interview_field(interview_id: int, field: str, value: str):
    conn = sqlite3.connect('interviews.db')
    cursor = conn.cursor()
    cursor.execute(f'UPDATE interviews SET {field} = ? WHERE id = ?', (value, interview_id))
    conn.commit()
    conn.close()

def get_interview_by_id(interview_id: int):
    conn = sqlite3.connect('interviews.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM interviews WHERE id = ?', (interview_id,))
    result = cursor.fetchone()
    conn.close()
    return dict(result) if result else None

# ==============================================================================
# 3. APP-KONFIGURATION
# ==============================================================================

st.set_page_config(page_title="Interview Transkription", page_icon="🎤", layout="wide")

st.markdown("""
<style>
    .stApp { max-width: 100%; padding: 0.5rem; }
    .stButton > button { width: 100%; min-height: 60px; font-size: 18px; font-weight: bold; border-radius: 10px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

if 'current_interview_id' not in st.session_state:
    st.session_state.current_interview_id = None
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""

if not init_database():
    st.stop()

# ==============================================================================
# 4. HAUPT-INTERFACE
# ==============================================================================

st.title("🎤 Interview Transkription")
st.caption("Wildvogelpflegestation - Besucherbefragung")

tab1, tab2, tab3 = st.tabs(["📝 **Neues Interview**", "📊 **Übersicht**", "ℹ️ **Hilfe**"])

with tab1:
    with st.expander("👤 Interview-Details", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            interviewer = st.text_input("Interviewer*in:", key="interviewer")
        with col2:
            interview_date = st.date_input("Datum:", value=datetime.now())
        interviewee_info = st.text_area("Interviewte Person:", placeholder="Alter, Geschlecht, Eindrücke...", height=60)
    
    consent = st.checkbox("✅ Einverständnis zur Aufnahme und Transkription wurde eingeholt")
    
    action_cols = st.columns(3)
    
    with action_cols[0]:
        if st.button("📋 Neues Interview starten", disabled=not (consent and interviewer), use_container_width=True, type="primary"):
            interview_data = {
                'date': interview_date, 'interviewer': interviewer, 'interviewee_info': interviewee_info,
                'transcription': '', 'notes': '', 'metadata': {}
            }
            interview_id = save_interview(interview_data)
            if interview_id:
                st.session_state.current_interview_id = interview_id
                st.session_state.transcript_text = ""
                st.success(f"✅ Interview #{interview_id} erstellt.")
                st.rerun()
    
    if st.session_state.current_interview_id:
        with action_cols[1]:
            if st.button("💾 Zwischenspeichern", use_container_width=True):
                update_interview_field(st.session_state.current_interview_id, "transcription", st.session_state.transcript_text)
                st.success("✅ Transkript in Datenbank gespeichert!")
        
        with action_cols[2]:
            if st.button("✅ Abschließen & Exportieren", use_container_width=True, type="secondary"):
                update_interview_field(st.session_state.current_interview_id, "transcription", st.session_state.transcript_text)
                interview_data = get_interview_by_id(st.session_state.current_interview_id)
                if interview_data:
                    html_content = generate_pdf_simple(interview_data)
                    st.download_button(
                        label="📥 HTML/PDF herunterladen", data=html_content,
                        file_name=f"interview_{st.session_state.current_interview_id}.html",
                        mime="text/html", use_container_width=True
                    )
                st.success(f"✅ Interview #{st.session_state.current_interview_id} abgeschlossen!")
                st.session_state.current_interview_id = None
                st.session_state.transcript_text = ""
                st.rerun()

    if st.session_state.current_interview_id:
        st.info(f"📍 Aktives Interview: #{st.session_state.current_interview_id}")
        st.markdown("---")
        st.markdown("### 🎙️ Sprachaufnahme & Bearbeitung")

        component_value = st.components.v1.html(
            create_speech_interface(st.session_state.transcript_text),
            key="speech_to_text"
        )

        if component_value and component_value.get("text") != st.session_state.transcript_text:
            st.session_state.transcript_text = component_value.get("text")
            st.rerun()

        edited_transcript = st.text_area(
            "Transkription (wird live aktualisiert und kann hier korrigiert werden):",
            value=st.session_state.transcript_text, height=200, key="transcript_edit"
        )

        if edited_transcript != st.session_state.transcript_text:
            st.session_state.transcript_text = edited_transcript
            st.rerun()
        
        st.markdown("### 📝 Notizen")
        current_interview = get_interview_by_id(st.session_state.current_interview_id)
        current_notes = current_interview.get('notes', '') if current_interview else ''
        notes = st.text_area("Zusätzliche Beobachtungen:", value=current_notes, height=100, key="notes_field")
        
        if st.button("💾 Notizen speichern", use_container_width=True):
            update_interview_field(st.session_state.current_interview_id, "notes", notes)
            st.success("✅ Notizen gespeichert!")

with tab2:
    st.header("📊 Interview-Übersicht")
    conn = sqlite3.connect('interviews.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM interviews ORDER BY created_at DESC')
    interviews = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if interviews:
        st.write(f"**Gesamt: {len(interviews)} Interviews**")
        for interview in interviews:
            with st.expander(f"Interview #{interview['id']} - {interview['interview_date']} - {interview['interviewer']}"):
                st.write(f"**Person:** {interview['interviewee_info']}")
                st.write(f"**Textlänge:** {len(interview['transcription'] or '')} Zeichen")
                if interview['transcription']:
                    st.text_area("Transkription:", value=interview['transcription'], height=150, disabled=True, key=f"trans_{interview['id']}")
                else:
                    st.warning("⚠️ Keine Transkription")
                if interview['notes']:
                    st.info(f"**Notizen:** {interview['notes']}")
                html_content = generate_pdf_simple(interview)
                st.download_button(
                    label=f"📥 Interview #{interview['id']} als HTML", data=html_content,
                    file_name=f"interview_{interview['id']}.html", mime="text/html",
                    key=f"download_{interview['id']}"
                )
    else:
        st.info("Bisher wurden keine Interviews erfasst.")
    
    if st.button("📥 Alle Interviews als JSON exportieren"):
        json_str = json.dumps(interviews, indent=2, ensure_ascii=False, default=str)
        st.download_button(
            label="⬇️ JSON-Datei jetzt herunterladen", data=json_str,
            file_name=f"alle_interviews_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with tab3:
    st.header("ℹ️ Anleitung")
    st.markdown("""
    ### 🚀 **So funktioniert's**
    
    1.  **Interview erstellen:**
        -   Im Tab `📝 Neues Interview` die Details (Interviewer, Datum etc.) ausfüllen.
        -   Die Checkbox für das Einverständnis anhaken.
        -   Auf `📋 Neues Interview starten` klicken.
    
    2.  **Aufnehmen & Bearbeiten:**
        -   Sobald das Interview aktiv ist, erscheint der Aufnahmebereich.
        -   Auf `▶️ Start` klicken, um die Spracherkennung zu beginnen.
        -   Der gesprochene Text erscheint **live** im unteren Textfeld.
        -   Du kannst jederzeit im Textfeld **Korrekturen tippen**, auch während die Aufnahme läuft.
        -   Mit `⏹️ Stop` wird die Aufnahme pausiert.
    
    3.  **Speichern & Abschließen:**
        -   Klicke auf `💾 Zwischenspeichern`, um den aktuellen Text in der Datenbank zu sichern.
        -   Wenn das Interview fertig ist, klicke auf `✅ Abschließen & Exportieren`, um die finale Version zu speichern und eine HTML/PDF-Datei herunterzuladen.
    
    ---
    
    ### 💡 **Wichtige Hinweise**
    
    -   **Automatische Übertragung:** Du musst den Text nicht mehr manuell kopieren. Was du sprichst, landet direkt im Textfeld.
    -   **Browser-Zugriff:** Du musst beim ersten Mal den Zugriff auf dein Mikrofon im Browser erlauben.
    -   **Browser-Kompatibilität:** Die App funktioniert am besten mit **Google Chrome** oder **Microsoft Edge** auf einem Computer oder Android-Gerät.
    -   **Notizen:** Du kannst jederzeit Notizen hinzufügen und separat speichern.
    """)

