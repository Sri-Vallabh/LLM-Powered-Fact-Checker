import streamlit as st
from fact_checker import FactChecker
from openai import OpenAI
import os
from dotenv import load_dotenv
import csv
from datetime import datetime
import pandas as pd
import random

load_dotenv()

def store_feedback_csv(claim, result, feedback, csv_file="data/feedback_log.csv"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = [
        now,
        claim,
        result.get("verdict", ""),
        result.get("confidence", ""),
        "|".join(result.get("evidence", [])),
        result.get("reasoning", ""),
        feedback
    ]
    header = ["datetime", "claim", "verdict", "confidence", "evidence", "reasoning", "feedback"]
    
    # Create file if it doesn't exist
    if not os.path.exists(csv_file):
        with open(csv_file, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
    
    # Append to existing file
    with open(csv_file, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(row)

def initialize_services():
    return FactChecker(
        chroma_path="app/chroma_db",
        collection_name="pib_titles",
        groq_client=OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
    )

def main():
    # Add sticky title using HTML and CSS
    st.markdown("""
<style>
.sticky-title {
    position: sticky;
    top: 0;
    z-index: 999;
    background: white;
    padding-top: 1rem;
    padding-bottom: 1rem;
    margin-bottom: 1rem;
    border-bottom: 2px solid #f0f0f0;
}
</style>
<div class="sticky-title">
    <h1>🔍 Fact Checker</h1>
</div>
""", unsafe_allow_html=True)
    checker = initialize_services()

    # Initialize session state variables
    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = False
    if "last_claim" not in st.session_state:
        st.session_state.last_claim = ""
    if "result" not in st.session_state:
        st.session_state.result = None

    # --- Custom CSS for wider columns and better visuals ---
    st.markdown("""
<style>
/* Reduce max-width and remove side paddings/margins for full width */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    max-width: 100% !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
     text-align: center;
}

/* Remove default margins on main content to reduce gaps */
main > div {
    margin-left: 0 !important;
    margin-right: 0 !important;
}

/* Stretch columns fully */
.css-1kyxreq, .css-1r6slb0 {
    width: 100% !important;
}

/* Style the DataFrame container for full width */
.stDataFrame {
    background: #f9f9f9 !important;
    border-radius: 12px;
    border: 1px solid #e0e0e0;
    padding: 0.5rem;
    width: 100% !important;
}

/* Style input area */
textarea, input[type="text"] {
    border: 2px solid #4CAF50 !important;
    border-radius: 6px !important;
    font-size: 1.1rem !important;
    background: #f4f8fc !important;
    width: 100% !important;
}

/* Style buttons */
button[kind="primary"] {
    background: #4CAF50 !important;
    color: white !important;
    border-radius: 6px !important;
    font-weight: bold !important;
}

/* Style scrollbars for DataFrame */
::-webkit-scrollbar {
    width: 8px;
    background: #f0f0f0;
}
::-webkit-scrollbar-thumb {
    background: #bdbdbd;
    border-radius: 4px;
}
</style>
""", unsafe_allow_html=True)


    # --- Layout ---
    spacer_col, left_col, right_col ,right_space= st.columns([1,9, 7,1], gap="large")

    with left_col:
        claim = st.text_area("Enter a claim to verify:", height=150)
        confidence_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.5, 0.05)

        if st.button("Verify Claim"):
            if not claim.strip():
                st.error("Please enter a claim to verify")
                return

            with st.spinner("Analyzing..."):
                # Store result in session state
                st.session_state.result = checker.verify_claim(claim, confidence_threshold)
                st.session_state.last_claim = claim
                st.session_state.feedback_submitted = False  # Reset feedback state for new claim

        # Display results from session state
        if st.session_state.result:
            result = st.session_state.result
            if "error" in result:
                st.error(f"Error: {result['error']}")
                if "raw_response" in result:
                    with st.expander("Show raw LLM response"):
                        st.code(result["raw_response"])
            else:
                # Display verdict
                verdict_color = {
                    "True": "green",
                    "False": "red",
                    "Unverifiable": "orange"
                }.get(result["verdict"], "gray")
                st.markdown(f"**Verdict:** :{verdict_color}[{result['verdict']}]")
                
                # Display confidence score
                st.metric("Confidence Score", f"{result.get('confidence', 0):.2f}")
                
                # Display evidence
                with st.expander("View Supporting Evidence"):
                    for idx, evidence in enumerate(result.get("evidence", []), 1):
                        st.markdown(f"{idx}. {evidence}")
                
                # Display reasoning
                st.markdown("**Analysis:**")
                st.write(result.get("reasoning", "No reasoning provided"))

            # Feedback system
            feedback_key = f"feedback_radio_{st.session_state.last_claim}"
            if not st.session_state.feedback_submitted:
                feedback = st.radio(
                    "Was this analysis helpful?",
                    ["", "👍 Yes", "👎 No"],
                    horizontal=True,
                    key=feedback_key
                )
                
                if feedback:
                    store_feedback_csv(st.session_state.last_claim, result, feedback)
                    st.session_state.feedback_submitted = True
                    st.rerun()  # Use st.rerun() instead of experimental_rerun()
            else:
                st.success("Thank you for your feedback! Your input helps improve the system.")

    with right_col:
        
        st.markdown("### 📋 All Claims")
        try:
            df = pd.read_csv("data/pib_titles.csv")["title"].to_frame()
            if not df.empty:
                st.markdown("""
<style>
.scrollable-cell {
    overflow-x: auto;
    white-space: nowrap;
    max-width: 100%;
    border: 1px solid #eee;
    padding: 6px 8px;
    font-family: monospace;
    background: #fafafa;
}
</style>
""", unsafe_allow_html=True)

            

            # Render each row as a scrollable div
            for idx, row in df.iterrows():
                st.markdown(
                    f'<div class="scrollable-cell">{row["title"]}</div>',
                    unsafe_allow_html=True
    )
        except Exception as e:
            st.warning(f"Unable to display full dataset: {e}")
    


if __name__ == "__main__":
    main()
