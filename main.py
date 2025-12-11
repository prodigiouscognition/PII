import streamlit as st
import pandas as pd
from pii import UnifiedPIIPipeline

# --- CONFIG & EXAMPLES ---
EXAMPLES = [
    "Write your own text...", # Default option
    "Ich bin am 12.04.1985 geboren (also 40 Jahre alt) und benötige Insulin wegen Diabetes, hier ist mein Ausweis: L01X00T47.",
    "Erreichen Sie mich unter ojaswini@gmail.com oder besuchen Sie www.hamburg.de/service für Termine.",
    "Mein Büro in der Hauptstraße 15, 20095 Hamburg ist ab 9 Uhr unter 040-12345678 erreichbar.",
    "Hier ist eine gültige IBAN für die Überweisung: DE43 2127 2486 1917 6073 77.",
    "Bitte belasten Sie meine Karte 4929 1234 5678 9015.",
    "Meine Glückszahl ist 1234 5678 1234 5671 und keine Kreditkarte.",
    "Der Patient nimmt Aspirin wegen starker Migräne.",
    "Morgen habe ich einen Termin für ein MRT und eine Blutabnahme.",
    "Frau Müller hat den Vertrag unterschrieben.",
    "Olaf Scholz und Robert Habeck waren heute in Berlin.",
    "Dr. Weber und Anwalt Schmidt sind im Meeting.",
    "Führerschein-Nr: B072R6U5359.",
    "Meine Handynummer ist privat (kein Führerschein).",
    "Steuer-ID: 12345678901.",
    "Reisepassnummer: C01X00T47."
]

# --- CACHED RESOURCE LOADING ---
@st.cache_resource
def load_pipeline():
    return UnifiedPIIPipeline()

def mask_pii_logic(input_text):
    pipeline = load_pipeline()
    output = pipeline.process_batch([input_text])
    return output

def update_text_area():
    """Callback to update text area based on dropdown selection"""
    selected = st.session_state.example_selector
    if selected != "Write your own text...":
        st.session_state.input_text_key = selected

def main():
    st.set_page_config(layout="wide", page_title="PII Redaction System")
    st.title("PII Redaction System")

    # --- INPUT SECTION ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Source Input")
        
        # 1. The Dropdown Selector
        st.selectbox(
            "Choose an example or write your own:",
            options=EXAMPLES,
            key="example_selector",
            on_change=update_text_area, # Triggers update when selection changes
            label_visibility="visible"
        )

        # 2. The Text Area (Linked to session state)
        # We use key='input_text_key' so we can modify it programmatically via the callback
        user_text = st.text_area(
            "Input Text", 
            height=250, 
            key="input_text_key",
            label_visibility="collapsed",
            placeholder="Select an example above or type here..."
        )
        
        process_btn = st.button("Run Masking Pipeline", type="primary", use_container_width=True)

    # --- OUTPUT SECTION ---
    if process_btn and user_text.strip():
        with st.spinner("Running inference..."):
            results = mask_pii_logic(user_text)
            data = results[0]

        with col2:
            st.subheader("Anonymized Output")
            st.text_area("Output", value=data['anonymized_text'], height=335, label_visibility="collapsed")

        # --- DIAGNOSTICS & ANALYSIS ---
        st.divider()
        st.subheader("Inference Analysis")

        # Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Processing Time", f"{data['processing_time_ms']} ms")
        m2.metric("PII Detected", "Yes" if data['has_pii'] else "No")
        m3.metric("Entity Count", len(data['detections']))

        # Dataframe
        if data['detections']:
            st.write("### Detected Entities")
            df = pd.DataFrame(data['detections'])
            
            # Select/Reorder columns if they exist in your output
            cols_to_show = ['text', 'type', 'confidence', 'start', 'end', 'token']
            # Filter to ensure we only show columns that actually exist in the response
            valid_cols = [c for c in cols_to_show if c in df.columns]
            df = df[valid_cols]
            
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "confidence": st.column_config.ProgressColumn(
                        "Confidence",
                        format="%.2f",
                        min_value=0,
                        max_value=1,
                    ),
                    "token": st.column_config.TextColumn("Mask Token", width="medium"),
                }
            )
    elif process_btn:
        st.warning("Please enter or select text to process.")

if __name__ == "__main__":
    main()