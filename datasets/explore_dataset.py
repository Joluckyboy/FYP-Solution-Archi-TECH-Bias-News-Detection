import pandas as pd
import numpy as np

# Read CSV in chunks to get full info
df_info = pd.read_csv('./Kaggle News Articles For Political Bias Classification.csv', nrows=20000)

print('Dataset Info:')
print(f'Columns: {df_info.columns.tolist()}')
print(f'\nUnique Sites: {df_info["site"].nunique()}')
print(f'Sample Sites:\n{df_info["site"].value_counts().head(20)}')
print(f'\nUnique Topics: {df_info["topic"].nunique()}')
print(f'Topics:\n{df_info["topic"].value_counts()}')
print(f'\nUnique Bias Types: {df_info["bias"].nunique()}')
print(f'Bias Types:\n{df_info["bias"].value_counts()}')
print(f'\nDate Range: {df_info["date"].min()} to {df_info["date"].max()}')
print(f'\nData Types:\n{df_info.dtypes}')
print(f'\nMissing Values:\n{df_info.isnull().sum()}')
