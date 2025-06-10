import streamlit as st
from fact_checker import FactChecker
from openai import OpenAI
import os
from dotenv import load_dotenv
import csv
from datetime import datetime

load_dotenv()

def store_feedback_csv(claim, result, feedback, csv_file="feedback_log.csv"):
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
        chroma_path="chroma_db",
        collection_name="pib_titles",
        groq_client=OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
    )

def main():
    st.title("🔍 Fact Checker")
    checker = initialize_services()

    # Initialize session state variables
    if "feedback_submitted" not in st.session_state:
        st.session_state.feedback_submitted = False
    if "last_claim" not in st.session_state:
        st.session_state.last_claim = ""
    if "result" not in st.session_state:
        st.session_state.result = None

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


if __name__ == "__main__":
    main()
