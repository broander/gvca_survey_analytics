# %%
import pandas as pd

df = pd.read_csv(
    "/workspaces/gvca_survey_analytics/2024 Parent Satisfaction Survey.csv"
)
pd.set_option("display.max_columns", None)
display(df.head())

# %%
for i in range(1, len(new_headers)):
    if new_headers[i][0].startswith("Unnamed"):
        new_headers[i] = (
            new_headers[i - 1][0],
            new_headers[i][1],
            f"Column {i}",
        )
    else:
        new_headers[i] = (new_headers[i][0], new_headers[i][1], f"Column {i}")

# Convert the updated headers to a DataFrame
headers_df = pd.DataFrame(
    new_headers, columns=["First Value", "Second Value", "Column Number"]
)

# Update the DataFrame with new headers
df.columns = pd.MultiIndex.from_tuples(new_headers)

# Display the updated DataFrame
display(df.head())

# %%
# Update headers using list comprehension
new_headers = [
    (
        (new_headers[i - 1][0], new_headers[i][1], f"Column {i}")
        if new_headers[i][0].startswith("Unnamed")
        or new_headers[i][0].startswith("Responses pertinent")
        else (new_headers[i][0], new_headers[i][1], f"Column {i}")
    )
    for i in range(len(new_headers))
]

# Convert the updated headers to a DataFrame
headers_df = pd.DataFrame(
    new_headers, columns=["First Value", "Second Value", "Column Number"]
)

# Update the DataFrame with new headers
df.columns = pd.MultiIndex.from_tuples(new_headers)

# Display the updated DataFrame
display(df.head())
