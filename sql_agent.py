import sqlite3
import os
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def get_database():
    db = SQLDatabase.from_uri(
        "sqlite:///data/retail.db",
        include_tables=[
            "CUSTOMERS", "ORDERS", "ORDER_ITEMS",
            "PRODUCTS", "PAYMENTS", "SHIPPING", "COUNTRIES"
        ]
    )
    return db

def run_sql(sql_query):
    """Run SQL directly on database"""
    conn = sqlite3.connect("data/retail.db")
    cursor = conn.cursor()
    try:
        cursor.execute(sql_query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return results, columns
    except Exception as e:
        conn.close()
        return None, str(e)

def ask_question(question):
    db = get_database()

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )

    table_info = db.get_table_info()

    # Step 1: Generate SQL
    sql_prompt = PromptTemplate.from_template("""
    You are an expert SQLite SQL writer for a retail database.
    Your job is to write ONE correct SQL query to answer the question.
    Return ONLY the raw SQL query — no explanation, no markdown, no backticks.

    GENERAL RULES:
    - Always use table aliases to avoid ambiguous column names
    - Always SELECT both the label and the value/count together
    - For counting use COUNT(), for totals use SUM()
    - For "most" use ORDER BY ... DESC LIMIT 1
    - For "least" use ORDER BY ... ASC LIMIT 1
    - For "top N" use ORDER BY ... DESC LIMIT N
    - For listing all use no LIMIT
    - Always qualify column names with their table alias

    TABLE RELATIONSHIPS:
    - ORDERS links to COUNTRIES via COUNTRY_ID
    - ORDERS links to CUSTOMERS via CUSTOMER_ID
    - ORDER_ITEMS links to ORDERS via ORDER_ID
    - ORDER_ITEMS links to PRODUCTS via PRODUCT_CODE
    - PAYMENTS links to ORDERS via ORDER_ID
    - SHIPPING links to ORDERS via ORDER_ID

    KEY COLUMNS:
    - Revenue/Amount: ORDERS.TOTAL_AMOUNT
    - Order count: COUNT(ORDERS.ORDER_ID)
    - Product name: PRODUCTS.DESCRIPTION
    - Country name: COUNTRIES.COUNTRY_NAME
    - Payment type: PAYMENTS.PAYMENT_TYPE
    - Carrier: SHIPPING.CARRIER
    - Order status: ORDERS.STATUS
    - Payment status: PAYMENTS.STATUS

    Database schema:
    {table_info}

    Question: {question}

    SQL Query:
    """)

    sql_chain = sql_prompt | llm | StrOutputParser()
    sql_query = sql_chain.invoke({
        "table_info": table_info,
        "question": question
    })

    # Clean up any markdown
    sql_query = sql_query.strip()
    for marker in ["```sql", "```SQL", "```"]:
        sql_query = sql_query.replace(marker, "")
    sql_query = sql_query.strip()

    print(f"\nGenerated SQL:\n{sql_query}")

    # Step 2: Run SQL
    results, columns = run_sql(sql_query)

    if results is None:
        print(f"\nSQL Error: {columns}")
        return "Sorry, I could not run that query. Please try rephrasing.", sql_query

    print(f"\nRaw Results: {results}")

    # Step 3: Format results clearly
    if results:
        formatted = "\n".join([
            ", ".join([f"{columns[i]}: {row[i]}"
            for i in range(len(columns))])
            for row in results
        ])
    else:
        formatted = "No results found"

    print(f"\nFormatted Results:\n{formatted}")

    # Step 4: Generate business answer
    answer_prompt = PromptTemplate.from_template("""
    You are a friendly retail business analyst presenting findings to an executive.

    Question asked: {question}

    Exact results from the database:
    {formatted_results}

    Write a 2-3 sentence response that:
    - Directly answers the question using the EXACT numbers from the results above
    - Adds one business insight about what this means
    - Suggests one action the business could take
    - Uses a warm professional tone
    - NEVER makes up numbers — only use what is shown in the results
    """)

    answer_chain = answer_prompt | llm | StrOutputParser()
    answer = answer_chain.invoke({
        "question": question,
        "formatted_results": formatted
    })

    return answer, sql_query


if __name__ == "__main__":
    # Test multiple different questions
    questions = [
        "Which country had the most orders?",
        "What is the most common payment type?",
        "How many orders were cancelled?",
        "What are the top 3 most expensive products?",
        "Which carrier shipped the most orders?"
    ]

    for q in questions:
        print(f"\n{'='*50}")
        print(f"Question: {q}")
        answer, sql = ask_question(q)
        print(f"\nAnswer: {answer}")