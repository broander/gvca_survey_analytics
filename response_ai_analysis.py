# access chatgpt from the cli
#
# learn more about model tuning here:
# https://platform.openai.com/docs/api-reference/chat/create
#
# relies on the OPENAI_API_KEY environment variable being set in your
# terminal with a valid OpenAI API key
# this is set via github codespaces secret management, if not set make sure
# it is shared with this repository in codespaces settings

import datetime
import json
import os
from pprint import pprint

from openai import OpenAI
from sqlalchemy import create_engine, text

try:
    from .utilities import load_env_vars
except:
    from utilities import load_env_vars

# see models here: https://platform.openai.com/docs/models
# OPENAI_MODEL_NAME = "gpt-4o"  # standard flagship model
# OPENAI_MODEL_NAME = "gpt-4o-mini"   # like gpt-3.5-turbo but faster and
OPENAI_MODEL_NAME = "o1-preview"  # most advanced, better at complex tasks

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
    """

OPENAI_MSG_STREAM = False
OPENAI_CLIENT = OpenAI()

# load environment variables from .env file
INPUT_FILEPATH, DATABASE_SCHEMA, DATABASE_CONNECTION_STRING = load_env_vars()

# database query to get the open response data
DATABASE_QUERY = "SELECT response FROM responses;"


def create_new_openai_client():
    """
    Create a new OpenAI API client
    """
    global OPENAI_CLIENT
    OPENAI_CLIENT = OpenAI()
    OPENAI_CLIENT.api_key = os.getenv("OPENAI_API_KEY")


def set_openai_model_name(model_name="gpt-4o"):
    """
    Set the model name for the OpenAI API
    """
    global OPENAI_MODEL_NAME
    OPENAI_MODEL_NAME = model_name


def set_prompt_content(prompt_context=OPENAI_PROMPT_CONTEXT):
    """
    Set the prompt context for the OpenAI API
    """
    global OPENAI_PROMPT_CONTEXT
    OPENAI_PROMPT_CONTEXT = prompt_context


def set_msg_stream(stream=OPENAI_MSG_STREAM):
    """
    Set the message stream setting for the OpenAI API
    """
    global OPENAI_MSG_STREAM
    OPENAI_MSG_STREAM = stream


def gpt_assistant(
    prompt,
    client=OPENAI_CLIENT,
    model_name=OPENAI_MODEL_NAME,
    prompt_context=OPENAI_PROMPT_CONTEXT,
    stream=OPENAI_MSG_STREAM,
    message_history=None,
):
    """
    OpenAI Chatbot.  See API Reference here:
    https://platform.openai.com/docs/api-reference/chat/create

    Input text string prompt and returns a tuple of the role, content, and
    token usage
    """
    # define the messages list based on the model name, as o1 doesn't support
    # the system prompt
    if model_name in ["o1-preview", "o1-mini"]:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                ],
            },
        ]
    else:
        messages = [
            {"role": "system", "content": prompt_context},
            {"role": "user", "content": prompt},
        ]

    # if stream is True, set stream_options, otherwise set to None
    if stream is True:
        stream_options = {"include_usage": True}
    else:
        stream_options = None

    # call the OpenAI API to get the completion using the provided client
    # session

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=stream,
        stream_options=stream_options,
    )

    role = ""
    message_content = ""
    usage = None
    # breakpoint()

    # if stream is True, process and save stream data and print stream content
    if stream is True:
        print("\n")
        for chunk in response:
            try:
                if chunk.choices[0].delta.content is not None:
                    delta = chunk.choices[0].delta.content
                    content = delta
                    print(content, end="", flush=True)
                    message_content += content
            except:
                pass
            finally:
                try:
                    if chunk.choices[0].delta.role is not None:
                        role = chunk.choices[0].delta.role
                except:
                    pass
            try:
                if chunk.usage is not None:
                    usage = chunk.usage
            except:
                pass
            # breakpoint()
        print("\n")
    elif stream is False:
        role = response.choices[0].message.role
        message_content = response.choices[0].message.content
        usage = response.usage
        print("\n" + message_content + "\n")
        # breakpoint()
    # breakpoint()
    return role, message_content, usage


def save_file(message_history):
    """
    Prompt the user for a filename and save the conversation to a file
    """
    file_name = input("Enter a file name: ")
    with open(file_name + ".json", "w") as f:
        # f.write(str(response_message.content))
        # breakpoint()
        json_object = json.dumps(message_history, indent=4)
        f.write(json_object)


def query_database(database_connection_string, query, database_schema=None):
            """
    Query the target database connection and schema using the provided query
    string
    """
    engine = create_engine(database_connection_string)
    with engine.connect() as connection:
        if database_schema is not None:
            command = f"SET SCHEMA '{database_schema}';"
            connection.execute(text(command)
        result = connection.execute(text(query))
        return result.fetchall()


def analyze_responses(
    database_connection_string=DATABASE_CONNECTION_STRING,
    query=DATABASE_QUERY,
    schema=DATABASE_SCHEMA,
):
    """
    Analyze the open responses using the OpenAI API
    """
    # get the open responses from the database
    open_responses = query_database(
        database_connection_string, query, schema
    )

    # create a new OpenAI client
    create_new_openai_client()

    # Prepare the responses for analysis
    prompt = "Here are the survey responses to analyze:\n"
    for response in open_responses:
        prompt += f"- {response[0]}\n"

    gpt_assistant(prompt)


def main():
    """
    Main program
    """
    create_new_openai_client()
    analyze_responses()


if __name__ == "__main__":
    main()
