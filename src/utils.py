import requests
import os
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.llms.openai import OpenAI
import openai
import sqlite3


def format_message(content):
    # Escape dollar signs to prevent Markdown formatting issues
    return content.replace("$", "\$")

def make_database_selections():
    database_type = st.selectbox('Select database',['PostgreSQL','Amazon Redshift','Amason RDS','MySQL','Snowflake'])
    return database_type

def make_document_repository_selections():
    document_repository_type = st.selectbox('Select document repository type',['Local Directory','SharePoint','Google Drive','S3 Bucket','Fetch Public Documents'])
    return document_repository_type

def enter_path():
    file_path = st.text_input('Enter file path', placeholder='/Users/YourName/Documents')
    return file_path

def make_public_document_selections():
    company_name = st.text_input("Enter a company name")
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)
    start_date = st.date_input("Start date", value=one_month_ago, min_value=one_month_ago, max_value=today)
    end_date = st.date_input("End date", value=today, min_value=one_month_ago, max_value=today)
    file_path = st.text_input('Enter file path to store fetched documents', value=os.path.join('data', company_name.replace(" ", "_")) )
    return company_name, start_date, end_date, file_path

@st.cache_resource(show_spinner=True)
def set_openai_key():
    openai.api_key = st.secrets["openai_api_key"]

def count_files_in_directory(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        count += len(files)
    return count

@st.cache_data(show_spinner=False)
def fetch_public_documents(company_name, start_date, end_date, api_key, save_path='data'):
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    url = f"https://newsapi.org/v2/everything?q={company_name}&from={start_date_str}&to={end_date_str}&sortBy=publishedAt&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        documents = response.json()['articles']
        for i, article in enumerate(documents):
            title = article.get('title', 'No Title Provided')
            publish_date = article.get('publishedAt', 'No Date Provided').split('T')[0]  # Extract just the date part
            publisher = article['source'].get('name', 'Unknown Publisher').replace(' ', '_').replace('/', '_')  # Replace spaces and slashes to avoid issues in filenames
            content = article.get('content')
            if content:
                # Format the document with title and date before the content
                document_content = f"Title: {title}\nDate: {publish_date}\n\n{content}"
                # Format the file name to include the publisher name and date
                file_name = f"{publisher}_{publish_date}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}.txt"
                file_path = os.path.join(save_path, file_name)
                with open(file_path, 'w') as file:
                    file.write(document_content)
        return True
    else:
        return False

def create_dir_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_model_and_tokenizer():
    set_openai_key()  # Ensure the API key is set before using the OpenAI model
    # Proceed to use the OpenAI model
    llm = OpenAI(api_key=openai.api_key, model="gpt-3.5-turbo")
    return llm

def get_meta(file_path):
    """ Custom function to extract metadata from files """
    return {
        "file_path": file_path,
        "last_modified": os.path.getmtime(file_path)
    }

@st.cache_data(ttl=86400)  # Cache for one day
def load_documents_and_prepare_index(directory):
    llm = get_model_and_tokenizer()
    service_context = ServiceContext.from_defaults(chunk_size=1024, llm=llm)

    # Use SimpleDirectoryReader with custom metadata extraction
    reader = SimpleDirectoryReader(directory, recursive=True, file_metadata=get_meta)
    documents = reader.load_data()

    # Create the index from the collected documents
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)

    # Generate data for DataFrame about the documents, using metadata
    data = []
    for doc in documents:
        doc_path = doc.metadata['file_path']
        last_modified = doc.metadata['last_modified']
        data.append({
            "file_name": os.path.basename(doc_path),
            "folder_name": os.path.basename(os.path.dirname(doc_path)),
            "file_type": os.path.splitext(doc_path)[1][1:],  # Remove the dot from extension
            "last_updated_date": datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S'),
            "indexed_status": "Yes"
        })

    df = pd.DataFrame(data)
    return index, df

def query_response(index, query):
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    return response

# Initialize database and create sample data


def text_to_sql_query(query_engine, text):
    try:
        # Generate SQL query from the input text using llamaindex
        response = query_engine.query(text)
        return response.query_str, response
    except Exception as e:
        return str(e), None

def execute_sql_query(engine, text, query):
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query))
            data = result.fetchall()
            columns = result.keys()
        return data, columns
    except Exception as e:
        return str(e), []