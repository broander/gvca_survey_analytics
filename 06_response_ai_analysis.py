"""
Access chatgpt from the cli and analyze open response data
"""

import datetime
import logging
import re
import subprocess
import time

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
    delimited categories that apply to each response.  In your response,
    combine respondent_id, question_id, and grade_level into a
    comma-deliminted compound key called "key".  With that, include categorization,
    and don't include the original response column or the question text column in
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
    """

    # prompt engineering pipeline:

    # 1. build response data to submit to the AI prompt

    # get the open responses from the database
    # is a list of tuples with:
    #   respondent_id, question_id, question_text, grade_level, and response
    open_responses = query_database(database_connection_string, query, schema)

    ### data as list of tuples method
    # temp_prompt_file_name = "temp_prompt_file"
    # temp_prompt_file_path = temp_prompt_file_name
    # # dump the raw data in open_responses into a file using oob python
    # with open(temp_prompt_file_path + ".txt", "w") as f:
    #     # write open_responses as a string
    #     f.write(str(open_responses))
    # # breakpoint()

    ### data as text method
    # Prepare the responses as text for submitting as first prompt
    # prompt = "Here are the survey responses to analyze:\n"
    # for response in open_responses:
    #     # prompt += f"- {response[0]}\n"
    #     prompt += f"- {response}\n"

    # save the prompt to a file so can pass to the subprocess as an argument
    # to avoid issues with very long prompt data inputs
    # TODO: consider refactor to use a temporary file
    # TODO: refactor file path to align with TODOs on save file functions
    # temp_prompt_file_name = "temp_prompt_file"
    # temp_prompt_file_path = temp_prompt_file_name
    # temp_prompt_file_full_name = temp_prompt_file_path + ".txt"
    # save_prompt_file(prompt, temp_prompt_file_path)

    # add the temp prompt file to the subprocess arguments
    # subprocess_args.append("--prompt_file")
    # subprocess_args.append(temp_prompt_file_full_name)

    # 2. setup up a subprocess to manage a pipeline of prompt inputs that
    # trigger based on patterns matched by the AI responses

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Start the subprocess
    # logging.info(subprocess_args[0], subprocess_args[1:])
    child = pexpect.spawn(subprocess_args[0], subprocess_args[1:])
    # child = pexpect.spawn(chat_subprocess(subprocess_args))

    # Define the patterns you expect and the corresponding responses
    patterns = [
        # r"\d+\>\s*Input>\s*",  # index 1: User Input Prompt
        r"\d+\>\s*",  # index 1: User Input Prompt
        pexpect.TIMEOUT,  # index 2: Timeout
        pexpect.EOF,  # index 3: End of file
    ]

    # Function to read and print one character at a time
    def read_and_print_characters(child):
        while True:
            try:
                char = child.read_nonblocking(size=1, timeout=1)
                print(
                    char.decode("utf-8", errors="ignore"), end="", flush=True
                )
            except pexpect.exceptions.TIMEOUT:
                break
            except pexpect.exceptions.EOF:
                break

    # 3. Loop to handle different patterns as defined
    while True:
        # Read and print character stream
        try:
            char = child.read_nonblocking(size=1, timeout=1)
            print(char.decode("utf-8", errors="ignore"), end="", flush=True)
        except pexpect.exceptions.TIMEOUT:
            pass
        except pexpect.exceptions.EOF:
            break

        # Check for patterns
        while True:
            try:
                index = child.expect(patterns, timeout=10)
                if index == 0:
                    # Work the data through the prompt in chunks of 50 tuples
                    logging.info(
                        f"Total Count of Responses to Process: {len(open_responses)}"
                    )
                    for i in range(0, len(open_responses), 50):
                        logging.info(
                            f"Processing chunk {i + 1} to {i + 50} of {len(open_responses)}"
                        )
                        # time.sleep(5)
                        # get the chunk of responses
                        chunk = open_responses[i : i + 50]
                        # prepare the chunk as a string
                        chunk_str = str(chunk)
                        # send the chunk to the AI
                        child.sendline(chunk_str)
                        # print the subprocess interaction
                        read_and_print_characters(child)
                        # read the AI response
                        print(child.read().decode())
                    # Send "s" to the prompt to save the results
                    child.sendline("s")
                elif index == 1:
                    # Handle timeout
                    logging.warning("Subprocess timed out.")
                    break
                elif index == 2:
                    # Handle end of file
                    logging.info("Subprocess finished.")
                    break

                # Read and print characters after each interaction
                read_and_print_characters(child)

            except pexpect.exceptions.TIMEOUT:
                # If no pattern is matched, allow manual input
                user_input = input("Input> ")
                child.sendline(user_input)
                read_and_print_characters(child)
            except pexpect.exceptions.EOF:
                logging.error("Unexpected end of file.")
                break

    # Print the final output
    print(child.before.decode())

    # 3. call the chatgpt subprocess to analyze the responses, using the
    # prompt context provided as a global variable and taking the responses
    # chat_subprocess(subprocess_args)

    # 4. Continue to chat with the AI to refine the analysis and save the
    # results to a file for later use

    # cleanup the temporary prompt file
    # subprocess.run(
    #     ["rm", temp_prompt_file_full_name],
    #     check=True,
    # )


def main():
    """
    Main program
    """
    analyze_responses()


if __name__ == "__main__":
    main()
