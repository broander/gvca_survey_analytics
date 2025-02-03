"""
Access chatgpt from the cli and analyze open response data
"""

import datetime
import logging
import re
import sys

import pexpect
from sqlalchemy import create_engine, text

from hello_gpt_assistant import (chat_subprocess, load_message_history,
                                 save_prompt_file)
from utilities import load_env_vars

# path to the hello_gpt_assistant.py script to call as a subprocess
AI_SCRIPT_PATH = "./hello_gpt_assistant.py"

# specify the desired model to be used for the OpenAI API
# see models here: https://platform.openai.com/docs/models
OPENAI_MODEL_NAME = "o1-mini"
# OPENAI_MODEL_NAME = "gpt-4o"

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
    response questions on the survey.
    \n
    Only provide strict categorization using this list of categories, and use
    no other cateogires:
    - Concern
    - Curriculum
    - Good Outcomes
    - Policies & Administration
    - Teachers
    - Culture & Virtues
    - Wellbeing
    - Communication
    - Community
    - Extra-curriculars & Sports
    - Facilities
    - Other
    \n
    Return the results as a structured json output, maintaining the original
    stucture but adding a new column to the results providing a list of comma
    delimited categories that apply to each response.  With that, include categorization, and don't include the original response column or the question text column in
    your json response.  Add an additional column to the json output as the
    first column which counts the number of responses you have provided back,
    starting at 1, and continuing until you have provided the same number of
    responses as inputs that I gave you.  This column should be named 'count'.
    \n Do not abreviate your results, you need to provide a full response of
    every input entry back with the categorizations added.  Don't provide
    anything but json back as your response.  The count of json entries you
    provide as output must match the count of input survey responses I give
    you.  The respondent IDs, question IDs, and grade levels from the input must
    also all be the same in the output.  If you hallucinate new values for
    these, you will be penalized.  You have 128k tokens to use, so keep going
    in providing responses and don't give up with an abreviated response.
    \n
   """
# In your response, combine respondent_id, question_id, and grade_level into a comma-deliminted compound key called "key".

# - Now check and ensure that the number of json entries you provided as output is the same as the number of rows of input I gave you.  Tell me the count of both in your response.
# - Now check that the respondent IDs from the input are also all the same in the output and there are no new ones you hallucinated.

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
    # "--history",
    # HISTORY_FILE_NAME,
    "--file",
    OUTPUT_FILE_NAME,
    "--location",
    OUTPUT_FILES_LOCATION,
]

# load environment variables from .env file
INPUT_FILEPATH, DATABASE_SCHEMA, DATABASE_CONNECTION_STRING = load_env_vars()

# database query to get the open response data
# DATABASE_QUERY = "SELECT respondent_id, response FROM question_open_responses;"
DATABASE_QUERY = """
WITH all_respondent_questions AS
    (
    SELECT
        respondent_id,
        question_id,
        question_text
    FROM
        respondents
        CROSS JOIN
            questions
    WHERE
        question_type = 'open response'
    AND NOT soft_delete
    )
SELECT
    respondent_id,
    question_id,
    question_text,
    CASE
        WHEN grammar THEN 'Grammar'
        WHEN middle THEN 'Middle'
        WHEN high THEN 'High'
        WHEN whole_school THEN 'Whole School'
    END AS grade_level,
    response
FROM
    all_respondent_questions
    LEFT JOIN
        question_open_responses USING (respondent_id, question_id)
    ORDER BY
        respondent_id,
        question_id,
        grammar DESC,
        middle DESC,
        high DESC,
        whole_school DESC
"""


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

    Spawn the subprocess and monitor its output.
    When a pre-defined pattern is matched, send the corresponding input.
    If a pattern's input is None, prompt the user for manual input.
    """
    ### prompt engineering pipeline:

    ### 1. build response data to submit to the AI prompt

    # get the open responses from the database
    # is a list of tuples with:
    #   respondent_id, question_id, question_text, grade_level, and response
    open_responses = query_database(database_connection_string, query, schema)

    ### 2. Define the patterns and the responses

    # Adjust the keys (regex) and values as needed.
    # For auto-trigger strings, provide an automatic response.
    # For manual input, set the value to None.
    patterns = {
        # r"1>\s": "Stuff to send prompt",  # catch first prompt
        # catch-all prompt ending with a number and ">" for manual input
        r"\d+\>\s": None,
    }

    # Create a list of regex patterns in the order you want them matched and add
    # to the front of the patterns dictionary

    # counter to track adding prompt entries to the pattern dictionary
    counter = 0

    # Process the open_responses in chunks to avoid overwhelming the AI
    chunk_size = 25
    print(f"Total Count of Responses to Process: {len(open_responses)}")
    # tell the ai to expect responses in chunks, and how many total it will recieve
    counter += 1
    patterns = {
        "1>\s": f"I will give you the response data in chunks of {chunk_size}. There will be {len(open_responses)} total responses provided to process",
        **patterns,
    }

    # process the open_responses in chunks of 50 and add chunks to the pattern
    # dictionary
    for i in range(0, len(open_responses), chunk_size):
        counter += 1
        # print(f"Processing chunk {i + 1} to {i + chunk_size} of {len(open_responses)}")
        chunk = open_responses[i : i + chunk_size]
        # add a chunk to the pattern dictionary
        patterns = {f"{counter}>\s": str(chunk), **patterns}

    # now add another entry to save the results
    counter += 1
    patterns = {f"{counter}>\s": "s", **patterns}

    # ask the AI to check that the total number of responses returned matches
    # the total number of responses provided
    counter += 1
    patterns = {
        f"{counter}>\s": "Check that the number of responses you provided matches the number of input tuples you were given",
        **patterns,
    }

    # Create a list of regex patterns in the order you want them matched.
    regex_list = list(patterns.keys())

    ### 3. Spawn the subprocess and monitor its output
    # set up logging
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        filename="output.log",
        filemode="w",
    )

    # Spawn the subprocess using the same Python interpreter.
    # Buffer output will be written to sys.stdout so you can see progress in real time.
    # child = pexpect.spawn(sys.executable, [AI_SCRIPT_PATH], encoding="utf-8")
    child = pexpect.spawn(
        subprocess_args[0], encoding="utf-8", args=subprocess_args[1:]
    )
    # child.logfile = sys.stdout   # show input and output
    child.logfile_read = sys.stdout  # show only output to avoid duplication

    # define timeout for the expect function
    timeout = 60

    while True:
        try:
            # Wait for one of the patterns to appear
            index = child.expect(regex_list, timeout=timeout)
            triggered_pattern = regex_list[index]
            response = patterns[triggered_pattern]

            # Inform which pattern was triggered
            logging.info(f"\n[Pattern matched: {triggered_pattern}]")

            if response is not None:
                print(f"***Automatically sending***:\n")
                child.sendline(response)
            else:
                # No auto-response defined: get manual input from user
                # Requires accurate r"foobar": None pattern to be defined
                manual_input = input("Input> ")
                child.sendline(manual_input + "\n")
        except pexpect.EOF:
            logging.info("Subprocess ended (EOF received).")
            break
        except pexpect.TIMEOUT:
            # Continue waiting if nothing matched in the given timeout
            logging.info("Timeout occurred. Continuing...")
            continue

    ### 4. Continue to chat with the AI to refine the analysis and save the
    # results to a file for later use


def main():
    """
    Main program
    """
    analyze_responses()


if __name__ == "__main__":
    main()
