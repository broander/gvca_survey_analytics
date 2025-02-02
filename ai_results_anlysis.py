# %% [markdown]
# # Import Libraries
# Import the necessary libraries, specifically pandas and json.

# %%
# Import Libraries
import pandas as pd
import json

# %% [markdown]
# # Load JSON Data
# Load the JSON file containing the survey responses using Python's built-in open() function or other methods.

# %%
# Load JSON Data
with open(
    "/workspaces/gvca_survey_analytics/response_analysis_logs/2025-02-02_02-22-47_ai_response_analysis.json",
    "r",
) as file:
    data = json.load(file)

# Extract relevant information and create a DataFrame
responses = []
for entry in data:
    if entry["role"] == "user":
        responses.append(entry["content"])

# Create DataFrame
df = pd.DataFrame(responses, columns=["response"])

# Display the DataFrame
df.head()

# %% [markdown]
# # Parse and Convert Data
# Parse the JSON data and convert it into a pandas DataFrame making sure that each survey response is a different row.

# %%
# Parse and Convert Data

# Extract relevant information and create a DataFrame
responses = []
for entry in data:
    if entry["role"] == "user":
        # Split the responses by new line and filter out empty strings
        split_responses = [
            resp.strip()
            for resp in entry["content"].split("\n")
            if resp.strip()
        ]
        responses.extend(split_responses)

# Create DataFrame
df = pd.DataFrame(responses, columns=["response"])

# Display the DataFrame
df.head()

# %% [markdown]
# # Display the DataFrame
# Display the resulting DataFrame using the .head() or print() commands to verify the correct loading of data.

# %%
# Display the DataFrame
df.head()

# %%
# Create a new DataFrame with user prompts and AI responses
user_prompts = []
ai_responses = []

# Iterate through the data assuming a user entry is immediately followed by an AI response
for i in range(len(data) - 1):
    if data[i]["role"] == "user" and data[i + 1]["role"] == "assistant":
        user_prompts.append(data[i]["content"])
        ai_responses.append(data[i + 1]["content"])

# Create DataFrame only if there are matching prompt-response pairs
if user_prompts and ai_responses:
    df_prompts_responses = pd.DataFrame(
        {"prompt": user_prompts, "ai_response": ai_responses}
    )
    display(df_prompts_responses.head())
else:
    print("No matching prompt-response pairs found.")

# %%
import json


def format_json_response(response):
    stripped = response.strip()
    if stripped.startswith("```json"):
        # Split into lines and remove the opening and closing markdown markers if present
        lines = stripped.splitlines()
        # Remove the first line (opening marker)
        if lines and lines[0].strip().startswith("```json"):
            lines = lines[1:]
        # Remove the last line if it is the closing marker
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        json_str = "\n".join(lines).strip()
        try:
            json_obj = json.loads(json_str)
            formatted_json = json.dumps(json_obj, indent=4)
            return formatted_json
        except Exception as e:
            # If JSON parsing fails, leave the response unchanged
            return response
    else:
        return response


# Apply the cleanup function to the ai_response column
df_prompts_responses["ai_response"] = df_prompts_responses[
    "ai_response"
].apply(format_json_response)
display(df_prompts_responses.head())

# %%
import json
import re

# Extract the JSON string from the ai_response column of row 2
json_str_row_2 = df_prompts_responses.loc[2, "ai_response"]


def extract_json_and_text(s):
    s = s.strip()
    json_start = s.find("{")
    json_end = s.rfind("}")

    if json_start != -1 and json_end != -1:
        json_str = s[json_start : json_end + 1]
        additional_text = s[:json_start].strip() + s[json_end + 1 :].strip()
        return json_str, additional_text
    else:
        return None, s


def fix_json_string(s):
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        s_fixed = s.replace("'", '"')
        s_fixed = s_fixed.rstrip(",")
        s_fixed = s_fixed.replace("}{", "},{")
        s_fixed = re.sub(r'(?<!")(\b\w+\b)(?!"):', r'"\1":', s_fixed)
        s_fixed = re.sub(r",\s*([}\]])", r"\1", s_fixed)
        attempts = 0
        while attempts < 3:
            try:
                return json.loads(s_fixed)
            except json.JSONDecodeError as e_inner:
                error_message = str(e_inner)
                if "Expecting ',' delimiter" in error_message:
                    pos = e_inner.pos
                    if pos < len(s_fixed) and s_fixed[pos] not in [
                        ",",
                        "}",
                        "]",
                    ]:
                        s_fixed = s_fixed[:pos] + "," + s_fixed[pos:]
                    else:
                        break
                    attempts += 1
                else:
                    break
        try:
            return json.loads(s_fixed)
        except json.JSONDecodeError as e_final:
            print(f"Error decoding JSON: {e_final}")
            return None


# Extract JSON and additional text
json_str, additional_text = extract_json_and_text(json_str_row_2)

if json_str:
    json_data_row_2 = fix_json_string(json_str)
    if json_data_row_2:
        df_json_row_2 = pd.DataFrame(json_data_row_2)
        display(df_json_row_2.head())
    else:
        print("The JSON string could not be fixed.")
else:
    print("No valid JSON found in the string.")

if additional_text:
    print("Additional text found:")
    print(additional_text)
else:
    print("No additional text found.")
    # Display the additional text found
    if additional_text:
        print("Additional text found:")
        print(additional_text)
    else:
        print("No additional text found.")

# %%
# Extract the JSON string from the ai_response column of row 0
json_str = df_prompts_responses.loc[0, "ai_response"]

# Load the JSON string into a dictionary
json_data = json.loads(json_str)

# Convert the dictionary into a DataFrame
df_json = pd.DataFrame(json_data)

# Display the new DataFrame
df_json.head()

# %%
df_json["categories"] = df_json["categories"].apply(
    lambda cats: ", ".join(cats) if isinstance(cats, list) else cats
)
display(df_json.head())


# %%
from sqlalchemy import create_engine, text

from utilities import load_env_vars

INPUT_FILEPATH, DATABASE_SCHEMA, DATABASE_CONNECTION_STRING = load_env_vars()

# Create a SQLAlchemy engine using the connection string defined previously
engine = create_engine(DATABASE_CONNECTION_STRING)

# Load the entire DataFrame (df_json from cell 11) into a new table in the sac_survey_2025 schema.
# Using the desired table name 'open_response_ai_categorization'
df_json.to_sql(
    name="open_response_ai_categorization",
    con=engine,
    schema="sac_survey_2025",
    if_exists="replace",  # change to 'append' if you want to add to an existing table
    index=False,
)

print(
    "The full DataFrame has been successfully loaded into the sac_survey_2025.open_response_ai_categorization table."
)
