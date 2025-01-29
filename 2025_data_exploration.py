# %%
import pandas as pd

df = pd.read_csv(
    "/workspaces/gvca_survey_analytics/2024 Parent Satisfaction Survey.csv"
)
pd.set_option("display.max_columns", None)
display(df.head())


# %%
