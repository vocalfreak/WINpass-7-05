import pandas as pd
import numpy as np
import csv
import sys 
import io

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import T5Tokenizer, T5ForConditionalGeneration
from dateparser import parse 

def parse_event_details(output):
    parts = [part.strip() for part in output.split('-') if part.strip()]
    
    event = {
        "title": "",
        "date": "",
        "time": "",
        "location": ""
    }
    
    for part in parts:
        if part.lower().startswith("title is"):
            event["title"] = part[len("Title is"):].strip()
        elif part.lower().startswith("date is"):
            event["date"] = part[len("Date is"):].strip()
        elif part.lower().startswith("time is"):
            event["time"] = part[len("Time is"):].strip()
        elif part.lower().startswith("location is"):
            event["location"] = part[len("Location is"):].strip()
    
    return event

def logistic_regression(captions_train_path, test_set_path):
    df = pd.read_csv(captions_train_path)
    ds = pd.read_csv(test_set_path)

    X_train = df["caption"].values
    y_train = df["is_event"].values

    X_test = ds["caption"].values

    model = Pipeline(steps=[
    ('tfidf', TfidfVectorizer()),               
    ('clf', LogisticRegression(max_iter=1000))  
   ])

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    ds["predicted"] = y_pred
    ds.to_csv(test_set_path, index=False, encoding="utf-8-sig")


def get_title_date(test_set_path, output_path):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-large")
    model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-large")

    df = pd.read_csv(test_set_path, encoding='utf-8-sig')
    df = df[df["predicted"] == 1]  

    details = []
    for caption in df['caption']:

        print(caption)

        input_text = f"""
        You are a data extraction model tasked with extracting event details from an instagram event caption.
        Extract the following details from the caption:
        - Title 
        - Date 
        - Time 
        - Location

        do not include any other information like ticket price, bundle, entrance fee, artist, winner and categories, 
        or any other information that is not listed above. 
        Format the information as Json, follow the the order of the information, including the punctation and spacing:
        - Title: title
        - Date: date
        - Time: time
        - Location: location

        caption:
        {caption}
        """
        input_ids = tokenizer(input_text, return_tensors="pt").input_ids

        tensor_output = model.generate(
        input_ids,
        max_length=55,
        do_sample=False,
        )

        output = tokenizer.decode(tensor_output[0], skip_special_tokens=True)
        details.append(output)

    df["details"] = details
    df.to_csv(test_set_path, index=False, encoding="utf-8-sig")
                                  

# paths 
captions_train_path = r"C:\Users\chiam\Projects\WINpass-7-05\captions_trainingset.csv"
test_set_path = r"C:\Users\chiam\Projects\WINpass-7-05\instagram_posts.csv"

#logistic_regression(captions_train_path, test_set_path)
get_title_date(test_set_path, test_set_path)