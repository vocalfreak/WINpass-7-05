import pandas as pd
import numpy as np
import csv
import sys 
import io
import re
import logging 
import requests
import time 

from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import T5Tokenizer, T5ForConditionalGeneration

huggingface_token = "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"

def call_huggingfaceapi(prompt, model="google/flan-t5-large", max_length=55):

    api_url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {huggingface_token}"}

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": max_length,
            "do_sample": False,
            "temperature": 0.1
        }
    }


    response = requests.post(api_url, headers=headers, json=payload, timeout=30)

    if response.status_code == 503: 
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        time.sleep(20)
    elif response.status_code == 200:
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0].get('output', '')  
        return result.get('output', '')
    
    return ""

def logistic_regression(captions_train_path, test_set_path):
    df = pd.read_csv(captions_train_path)
    ds = pd.read_csv(test_set_path)

    X_train = df["caption"].fillna("").values  
    y_train = df["is_event"].values
    
    X_test = ds["caption"].fillna("").values   
    
    model = Pipeline(steps=[
        ('tfidf', TfidfVectorizer()),              
        ('clf', LogisticRegression(max_iter=1000))  
    ])
    
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    
    ds["predicted"] = y_pred
    ds.to_csv(test_set_path, index=False, encoding="utf-8-sig")


def get_title_date(test_set_path):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-large")
    model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-large")

    df = pd.read_csv(test_set_path, encoding='utf-8-sig')
    df = df[df["predicted"] == 1]  

    details = []
    for caption in df['caption']:

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
        output = call_huggingfaceapi(input_text)
        details.append(output)
        time.sleep(1)

    df["details"] = details
    df.to_csv(test_set_path, index=False, encoding="utf-8-sig")

def clean_output_text(text):

    text = text.strip()
    
    text = re.sub(r'\s+', ' ', text)
    
    text = re.sub(r'[\-=]+\s*', '- ', text)
    
    return text

def extract_event_data(output_text):

    output_text = clean_output_text(output_text)
    
    result = {
        'title': '',
        'date': '',
        'time': '',
        'location': ''
    }
    

    title_patterns = [
        r'Title:?\s*["""]?([^-"]+?)["""]?(?=\s*-|\s*$)', 
        r'Title\s*[=:]?\s*(.+?)(?=\s*-|\s*$)', 
        r'^- Title:?\s*(.+?)(?=\s*-|\s*$)' 
    ]
    
    for pattern in title_patterns:
        title_match = re.search(pattern, output_text)
        if title_match:
            text = title_match.group(1).strip()
            result['title'] = ' '.join(text.split()[:10])
            break
    
    date_patterns = [
        r'Date:?\s*([^-]+?)(?=\s*-|\s*$)',  
        r'Date\s*[=:]?\s*(.+?)(?=\s*-|\s*$)',  
        r'- Date:?\s*(.+?)(?=\s*-|\s*$)',  
        r'\b(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b', 
        r'\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b'  
    ]

    for pattern in date_patterns:
        date_match = re.search(pattern, output_text)
        if date_match:
            result['date'] = date_match.group(1).strip()
            break
    
    time_patterns = [
        r'Time:?\s*([^-]+?)(?=\s*-|\s*$)', 
        r'Time\s*[=:]?\s*(.+?)(?=\s*-|\s*$)',  
        r'- Time:?\s*(.+?)(?=\s*-|\s*$)',  
        r'\b(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\s*[-–]\s*\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\b' 
    ]
    
    for pattern in time_patterns:
        time_match = re.search(pattern, output_text)
        if time_match:
            result['time'] = time_match.group(1).strip()
            break
    
    location_patterns = [
        r'Location:?\s*([^-]+?)(?=\s*-|\s*$)',  
        r'Location\s*[=:]?\s*(.+?)(?=\s*-|\s*$)',  
        r'- Location:?\s*(.+?)(?=\s*-|\s*$)', 
        r'Venue:?\s*([^-]+?)(?=\s*-|\s*$)',  
        r'Venue\s*[=:]?\s*(.+?)(?=\s*-|\s*$)'  
    ]
    
    for pattern in location_patterns:
        location_match = re.search(pattern, output_text)
        if location_match:
            result['location'] = location_match.group(1).strip()
            break
    
    return result

def get_events_data(test_set_path):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    df = pd.read_csv(test_set_path, encoding='utf-8-sig')
    details = df["details"]
    
    titles = []
    dates = []
    times = []
    locations = []

    for detail in details:
        result = extract_event_data(detail)
        titles.append(result["title"])
        dates.append(result["date"])
        times.append(result["time"])
        locations.append(result["location"])

    df["title"] = titles
    df["date"] = dates
    df["time"] = times
    df["location"] = locations

    df.to_csv(test_set_path, index=False, encoding="utf-8-sig")


# paths 
# captions_train_path = r"C:\Users\chiam\Projects\WINpass-7-05\captions_trainingset.csv"
# test_set_path = r"C:\Users\chiam\Projects\WINpass-7-05\instagram_posts.csv"

captions_train_path = "captions_trainingset.csv"
test_set_path = "instagram_posts.csv"

#logistic_regression(captions_train_path, test_set_path)
#get_title_date(test_set_path, test_set_path)
#get_events_data(test_set_path)
