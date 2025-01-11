# FILE: analyze_with_chatgpt.py

import openai
import os
from sqlalchemy import create_engine

# Load environment variables
DATABASE_CONNECTION_STRING = os.getenv("DATABASE_CONNECTION_STRING")
DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY


def query_database(query):
    eng = create_engine(DATABASE_CONNECTION_STRING)
    with eng.connect() as conn:
        conn.execute(f"SET SCHEMA '{DATABASE_SCHEMA}';")
        result = conn.execute(query)
        return result.fetchall()


def analyze_with_chatgpt(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003", prompt=prompt, max_tokens=150
    )
    return response.choices[0].text.strip()


def main():
    # Example query to fetch data
    query = "SELECT response FROM question_open_responses LIMIT 10;"
    responses = query_database(query)

    # Prepare prompt for ChatGPT
    prompt = "Analyze the following survey responses:\n"
    for response in responses:
        prompt += f"- {response[0]}\n"

    # Get analysis from ChatGPT
    analysis = analyze_with_chatgpt(prompt)
    print("ChatGPT Analysis:\n", analysis)


if __name__ == "__main__":
    main()
