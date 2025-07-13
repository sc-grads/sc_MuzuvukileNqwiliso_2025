import spacy
from fuzzywuzzy import process
import re

nlp = spacy.load("en_core_web_sm")

def extract_entities(query):
    doc = nlp(query)
    entities = {
        "names": [],
        "dates": [],
        "keywords": []
    }
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            entities["names"].append(ent.text)
        elif ent.label_ == "DATE":
            entities["dates"].append(ent.text)
    
    # Expanded keywords for better context
    keywords = [
        "timesheet", "employee", "client", "project", "leave", 
        "total hours", "billable", "non-billable", "hour", "day", "week", "month", "year",
        "request", "status", "type"
    ]
    for keyword in keywords:
        if keyword in query.lower():
            entities["keywords"].append(keyword)
            
    return entities

def process_query(query, schema_metadata):
    """
    Processes the natural language query to extract key entities.
    This function no longer modifies the query itself.
    """
    return extract_entities(query)
