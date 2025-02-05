"""
Access chatgpt from the cli

learn more about model tuning here:
https://platform.openai.com/docs/api-reference/chat/create

simple api example and explanation here:
https://community.openai.com/t/build-your-own-ai-assistant-in-10-lines-of-code-python/83210

relies on the OPENAI_API_KEY environment variable being set in your
terminal with a valid OpenAI API key
this is set via github codespaces secret management, if not set make sure
it is shared with this repository in codespaces settings
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

from openai import OpenAI

# specify the desired model to be used for the OpenAI API
# see models here: https://platform.openai.com/docs/models
OPENAI_MODEL_NAME = "o1-preview"

# specify the OpenAI message stream default
OPENAI_MSG_STREAM = True

# specify the initial prompt context for the OpenAI API
# prompt engineering best practices:
# https://help.openai.com/en/articles/6654000-best-practices-for-prompt-engineering-with-the-openai-api
# prompt context for the open response analysis task
OPENAI_PROMPT_CONTEXT = """
    You are a helpful assistant.
    """

# specify an optional initial prompt to run after the context
INITIAL_PROMPT = ""

# specify optional prompt history file location and name to load
HISTORY_FILE = ""

# specify model settings and initialize
# see models here: https://platform.openai.com/docs/models
OPENAI_MODELS_DICT = {
    "gpt-4o": {
        "name": "gpt-4o",
        "max_tokens": 128000,
        "reasoning_effort": None,
    },
    "gpt-4o-mini": {
        "name": "gpt-4o-mini",
        "max_tokens": 128000,
        "reasoning_effort": None,
    },
    "o1-preview": {
        "name": "o1-preview",
        "max_tokens": 128000,
        "reasoning_effort": None,
    },
    "o1": {
        "name": "o1",
        "max_tokens": 200000,
        "reasoning_effort": "medium",
    },
    "o1-mini": {
        "name": "o1-mini",
        "max_tokens": 128000,
        "reasoning_effort": None,
    },
    "o3-mini": {
        "name": "o3-mini",
        "max_tokens": 200000,
        "reasoning_effort": "medium",
    },
}

# Output Files Location
OUTPUT_FILES_LOCATION = "."
# OUTPUT_FILES_LOCATION = "."
# Output File Name global variable based on current date and time
OUTPUT_FILE_NAME = ""
# OUTPUT_FILE_NAME = datetime.datetime.now().strftime(
#     "%Y-%m-%d_%H-%M-%S" + "ai_response_history"
# )


def create_new_openai_client():
    """
    Create a new OpenAI API client and return the object
    """
    openai_client = OpenAI()
    openai_client.api_key = os.getenv("OPENAI_API_KEY")
    return openai_client


# TODO: refactor to fix message history dangerous default value as list
def gpt_assistant(
    prompt,
    prompt_context="",
    message_history=[],
    client=create_new_openai_client(),
    model_name="gpt-4o",
    stream=True,
    reasoning_effort=None,
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
    if model_name in ["gpt-4o", "gpt-4o-mini"]:
        if prompt_context:
            messages = [
                {"role": "system", "content": prompt_context},
            ]
        messages.extend(
            [
                {"role": "user", "content": prompt},
            ]
        )
    else:
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
        if reasoning_effort:
            response = client.chat.completions.create(
                model=model_name,
                messages=conversation,
                stream=stream,
                stream_options=stream_options,
                reasoning_effort=reasoning_effort,
            )
        else:
            response = client.chat.completions.create(
                model=model_name,
                messages=conversation,
                stream=stream,
                stream_options=stream_options,
            )
            # breakpoint()
    except RateLimitError as e:
        print(e)
        print("Rate limit exceeded.  Please try again later.")
        # breakpoint()
        return
    except Exception as e:
        print(e)
        print("An error occurred.  Please try again later.")
        raise e

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


# TODO: refactor to fix file location behavior so can accept fully qualified
# file names or just file name and file location, and if no file location
# assume current directory
def save_file(
    message_history,
    file_name="",
    file_location=".",
):
    """
    Prompt the user for a location and filename and save the conversation to a file
    """
    file_saved = False
    while not file_saved:
        # breakpoint()
        # make minor corrections to file location and check quality
        if "~" in file_location:
            file_location = os.path.expanduser(file_location)
        if file_location and not file_location.endswith("/"):
            file_location += "/"
        if not os.path.exists(file_location):
            print("Location directory does not exist.  Please try again.")
            file_location = ""
        # if file location and file name, ready to save
        if file_location and file_name:
            file_saved = True
        # prompt user for file name if not provided
        while not file_name:
            file_name = input(
                "Enter a file name, or 't' for a standard timestamp-based name: "
            )
            if file_name == "t":
                file_name = datetime.datetime.now().strftime(
                    "%Y-%m-%d_%H-%M-%S" + "_ai_response_history"
                )
        # prompt user for file location if not provided or was invalid and set
        # to empty string
        while not file_location:
            file_location = input(
                "Enter a file location, or '.' for current directory: "
            )
    # save file
    with open(file_location + file_name + ".json", "w") as f:
        json_object = json.dumps(message_history, indent=4)
        f.write(json_object)
    print(f"Conversation saved to {file_location} {file_name}.json")


def load_message_history(file_name, file_location=""):
    """
    Load long prompt string from a file.  File should contain just the content
    desired for the prompt string.
    Input:
        file_name: str: the file name to load
            file name should either be full path or file name with path provided
        file_location: str: the file location to look for the file
    Output: message_history list: the message history
    """
    file_opened = False
    while not file_opened:
        while not file_name:
            print("No file name provided. Please try again.")
            file_name = input("Enter a file name: ")
        try:
            with open(file_location + file_name, "r") as f:
                message_history = json.load(f)
            file_opened = True
        except FileNotFoundError:
            print("History file not found. Please try again.")
            file_name = ""
    return message_history


# TODO: refactor to fix file location behavior so can accept fully qualified
# file names or just file name and file location, and if no file location
# assume current directory
def save_prompt_file(prompt, file_name="", file_location="."):
    """
    Save the prompt to a file
    """
    file_saved = False
    while not file_saved:
        # make minor corrections to file location and check quality
        if "~" in file_location or file_location == ".":
            file_location = os.path.expanduser(file_location)
        if file_location and not file_location.endswith("/"):
            file_location += "/"
        if not os.path.exists(file_location):
            print("Location directory does not exist.  Please try again.")
            file_location = ""
        # if file location and file name, ready to save
        if file_location and file_name:
            file_saved = True
        # prompt user for file name if not provided
        while not file_name:
            file_name = input("No file name provided. Please try again.")
        # prompt user for file location if not provided or was invalid and set to
        # empty string
        while not file_location:
            file_location = input(
                "Enter a file location, or '.' for current directory: "
            )
    # save file
    # print first 100 characters of prompt
    # print(f"Prompt: {prompt[:100]}")
    with open(file_location + file_name + ".txt", "w") as f:
        f.write(prompt)
    # current_directory = os.getcwd()
    # print(f"Current directory is: {current_directory}")
    print(f"Prompt file saved to {file_location} {file_name}.txt")


def open_prompt_file(file_name, file_location=""):
    """
    Open the prompt file and return the prompt text.
    Load long prompt string from a file.  File should contain just the content
    desired for the prompt string.
    Input:
        file_name: str: the file name to load
            file name should either be full path or file name with path provided
        file_location: str: the file location to look for the file
    Output: prompt: str: the prompt
    """
    file_opened = False
    while not file_opened:
        while not file_name:
            print("No file name provided. Please try again.")
            file_name = input("Enter a file name: ")
        try:
            print(f"Opening prompt file {file_location} {file_name}")
            with open(file_location + file_name, "r") as f:
                prompt_string = f.read()
            file_opened = True
        except FileNotFoundError:
            print("Prompt file not found. Please try again.")
            file_name = ""
    return prompt_string


# TODO: refactor to fix dangerous default value of model dict
def chat_prompt(
    model=OPENAI_MODELS_DICT["gpt-4o"],
    stream=True,
    context="",
    initial_prompt="",
    message_history=[],
    file="",
    location=".",
):
    """
    Prompt the user for a message and return the response
    """
    # set the token limit
    token_limit = model["max_tokens"]
    # initialize message history storage list
    # message_history = []
    # initialize prompt variable
    prompt_count = 1
    # initialize tokens used variable
    tokens_used = 0
    # initialize the prompt variable
    prompt = ""
    # initialize the openai client
    openai_client = create_new_openai_client()

    # if message history provided as argument, print old messages
    if message_history:
        print("Message history provided.  Printing message history.")
        for message in message_history:
            if message["role"] == "user":
                print(f"\n{prompt_count}> {message['content']} \n")
            elif message["role"] == "assistant":
                print(f"\n {message['content']} \n")
                # iterate prompt count for every reply by assistant
                prompt_count += 1
    # now done with message history if provided, prompt user for input
    if message_history or not initial_prompt:
        print("Provide a prompt for ChatGPT, or enter 'help' or '?' for help.")
        prompt = input(f"{prompt_count}> ")
    # if initial prompt provided as argument
    else:
        prompt = initial_prompt
        print("Initial prompt provided.  Silently processing, please standby.")

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
            if prompt_count == 1 and not message_history:
                prompt_context = context
            else:
                prompt_context = ""
            # call the assistant function with the current prompt response
            # and also all previous message history so ai has chat context
            role, content, usage = gpt_assistant(
                prompt,
                prompt_context=prompt_context,
                message_history=message_history,
                model_name=model["name"],
                client=openai_client,
                stream=stream,
                reasoning_effort=model["reasoning_effort"],
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
            save_file(message_history, file, location)

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
            save_file(message_history, file, location)

    # when quiting, prompt the user to save the conversation or continue
    # quiting
    while tokens_used <= token_limit and prompt == "q":
        print("Quitting, type 's' to save the conversation or ENTER to quit.")
        prompt = input(f"{prompt_count}> ")
        if prompt == "s":
            save_file(message_history, file, location)
        print("Goodbye!")

    # close the OpenAI client session
    if prompt == "q":
        openai_client.close()


def argument_parser():
    """
    Parse the command line arguments
    """
    # parse the command line arguments
    parser = argparse.ArgumentParser(description="OpenAI Chatbot")

    parser.add_argument(
        "-m",
        "--model",
        "--model_name",
        type=str,
        help="OpenAI model name; default is gpt-4o",
        default=OPENAI_MODEL_NAME,
    )
    parser.add_argument(
        "-c",
        "--context",
        type=str,
        help="Prompt context; default is simple assistant",
        default=OPENAI_PROMPT_CONTEXT,
    )
    parser.add_argument(
        "-s",
        "--stream",
        type=bool,
        help="Stream the response; default is True",
        default=OPENAI_MSG_STREAM,
    )
    parser.add_argument(
        "-r",
        "--history",
        "--history_file",
        "--recall",
        type=str,
        help="Message history file name; default is no history file",
        default=HISTORY_FILE,
    )
    parser.add_argument(
        "-f",
        "--file",
        "--output_file",
        type=str,
        help="Output file name; default is to prompt user",
        default=OUTPUT_FILE_NAME,
    )
    parser.add_argument(
        "-l",
        "--location",
        "--output_location",
        type=str,
        help="Output files location; default is to prompt user",
        default=OUTPUT_FILES_LOCATION,
    )
    parser.add_argument(
        "-p",
        "--prompt",
        type=str,
        help="Initial prompt to execute after context is set; default is empty",
        default="",
    ),
    parser.add_argument(
        "-pf",
        "--prompt_file",
        type=str,
        help="Prompt file name to load; default is empty; file should be text only",
        default="",
    )

    args = parser.parse_args()
    return args


def main(**kwargs):
    """
    Main function to process parameters and call the chat prompt
    """

    # process keyword arguments
    model = kwargs.get("model", OPENAI_MODELS_DICT["gpt-4o"])
    context = kwargs.get("context", "")
    stream = kwargs.get("stream", True)
    history_file = kwargs.get("history", "")
    file = kwargs.get("file", "")
    location = kwargs.get("location", ".")
    prompt = kwargs.get("prompt", "")
    prompt_file = kwargs.get("prompt_file", "")

    # load the message history from a file if provided
    message_history = []
    if history_file:
        message_history = load_message_history(history_file)

    # load the prompt from a file if provided
    if prompt_file:
        prompt = open_prompt_file(prompt_file)

    # call the chat prompt
    chat_prompt(
        model=model,
        stream=stream,
        context=context,
        initial_prompt=prompt,
        message_history=message_history,
        file=file,
        location=location,
    )


if __name__ == "__main__":
    # parse the command line arguments
    args = argument_parser()
    main(
        model=OPENAI_MODELS_DICT[args.model],
        context=args.context,
        stream=args.stream,
        history=args.history,
        file=args.file,
        location=args.location,
        prompt=args.prompt,
        prompt_file=args.prompt_file,
    )


def chat_subprocess(args_list):
    """
    Call the hello_gpt_assistant.py script as a subprocess
    Input: args_list - list of arguments to pass to the subprocess
    Assumed to be the same arguments as the hello_gpt_assistant.py script
    """
    # call hello_gpt_assistant as subprocess with the arguments to analyze the
    # responses.  This allows this script to provide inputs to the user input
    # prompts and receive the AI responses as output

    # define the pattern to match the subprocess prompt
    # should match patterh of "1>", "2>", "3>", etc. like in the
    # hello_gpt_assistant.py
    subprocess_prompt_pattern = re.compile(r"\d+\> ")

    with subprocess.Popen(
        args_list,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
        text=True,
    ) as process:
        buffer = ""

        # Read the output in real-time
        while True:
            char = process.stdout.read(1)
            if not char:
                # EOF reached
                break

            # add the character to the buffer
            buffer += char

            # print the char so we see what's happening
            sys.stdout.write(char)
            sys.stdout.flush()

            # check if hte line matches the subprocess prompt pattern
            match = subprocess_prompt_pattern.search(buffer)
            if match:
                # Prompt the user for input back to the subprocess
                user_input = input("\nInput> ")
                process.stdin.write(user_input + "\n")
                process.stdin.flush()

                # Clear the buffer
                buffer = ""

        # Check for any errors
        stderr = process.stderr.read()
        if stderr:
            print("Errors from subprocess:")
            print(stderr.decode())

        # Optionally wait for the process to end and get exit code
        # return_code = process.wait()
        # print(f"Subprocess finished with return code {return_code}")
