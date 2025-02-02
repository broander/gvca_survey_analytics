"""
Access chatgpt from the cli and analyze open response data
"""

import re
import signal
import subprocess
import sys
import threading

import pexpect
from sqlalchemy import create_engine, text

from hello_gpt_assistant import (chat_subprocess, load_message_history,
                                 save_prompt_file)
from utilities import load_env_vars

# Path to the hello_gpt_assistant.py script to call as a subprocess
AI_SCRIPT_PATH = "./hello_gpt_assistant.py"

# Specify the desired model to be used for the OpenAI API
OPENAI_MODEL_NAME = "gpt-4o"


def run_subprocess():
    """
    Spawn the subprocess and monitor its output.
    When a pre-defined pattern is matched, send the corresponding input.
    If a pattern's input is None, prompt the user for manual input.
    """
    # Define the patterns and the responses
    # Adjust the keys (regex) and values as needed.
    # For auto-trigger strings, provide an automatic response.
    # For manual input, set the value to None.
    patterns = {
        r"1>\s*": "What year did hank aaron break the record?",
        r"2>\s*": "How old was he?",
        r"3>\s*": "What year did he enter the hall of fame?",
        # catch-all prompt ending with a number and ">" for manual input
        r"\d+\>\s*$": None,
    }

    # Create a list of regex patterns in the order you want them matched.
    regex_list = list(patterns.keys())

    # Spawn the subprocess using the same Python interpreter.
    # Buffer output will be written to sys.stdout so you can see progress in real time.
    child = pexpect.spawn(sys.executable, [AI_SCRIPT_PATH], encoding="utf-8")
    # child.logfile = sys.stdout   # show input and output
    child.logfile_read = sys.stdout  # show only output to avoid duplication

    while True:
        try:
            # Wait for one of the patterns to appear
            index = child.expect(regex_list, timeout=60)
            triggered_pattern = regex_list[index]
            response = patterns[triggered_pattern]

            # Inform which pattern was triggered
            print(f"\n[Pattern matched: {triggered_pattern}]")

            if response is not None:
                # print(f"Automatically sending: {response}\n")
                print(f"***Automatically sending***:\n")
                child.sendline(response)
            else:
                # No auto-response defined: get manual input from user
                # Requires accurate r"foobar": None pattern to be defined
                manual_input = input("Input> ")
                child.sendline(manual_input + "\n")
        except pexpect.EOF:
            print("Subprocess ended (EOF received).")
            break
        except pexpect.TIMEOUT:
            # Continue waiting if nothing matched in the given timeout
            continue


def main():
    """
    Main program
    """
    run_subprocess()


if __name__ == "__main__":
    main()
