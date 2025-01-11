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
from pprint import pprint

from openai import OpenAI

# initialize the OpenAI API client
OPENAI_CLIENT = OpenAI()

# see models here: https://platform.openai.com/docs/models
# OPENAI_MODEL_NAME = "gpt-4o"  # standard flagship model
# OPENAI_MODEL_NAME = "gpt-4o-mini"   # like gpt-3.5-turbo but faster and
OPENAI_MODEL_NAME = "o1-preview"  # most advanced, better at complex tasks
OPENAI_PROMPT_CONTEXT = "You are a helpful assistant."
OPENAI_MSG_STREAM = True  # not working yet so leave False


def create_new_openai_client():
    """
    Create a new OpenAI API client
    """
    global OPENAI_CLIENT
    OPENAI_CLIENT = OpenAI()


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


def hello_gpt_assistant(
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


def chat_prompt():
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

    # initial prompt message
    if not message_history:
        print("Provide a prompt for ChatGPT, or enter 'help' or '?' for help.")
        prompt = input(f"{prompt_count}> ")

    # loop until the user quits or the token limit is reached
    while prompt != "q" and tokens_used <= token_limit:
        # user help
        if prompt in ["help", "?"]:
            print(
                "Type 'q' to quit, 's' to save the conversation to a file, "
                "or type a message to continue the conversation."
            )

        # skip the assistant function if the user uses a menu option or the
        # token limit is reached
        if prompt not in ["help", "?", "s", ""]:
            # increment the prompt count
            prompt_count += 1
            # call the assistant function
            # response = hello_gpt_assistant(prompt)
            role, content, usage = hello_gpt_assistant(prompt)
            # get the number of tokens used
            # tokens_used = response.usage.total_tokens
            tokens_used = usage.total_tokens
            # add the prompt to the message history
            user_prompt = {"role": "user", "content": prompt}
            message_history.append(user_prompt)
            # append the response to the message history
            # response_message = {
            #     "role": response.choices[0].message.role,
            #     "content": response.choices[0].message.content,
            # }
            response_message = {
                "role": role,
                "content": content,
            }
            message_history.append(response_message)
            # breakpoint()

        # subsequent prompt messages after first one
        prompt = input(f"{prompt_count}> ")

        # save the conversation to a text file as json
        if prompt == "s":
            save_file(message_history)

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


def main():
    """
    Main program
    """
    chat_prompt()


if __name__ == "__main__":
    main()
