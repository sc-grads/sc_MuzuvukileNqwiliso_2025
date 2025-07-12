import re
import spacy
from fuzzywuzzy import process

def process_query(nl_query, schema_metadata):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(nl_query)
    
    keywords = [token.text.lower() for token in doc if token.pos_ in ["NOUN", "PROPN"]]
    if any(term in nl_query.lower() for term in ["in", "for", "during"]):
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME"]:
                keywords.append(ent.text.lower())
    
    table_names = [
        re.search(r"Table: Timesheet\.(\w+)", meta).group(1).lower()
        for meta in schema_metadata
        if re.search(r"Table: Timesheet\.(\w+)", meta)
    ]
    
    column_names = []
    for meta in schema_metadata:
        columns = re.search(r"Columns: (.+)", meta)
        if columns:
            column_names.extend([
                col.split("(")[0].strip().lower()
                for col in columns.group(1).split(", ")
            ])
    
    matched_tables = []
    matched_columns = []
    for keyword in keywords:
        table_match = process.extractOne(keyword, table_names, score_cutoff=80)
        if table_match:
            matched_tables.append(table_match[0])
        column_match = process.extractOne(keyword, column_names, score_cutoff=80)
        if column_match:
            matched_columns.append(column_match[0])
    
    enhanced_query = f"{nl_query} (Relevant tables: {', '.join(matched_tables) if matched_tables else 'infer from schema'}; Relevant columns: {', '.join(matched_columns) if matched_columns else 'infer from schema'})"
    return enhanced_query
