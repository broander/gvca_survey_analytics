"""
Access chatgpt from the cli and analyze open response data
"""

import datetime
import subprocess

from sqlalchemy import create_engine, text

from hello_gpt_assistant import (chat_subprocess, load_message_history,
                                 save_prompt_file)
from utilities import load_env_vars

# path to the hello_gpt_assistant.py script to call as a subprocess
AI_SCRIPT_PATH = "./hello_gpt_assistant.py"

# specify the desired model to be used for the OpenAI API
# see models here: https://platform.openai.com/docs/models
OPENAI_MODEL_NAME = "o1-mini"

# specify the initial prompt context for the OpenAI API
# prompt engineering best practices:
# https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api
# prompt context for the open response analysis task
OPENAI_PROMPT_CONTEXT = """
    You are a skilled analyst with experience in survey and sentiment analysis.
    You have been asked to analyze the responses to an annual survey of parents
    of the students at a classical education focused charter school named Golden
    View Classical Academy.  The survey was conducted to gather feedback from
    the parents on the school's performance and to identify areas for focus by
    the school accountability committee to be shared with the school board and
    administration.  The survey responses you are getting are from the open
    response questions on the survey.  Your task is to analyze the responses and
    provide a summary of the key themes and areas of focus.  You should produce
    first a written summary of the key themes and areas of focus, and then
    second a list of 10-20 bullet point category names that capture the main
    themes shared in the open responses.
    \n
    In analyzing the responses, consider the following categories which showed
    up in survey results in past years and may be relevant to analyzing this
    years results.  If relevant, include these categories in your analysis and
    results.
    \n
    These categories to consider are: Concern, Curriculum, Good Outcomes,
    Policies & Administration, Teachers, Culture & Virtues, Wellbeing,
    Communication, Community, Extra-curriculars & Sports, Facilities, and
    Other.
    """

# specify optional prompt history file to load
HISTORY_FILE_NAME = ""
# HISTORY_FILE_NAME = "2025-01-13_04-07-37_ai_response_analysis.json"

# Output Files Location
OUTPUT_FILES_LOCATION = "./response_analysis_logs/"
# Output File Name global variable based on current date and time
OUTPUT_FILE_NAME = datetime.datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S" + "_ai_response_analysis"
)

CHAT_SUBPROCESS_ARGS = [
    "python",
    AI_SCRIPT_PATH,
    "--model",
    OPENAI_MODEL_NAME,
    "--context",
    OPENAI_PROMPT_CONTEXT,
    "--history",
    HISTORY_FILE_NAME,
    "--file",
    OUTPUT_FILE_NAME,
    "--location",
    OUTPUT_FILES_LOCATION,
]

# load environment variables from .env file
INPUT_FILEPATH, DATABASE_SCHEMA, DATABASE_CONNECTION_STRING = load_env_vars()

# database query to get the open response data
# DATABASE_QUERY = "SELECT respondent_id, response FROM question_open_responses;"
DATABASE_QUERY = "SELECT response FROM question_open_responses;"


def query_database(database_connection_string, query, database_schema=None):
    """
    Query the target database connection and schema using the provided query
    string
    """
    engine = create_engine(database_connection_string)
    with engine.connect() as connection:
        if database_schema is not None:
            command = f"SET SCHEMA '{database_schema}';"
            connection.execute(text(command))
        result = connection.execute(text(query))
        return result.fetchall()


def analyze_responses(
    database_connection_string=DATABASE_CONNECTION_STRING,
    query=DATABASE_QUERY,
    schema=DATABASE_SCHEMA,
    subprocess_args=CHAT_SUBPROCESS_ARGS,
):
    """
    Analyze the open responses using the OpenAI API
    """

    # prompt engineering pipeline:

    # 1. build prompt to submit the responses data to the AI

    # get the open responses from the database
    open_responses = query_database(database_connection_string, query, schema)

    # Prepare the responses for submitting as first prompt
    prompt = "Here are the survey responses to analyze:\n"
    for response in open_responses:
        prompt += f"- {response[0]}\n"

    # save the prompt to a file so can pass to the subprocess as an argument
    # to avoid issues with very long prompt data inputs
    # TODO: consider refactor to use a temporary file
    # TODO: refactor file path to align with TODOs on save file functions
    temp_prompt_file_name = "temp_prompt_file"
    temp_prompt_file_path = temp_prompt_file_name
    temp_prompt_file_full_name = temp_prompt_file_path + ".txt"
    save_prompt_file(prompt, temp_prompt_file_path)

    # add the prompt file to the subprocess arguments
    subprocess_args.append("--prompt_file")
    subprocess_args.append(temp_prompt_file_full_name)

    # 2. call the chatgpt subprocess to analyze the responses, using the

    # prompt context provided as a global variable and taking the responses
    chat_subprocess(subprocess_args)

    # 3. Continue to chat with the AI to refine the analysis and save the
    # results to a file for later use

    # cleanup the temporary prompt file
    subprocess.run(
        ["rm", temp_prompt_file_full_name],
        check=True,
    )


def main():
    """
    Main program
    """
    analyze_responses()


if __name__ == "__main__":
    main()
