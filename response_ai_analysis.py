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

# Output Files Location
OUTPUT_FILES_LOCATION = "./response_analysis_logs/"
# Output File Name global variable based on current date and time
OUTPUT_FILE_NAME = datetime.datetime.now().strftime(
    "%Y-%m-%d_%H-%M-%S" + "_ai_response_analysis"
)

# load environment variables from .env file
INPUT_FILEPATH, DATABASE_SCHEMA, DATABASE_CONNECTION_STRING = load_env_vars()

# database query to get the open response data
# DATABASE_QUERY = "SELECT respondent_id, response FROM question_open_responses;"
DATABASE_QUERY = "SELECT response FROM question_open_responses;"

# setup the OpenAI API client
# initialize the global variable that will point to the OpenAI API client
OPENAI_CLIENT = OpenAI()


def create_new_openai_client():
    """
    Create a new OpenAI API client and attach to the global variable
    """
    global OPENAI_CLIENT
    OPENAI_CLIENT = OpenAI()
    OPENAI_CLIENT.api_key = os.getenv("OPENAI_API_KEY")


# specify model settings and initialize
# see models here: https://platform.openai.com/docs/models
# OPENAI_MODEL_NAME = "gpt-4o"  # standard flagship model
# OPENAI_MODEL_NAME = "gpt-4o-mini"   # like gpt-3.5-turbo but faster and
# OPENAI_MODEL_NAME = "o1-preview"  # most advanced, better at complex tasks
OPENAI_MODEL_NAME = "o1-mini"  # most advanced, better at complex tasks
OPENAI_MSG_STREAM = True
create_new_openai_client()


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
    prompt_context=OPENAI_PROMPT_CONTEXT,
    message_history=[],
    client=OPENAI_CLIENT,
    model_name=OPENAI_MODEL_NAME,
    stream=OPENAI_MSG_STREAM,
):
    """
    OpenAI Chatbot.  See API Reference here:
    https://platform.openai.com/docs/api-reference/chat/create

    Input text string prompt and returns a tuple of the role, content, and
    token usage

    Parameters:
        prompt: str: the message prompt to send to the chatbot
        client: OpenAI: the OpenAI API client object
        model_name: str: the OpenAI model name to use
        prompt_context: str: the prompt context to use
        stream: bool: whether to stream the response
        message_history: list: the message history list
    """

    # define RateLimitError exception
    class RateLimitError(Exception):
        def __init__(self, message):
            self.message = message
            super().__init__(self.message)

    # define the messages list based on the model name, as o1 doesn't support
    # the system prompt
    messages = []
    if model_name in ["o1-preview", "o1-mini"]:
        if prompt_context:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_context},
                    ],
                },
            ]
        messages.extend(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                    ],
                },
            ]
        )
    else:
        if prompt_context:
            messages = [
                {"role": "system", "content": prompt_context},
            ]
        messages.extend(
            [
                {"role": "user", "content": prompt},
            ]
        )
    # add the message history to the messages list
    # messages.extend(message_history)
    conversation = message_history + messages
    # breakpoint()

    # if stream is True, set stream_options, otherwise set to None
    if stream is True:
        stream_options = {"include_usage": True}
    else:
        stream_options = None

    # call the OpenAI API to get the completion using the provided client
    # session
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=conversation,
            stream=stream,
            stream_options=stream_options,
        )
    except RateLimitError as e:
        print(e)
        print("Rate limit exceeded.  Please try again later.")
        return
    except Exception as e:
        print(e)
        print("An error occurred.  Please try again later.")
        return

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


def save_file(
    message_history,
    file_name=OUTPUT_FILE_NAME,
    file_location=OUTPUT_FILES_LOCATION,
):
    """
    Prompt the user for a filename and save the conversation to a file
    """
    if not file_name:
        file_name = input("Enter a file name: ")
        file_name = file_location + file_name
    with open(file_location + file_name + ".json", "w") as f:
        json_object = json.dumps(message_history, indent=4)
        f.write(json_object)
    print(f"Conversation saved to {file_location} {file_name}.json")


def chat_prompt(initial_prompt=""):
    """
    Prompt the user for a message and return the response
    """
    token_limit = 124000
    # initialize message history storage list
    message_history = []
    # initialize prompt variable
    prompt_count = 1
    # initialize tokens used variable
    tokens_used = 0
    # initialize the prompt variable
    prompt = ""

    # initial prompt message

    # initial prompt message
    # if no initial prompt provided as argument
    if not initial_prompt:
        print("Provide a prompt for ChatGPT, or enter 'help' or '?' for help.")
        prompt = input(f"{prompt_count}> ")
    # if initial prompt provided as argument
    else:
        prompt = initial_prompt

    # main loop: loop until the user quits or the token limit is reached
    while prompt != "q" and tokens_used <= token_limit:
        # user help
        if prompt in ["help", "?"]:
            print(
                "Type 'q' to quit, 's' to save the conversation to a file, "
                "or type a message to continue the conversation."
            )

        # skip the assistant function if the user uses a menu option or the
        # token limit is reached
        if prompt not in ["help", "?", "s", "", "t"]:
            # if first prompt, send the prompt context text
            if prompt_count == 1:
                prompt_context = OPENAI_PROMPT_CONTEXT
            else:
                prompt_context = ""
            # call the assistant function with the current prompt response
            # and also all previous message history so ai has chat context
            role, content, usage = gpt_assistant(
                prompt,
                prompt_context=prompt_context,
                message_history=message_history,
            )
            # add prompt context to the message history
            if prompt_context:
                prompt_context_message = {
                    "role": "user",
                    "content": prompt_context,
                }
                message_history.append(prompt_context_message)
            # add the prompt to the message history
            user_prompt = {"role": "user", "content": prompt}
            message_history.append(user_prompt)
            # get the number of tokens used
            tokens_used = usage.total_tokens
            # add the response to the message history
            response_message = {
                "role": role,
                "content": content,
            }
            message_history.append(response_message)
            # increment the prompt count
            prompt_count += 1
            # breakpoint()

        # subsequent prompt messages after first one
        prompt = input(f"{prompt_count}> ")

        # save the conversation to a text file as json
        if prompt == "s":
            save_file(message_history)

        # print the token usage
        if prompt == "t":
            print(f"Tokens used: {tokens_used} of max {token_limit}")

    # when token limit is reached, prompt the user to save the conversation or
    # quit
    while tokens_used > token_limit and prompt != "q":
        print(
            f"Token limit of {token_limit} reached. "
            "Press 's' to save your conversation or 'q' to quit."
        )
        prompt = input(f"{prompt_count}> ")
        if prompt == "s":
            save_file(message_history)

    # when quiting, prompt the user to save the conversation or continue
    # quiting
    while tokens_used <= token_limit and prompt == "q":
        print("Quitting, type 's' to save the conversation or ENTER to quit.")
        prompt = input(f"{prompt_count}> ")
        if prompt == "s":
            save_file(message_history)
        print("Goodbye!")

    if prompt == "q":
        OPENAI_CLIENT.close()


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
):
    """
    Analyze the open responses using the OpenAI API
    """

    # get the open responses from the database
    open_responses = query_database(database_connection_string, query, schema)

    # Prepare the responses for analysis
    prompt = "Here are the survey responses to analyze:\n"
    for response in open_responses:
        prompt += f"- {response[0]}\n"

    # call the chat_prompt function to analyze the responses
    # uses the prompt context provided as a global variable and silently
    # takes the responses as the first user prompt input before continuing
    # the chat session so you can provie futher direction to the AI
    chat_prompt(prompt)


def main():
    """
    Main program
    """
    analyze_responses()


if __name__ == "__main__":
    main()
