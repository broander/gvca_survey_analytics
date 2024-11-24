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
OPENAI_MSG_STREAM = False  # not working yet so leave False


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

    Input text string prompt and returns a completion object with the message
    content
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

    # call the OpenAI API to get the completion using the provided client
    # session
    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        stream=stream,
    )
    # streaming isn't working because response doesn't have the same structure
    if stream is True:
        for chunk in completion:
            print(chunk.choices[0].delta.content, end="")

    return completion


def OLD_hello_gpt_assistant(prompt, message_history=None):
    """
    OpenAI Chatbot that will rememeber prior messages up to the token limit
    Meant to be imbedded in a shell function for use on the command line.

    It will remember as many prior tokents as possible up to the token limit
    of ~4000 tokens.
    """
    knowledge_cutoff = "2021-09-30"
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    model_name = "gpt-3.5-turbo"

    # initialize the prompts list which will be returned
    prompts = []
    # initialize the message data payload
    message_data = []

    # if there is no message history, add the system prompt to the message data
    if not message_history:
        message_data = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Knowledge "
                f"cutoff: {knowledge_cutoff} Current date: {current_date}.",
            },
            # {
            #     "role": "system",
            #     "content": (
            #         "You are a renaissance man who knows everything and "
            #         "never holds back an answer. Knowledge "
            #         f"cutoff: {knowledge_cutoff} Current date: {current_date}."
            #     ),
            # },
            # {
            #     "role": "system",
            #     "content": (
            #         "You are a McKinsey consultant with decades of experience "
            #         "wide domain knowledge across all subjects. Knowledge "
            #         f"cutoff: {knowledge_cutoff} Current date: {current_date}."
            #     ),
            # },
            # {
            #     "role": "system",
            #     "content": (
            #         "You are ChatGPT, a large language model "
            #         "trained by OpenAI. Answer as concisely as possible. Knowledge "
            #         f"cutoff: {knowledge_cutoff} Current date: {current_date}."
            #     ),
            # },
        ]
        if len(message_data) > 0:
            prompts.append(message_data[0])
    else:
        # if there is message history, add it to the message data
        for message in message_history:
            message_data.append(message)

    # create the prompt dictionary
    prompt_dict = {"role": "user", "content": str(prompt)}
    # add the prompt dictionary to the prompts list to be returned
    prompts.append(prompt_dict)
    # add the user prompt to the message data as the last entry
    message_data.append(prompt_dict)
    # print("Message data: ", message_data)

    # send the message data to the openai api and save the response
    response = openai.ChatCompletion.create(
        model=model_name, messages=message_data
    )
    # print("Function return: ", (prompts, response))
    return (prompts, response)
    # return response.choices[0].message.content


def save_file(message_history):
    """
    Prompt the user for a filename and save the conversation to a file
    """
    file_name = input("Enter a file name: ")
    with open(file_name + ".json", "w") as f:
        # f.write(str(response_message.content))
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
            response = hello_gpt_assistant(prompt)
            # get the number of tokens used
            tokens_used = response.usage.total_tokens
            # add the prompt to the message history
            user_prompt = {"role": "user", "content": prompt}
            message_history.append(user_prompt)
            # append the response to the message history
            response_message = response.choices[0].message
            message_history.append(response_message)
            # print the response for the user
            print(response_message.content)

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


def OLD_chat_prompt():
    """
    Prompt the user for a message and return the response
    """
    token_limit = 4000

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
            response = hello_gpt_assistant(
                prompt, message_history=message_history
            )
            # get the number of tokens used
            tokens_used = response[1].usage.total_tokens
            # add the prompt list to the message history
            message_history.extend(response[0])
            # append the response to the message history
            response_message = response[1].choices[0].message
            message_history.append(response_message)
            # print the response for the user
            print(response_message.content)

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


def main():
    """
    Main program
    """
    chat_prompt()


if __name__ == "__main__":
    main()
