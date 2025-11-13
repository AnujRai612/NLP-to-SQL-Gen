#Step1: Extract Schema

from sqlalchemy import create_engine, inspect
import json
import re


db_url = "sqlite:///amazon.db"

def extract_schema(db_url):
    engine = create_engine(db_url)
    inspector = inspect(engine)
    schema = {}

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        schema[table_name] = [col['name'] for col in columns]
    return json.dumps(schema)

#Step2: Text to SQL (GROQ -llama)

import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
load_dotenv()
GROQ_API_KEY=os.getenv("GROQ_API_KEY")
os.environ["GROQ_API_KEY"]=GROQ_API_KEY


def text_to_sql(schema, prompt):
    SYSTEM_PROMPT = """
    You are an expert SQL generator. Given a database schema and a user prompt, generate a valid SQL query that answers the prompt. 
    Only use the tables and columns provided in the schema. ALWAYS ensure the SQL syntax is correct and avoid using any unsupported features. 
    Output only the SQL as your response will be directly used to query data from the database. No preamble please. Do not use <think> tags.
    """
    llm=ChatGroq(model="llama-3.3-70b-versatile",temperature=0)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", "Schema:\n{schema}\n\nQuestion: {user_prompt}\n\nSQL Query:")
    ])


    chain = prompt_template | llm
    raw_response = chain.invoke({"schema": schema, "user_prompt": prompt})
    if hasattr(raw_response, "content"):
        raw_response = raw_response.content

    cleaned_response = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL)
    return cleaned_response.strip()


schema=extract_schema(db_url)
prompt="Tell me the names of all the customers"
sql_query=text_to_sql(schema,prompt)
print(sql_query)