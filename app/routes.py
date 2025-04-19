from utils.csv_utils import import_csv_init
import csv

# Paths
df_path = r"C:\Users\chiam\Downloads\Test_George.csv"
db_path = "winpass.db"

with open(df_path, newline='', encoding='utf-8') as df:
    df = csv.DictReader(df)

import_csv_init(df, db_path)