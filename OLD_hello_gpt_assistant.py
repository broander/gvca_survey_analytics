# access chatgpt from the cli
#
# learn more about model tuning here:
# https://platform.openai.com/docs/api-reference/chat/create
#
# relies on the OPENAI_API_KEY environment variable being set in your
# terminal with a valid OpenAI API key

import datetime
import json
from pprint import pprint

import openai


def hello_gpt_assistant(prompt, message_history=None):
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
