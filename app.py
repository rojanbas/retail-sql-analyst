import streamlit as st
import sqlite3
import pandas as pd
from sql_agent import ask_question

st.set_page_config(
    page_title="Retail SQL Analyst",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 AI-Powered Retail SQL Analyst")
st.markdown("Ask any business question about the retail database in plain English")

# Sidebar
with st.sidebar:
    st.header("📊 Database Info")
    st.markdown("""
    **Tables available:**
    - CUSTOMERS (600 rows)
    - ORDERS (600 rows)
    - ORDER_ITEMS (600 rows)
    - PRODUCTS (600 rows)
    - PAYMENTS (600 rows)
    - SHIPPING (600 rows)
    - COUNTRIES (10 rows)
    """)

    st.header("💡 Try These Questions")
    sample_questions = [
        "Which country had the most orders?",
        "What is the total revenue by country?",
        "How many orders were cancelled?",
        "Which payment type is most common?",
        "What are the top 5 most expensive products?",
        "How many orders were shipped by UPS?",
        "What was the total revenue?",
    ]

    for q in sample_questions:
        if st.button(q, use_container_width=True):
            st.session_state.question = q

# Main area
question = st.text_input(
    "Ask your question:",
    value=st.session_state.get("question", ""),
    placeholder="e.g. Which country had the most orders?"
)

if question:
    with st.spinner("AI is thinking..."):
        try:
            answer, sql_query = ask_question(question)

            # Show answer
            st.subheader("💬 Answer")
            st.success(answer)

            # Show SQL
            with st.expander("🔍 View Generated SQL Query"):
                st.code(sql_query, language="sql")

            # Show raw data table
            with st.expander("📋 View Raw Data"):
                try:
                    conn = sqlite3.connect("data/retail.db")
                    df = pd.read_sql_query(sql_query, conn)
                    conn.close()
                    st.dataframe(df)
                except Exception as e:
                    st.error(f"Could not display table: {e}")

        except Exception as e:
            st.error(f"Error: {e}")
            st.info("Make sure Ollama is running in the background")

else:
    st.info("👆 Type a question above or click one from the sidebar")