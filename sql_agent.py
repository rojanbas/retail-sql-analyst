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

    # Groq instead of Ollama — free and fast
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",   # free LLaMA 3 model via Groq
        temperature=0,
        api_key=os.getenv("GROQ_API_KEY")
    )

    table_info = db.get_table_info()

    # Step 1: Generate SQL
    sql_prompt = PromptTemplate.from_template("""
    You are a SQL expert working with a retail database.
    Write a SQLite SQL query to answer the question below.
    Return ONLY the raw SQL query. No explanation. No markdown. No backticks.

    STRICT RULES:
    - ALWAYS use O as alias for ORDERS, C as alias for COUNTRIES
    - ALWAYS use C.COUNTRY_NAME and COUNT(O.ORDER_ID) as total
    - ALWAYS use GROUP BY C.COUNTRY_ID
    - ALWAYS end with ORDER BY total DESC LIMIT 1 for most questions
    - ALWAYS end with ORDER BY total ASC LIMIT 1 for least questions
    - For revenue use SUM(O.TOTAL_AMOUNT) as total
    - For joins: FROM ORDERS O JOIN COUNTRIES C ON C.COUNTRY_ID = O.COUNTRY_ID
    - ALWAYS SELECT both the label AND the number together
    - ALWAYS use table aliases to avoid ambiguous column names

    Table structure:
    {table_info}

    Question: {question}

    SQL Query:
    """)

    sql_chain = sql_prompt | llm | StrOutputParser()
    sql_query = sql_chain.invoke({
        "table_info": table_info,
        "question": question
    })

    # Clean up
    sql_query = sql_query.strip()
    for marker in ["```sql", "```SQL", "```"]:
        sql_query = sql_query.replace(marker, "")
    sql_query = sql_query.strip()

    print(f"\nGenerated SQL:\n{sql_query}")

    # Step 2: Run SQL
    results, columns = run_sql(sql_query)

    if results is None:
        print(f"\nSQL Error: {columns}")
        return "Could not run the query.", sql_query

    print(f"\nRaw Results: {results}")

    # Step 3: Format results
    if results:
        formatted = "\n".join([
            ", ".join([f"{columns[i]}: {row[i]}"
            for i in range(len(columns))])
            for row in results
        ])
    else:
        formatted = "No results found"

    print(f"\nFormatted Results:\n{formatted}")

    # Step 4: Generate plain English answer
    answer_prompt = PromptTemplate.from_template("""
    You are a friendly and insightful retail business analyst presenting
    findings to a business executive.

    Question: {question}

    Exact database results:
    {formatted_results}

    Write a response that:
    - Starts with the direct answer using the exact numbers
    - Adds one business insight about what this means
    - Suggests one possible business action based on the finding
    - Uses a warm professional tone — not robotic
    - Keeps it to 3-4 sentences maximum
    - Never make up numbers — only use what is in the results above
    """)

    answer_chain = answer_prompt | llm | StrOutputParser()
    answer = answer_chain.invoke({
        "question": question,
        "formatted_results": formatted
    })

    return answer, sql_query


if __name__ == "__main__":
    print("Testing with Groq API...")
    answer, sql = ask_question("Which country had the most orders?")
    print("\nFinal Answer:")
    print(answer)