import streamlit as st
import sqlite3
from datetime import datetime
import json
from typing import Dict, Any

# PDF-Generierung
def generate_pdf_simple(interview_data):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Interview #{interview_data.get('id', 'N/A')}</title>
        <style>
            @media print {{
                body {{ margin: 0; }}
                .no-print {{ display: none; }}
            }}
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #34495e; margin-top: 30px; }}
            .metadata {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            .metadata p {{ margin: 5px 0; }}
            .transcription {{
                background: #ffffff;
                border: 1px solid #ddd;
                padding: 20px;
                border-radius: 5px;
                white-space: pre-wrap;
                margin: 20px 0;
            }}
            .notes {{
                background: #fff9e6;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
            }}
            .footer {{
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                color: #666;
                font-size: 12px;
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

st.set_page_config(page_title="Interview Transkription", page_icon="🎤", layout="wide")

st.markdown("""
<style>
    .stApp { max-width: 100%; padding: 0.5rem; }
    .stButton > button { width: 100%; min-height: 60px; font-size: 18px; font-weight: bold; border-radius: 10px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

# Datenbank
def init_database():
    try:
        conn = sqlite3.connect('interviews.db')
        cursor = conn.cursor()
        cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='interviews'")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                CREATE TABLE interviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    interview_date TEXT NOT NULL,
                    interviewer TEXT,
                    interviewee_info TEXT,
                    transcription TEXT,
                    notes TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    date_str = interview_data.get('date', datetime.now().isoformat())
    if isinstance(date_str, datetime):
        date_str = date_str.isoformat()
    cursor.execute('''
        INSERT INTO interviews (interview_date, interviewer, interviewee_info, transcription, notes, metadata)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        date_str,
        interview_data.get('interviewer', ''),
        interview_data.get('interviewee_info', ''),
        interview_data.get('transcription', ''),
        interview_data.get('notes', ''),
        json.dumps(interview_data.get('metadata', {}))
    ))
    interview_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return interview_id

def update_interview_transcription(interview_id: int, transcription: str):
    conn = sqlite3.connect('interviews.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE interviews SET transcription = ? WHERE id = ?', (transcription, interview_id))
    conn.commit()
    conn.close()

def get_interview_by_id(interview_id: int):
    conn = sqlite3.connect('interviews.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, interview_date, interviewer, interviewee_info, transcription, notes, created_at FROM interviews WHERE id = ?', (interview_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {'id': result[0], 'date': result[1], 'interviewer': result[2], 'interviewee_info': result[3], 'transcription': result[4], 'notes': result[5], 'created_at': result[6]}
    return None

def create_speech_interface(interview_id):
    return f"""
    <div style="padding: 20px; background: #f8f9fa; border-radius: 10px;">
        <div style="text-align: center; margin-bottom: 20px;">
            <span id="status" style="font-size: 18px; font-weight: bold;">🎤 Bereit</span>
        </div>
        <div style="text-align: center; margin-bottom: 20px;">
            <button onclick="start()" id="startBtn" style="background: #4CAF50; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin: 5px;">▶️ Start</button>
            <button onclick="stop()" id="stopBtn" disabled style="background: #f44336; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin: 5px;">⏹️ Stop</button>
            <a id="dlBtn" style="display: none; background: #2196F3; color: white; padding: 15px 30px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin: 5px; text-decoration: none;">💾 Download TXT</a>
        </div>
        <div style="margin-top: 20px;">
            <label style="font-weight: bold;">🗣️ Live:</label>
            <div id="interim" style="color: #666; font-style: italic; background: white; padding: 10px; border-radius: 5px; min-height: 30px;">...</div>
        </div>
        <div style="margin-top: 20px;">
            <label style="font-weight: bold;">📝 Transkription:</label>
            <div id="final" style="background: white; padding: 15px; border-radius: 5px; min-height: 150px; max-height: 300px; overflow-y: auto; white-space: pre-wrap;"></div>
        </div>
    </div>

    <script>
        let rec = null;
        const key = 'tr_{interview_id}';
        let txt = localStorage.getItem(key) || '';
        let active = false;
        
        if (txt) document.getElementById('final').textContent = txt;

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
            
            rec.onresult = (e) => {{
                let interim = '';
                for (let i = e.resultIndex; i < e.results.length; i++) {{
                    let t = e.results[i][0].transcript.replace(/gruezi/gi, 'Grüezi').replace(/merci/gi, 'Merci');
                    if (e.results[i].isFinal) {{
                        txt += t + ' ';
                        document.getElementById('final').textContent = txt;
                        localStorage.setItem(key, txt);
                        updateDownload();
                    }} else {{
                        interim += t;
                    }}
                }}
                document.getElementById('interim').textContent = interim || '...';
            }};
            
            rec.onerror = (e) => {{
                if (e.error === 'no-speech' && active) {{
                    setTimeout(() => {{ if (active) rec.start(); }}, 100);
                }} else if (e.error === 'not-allowed') {{
                    alert('Mikrofon-Zugriff verweigert!');
                    document.getElementById('status').innerHTML = '❌ Kein Zugriff';
                    reset();
                }}
            }};
            
            rec.onend = () => {{
                if (active) rec.start();
                else reset();
            }};
        }} else {{
            document.getElementById('status').innerHTML = '❌ Browser nicht unterstützt';
            document.getElementById('startBtn').disabled = true;
        }}
        
        function start() {{ if (rec) rec.start(); }}
        
        function stop() {{
            if (rec) {{
                active = false;
                rec.stop();
                document.getElementById('status').innerHTML = '✅ Gestoppt';
                localStorage.setItem(key, txt);
                updateDownload();
            }}
        }}
        
        function reset() {{
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            active = false;
        }}
        
        function updateDownload() {{
            const btn = document.getElementById('dlBtn');
            if (txt) {{
                const blob = new Blob([txt], {{type: 'text/plain;charset=utf-8'}});
                const url = URL.createObjectURL(blob);
                btn.href = url;
                btn.download = 'interview_{interview_id}_' + new Date().toISOString().slice(0,10) + '.txt';
                btn.style.display = 'inline-block';
            }}
        }}
        
        window.addEventListener('load', updateDownload);
        window.addEventListener('beforeunload', () => {{ if (txt) localStorage.setItem(key, txt); }});
    </script>
    """

# Session State
if 'current_interview_id' not in st.session_state:
    st.session_state.current_interview_id = None
if 'transcript_text' not in st.session_state:
    st.session_state.transcript_text = ""

if not init_database():
    st.stop()

st.title("🎤 Interview Transkription")
st.caption("Wildvogelpflegestation - Besucherbefragung")

tab1, tab2, tab3 = st.tabs(["📝 Neues Interview", "📊 Übersicht", "ℹ️ Hilfe"])

with tab1:
    with st.expander("👤 Interview-Details", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            interviewer = st.text_input("Interviewer*in:", key="interviewer")
        with col2:
            interview_date = st.date_input("Datum:", value=datetime.now())
        interviewee_info = st.text_area("Interviewte Person:", placeholder="Alter, Geschlecht, Eindrücke...", height=60)
    
    consent = st.checkbox("✅ Einverständnis wurde eingeholt")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Neues Interview", disabled=not (consent and interviewer), use_container_width=True, type="primary"):
            interview_data = {
                'date': interview_date,
                'interviewer': interviewer,
                'interviewee_info': interviewee_info,
                'transcription': '',
                'notes': '',
                'metadata': {}
            }
            interview_id = save_interview(interview_data)
            if interview_id:
                st.session_state.current_interview_id = interview_id
                st.session_state.transcript_text = ""
                st.success(f"✅ Interview #{interview_id} erstellt")
                st.rerun()
    
    with col2:
        if st.session_state.current_interview_id:
            if st.button("💾 In DB speichern", use_container_width=True):
                if st.session_state.transcript_text:
                    update_interview_transcription(st.session_state.current_interview_id, st.session_state.transcript_text)
                    st.success("✅ Gespeichert!")
                else:
                    st.warning("⚠️ Kein Text!")
    
    with col3:
        if st.session_state.current_interview_id:
            if st.button("✅ Abschließen", use_container_width=True, type="secondary"):
                if st.session_state.transcript_text:
                    update_interview_transcription(st.session_state.current_interview_id, st.session_state.transcript_text)
                interview_data = get_interview_by_id(st.session_state.current_interview_id)
                if interview_data:
                    html_content = generate_pdf_simple(interview_data)
                    st.download_button(
                        label="📥 HTML/PDF herunterladen",
                        data=html_content,
                        file_name=f"interview_{st.session_state.current_interview_id}_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                        mime="text/html",
                        use_container_width=True
                    )
                st.success(f"✅ Interview #{st.session_state.current_interview_id} abgeschlossen!")
                st.session_state.current_interview_id = None
                st.session_state.transcript_text = ""
    
    if st.session_state.current_interview_id:
        st.info(f"📍 Aktuelles Interview: #{st.session_state.current_interview_id}")
        
        st.markdown("### 🎙️ Sprachaufnahme")
        st.components.v1.html(create_speech_interface(st.session_state.current_interview_id), height=450)
        
        st.markdown("---")
        st.markdown("### ✏️ Text bearbeiten / einfügen")
        st.info("👆 **Nach Aufnahme:** Auf '💾 Download TXT' klicken, dann Datei öffnen und hier einfügen!")
        
        transcript = st.text_area(
            "Text hier einfügen:",
            value=st.session_state.transcript_text,
            height=200,
            key="transcript_edit"
        )
        
        if transcript != st.session_state.transcript_text:
            st.session_state.transcript_text = transcript
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Speichern", use_container_width=True, type="primary"):
                if transcript:
                    update_interview_transcription(st.session_state.current_interview_id, transcript)
                    st.success("✅ Gespeichert!")
                else:
                    st.warning("⚠️ Kein Text!")
        
        with col2:
            if st.button("🔄 Aus DB laden", use_container_width=True):
                interview_data = get_interview_by_id(st.session_state.current_interview_id)
                if interview_data and interview_data.get('transcription'):
                    st.session_state.transcript_text = interview_data['transcription']
                    st.rerun()
                else:
                    st.info("Keine Daten in DB")
        
        with col3:
            if st.button("🗑️ Löschen", use_container_width=True):
                st.session_state.transcript_text = ""
                st.rerun()
        
        st.markdown("### 📝 Notizen")
        current_interview = get_interview_by_id(st.session_state.current_interview_id)
        current_notes = current_interview.get('notes', '') if current_interview else ''
        notes = st.text_area("Zusätzliche Beobachtungen:", value=current_notes, height=100, key="notes_field")
        
        if st.button("💾 Notizen speichern"):
            conn = sqlite3.connect('interviews.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE interviews SET notes = ? WHERE id = ?', (notes, st.session_state.current_interview_id))
            conn.commit()
            conn.close()
            st.success("✅ Notizen gespeichert!")

with tab2:
    st.header("📊 Interview-Übersicht")
    conn = sqlite3.connect('interviews.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, interview_date, interviewer, interviewee_info, LENGTH(transcription) as length, transcription, notes FROM interviews ORDER BY created_at DESC')
    interviews = cursor.fetchall()
    conn.close()
    
    if interviews:
        st.write(f"**Gesamt: {len(interviews)} Interviews**")
        for interview in interviews:
            with st.expander(f"Interview #{interview[0]} - {interview[1]} - {interview[2]}"):
                st.write(f"**Person:** {interview[3]}")
                st.write(f"**Textlänge:** {interview[4]} Zeichen")
                if interview[5]:
                    st.text_area("Transkription:", value=interview[5], height=150, disabled=True, key=f"trans_{interview[0]}")
                else:
                    st.warning("⚠️ Keine Transkription")
                if interview[6]:
                    st.info(f"**Notizen:** {interview[6]}")
                
                interview_data = {
                    'id': interview[0], 'date': interview[1], 'interviewer': interview[2],
                    'interviewee_info': interview[3], 'transcription': interview[5] or 'Keine Transkription',
                    'notes': interview[6], 'created_at': interview[1]
                }
                html_content = generate_pdf_simple(interview_data)
                st.download_button(
                    label=f"📥 Interview #{interview[0]} als HTML",
                    data=html_content,
                    file_name=f"interview_{interview[0]}.html",
                    mime="text/html",
                    key=f"download_{interview[0]}"
                )
    else:
        st.info("Noch keine Interviews")
    
    if st.button("📥 Alle als JSON exportieren"):
        conn = sqlite3.connect('interviews.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM interviews')
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        json_str = json.dumps(data, indent=2, ensure_ascii=False, default=str)
        st.download_button(
            label="⬇️ JSON herunterladen",
            data=json_str,
            file_name=f"alle_interviews_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

with tab3:
    st.header("ℹ️ Anleitung")
    st.markdown("""
    ### 🚀 So geht's
    
    1. **Interview erstellen:** Details eingeben → Einverständnis ✅ → "Neues Interview"
    2. **Aufnehmen:** "▶️ Start" → Sprechen → "⏹️ Stop"
    3. **Speichern:** Auf "💾 Download TXT" klicken → Datei öffnen → Text kopieren → In Textfeld einfügen → "💾 Speichern"
    4. **Abschließen:** "✅ Abschließen" → HTML/PDF Download
    
    ### 💡 Wichtig
    - **Download TXT Button** erscheint nach dem Stoppen der Aufnahme
    - Text wird **lokal im Browser** gespeichert
    - **Manuell** in DB übertragen mit "💾 Speichern"
    - Bei längeren Interviews: Regelmäßig speichern!
    
    ### 📱 Browser
    - ✅ Chrome/Edge (empfohlen)
    - ❌ Safari iOS
    """)