import requests
import os
import streamlit as st
from datetime import datetime, timedelta
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index.llms.openai import OpenAI
import openai

@st.experimental_fragment
def make_article_selections():
    company_name = st.text_input("Enter a company name:")
    today = datetime.now()
    one_month_ago = today - timedelta(days=30)
    start_date = st.date_input("Start Date", value=one_month_ago, min_value=one_month_ago, max_value=today)
    end_date = st.date_input("End Date", value=today, min_value=one_month_ago, max_value=today)
    return company_name, start_date, end_date

#@st.cache_resource(show_spinner=True)
def set_openai_key():
    openai.api_key = st.secrets["openai_api_key"]

@st.cache_data(show_spinner=False)
def fetch_articles(company_name, start_date, end_date, api_key, save_path='data'):
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    url = f"https://newsapi.org/v2/everything?q={company_name}&from={start_date_str}&to={end_date_str}&sortBy=publishedAt&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json()['articles']
        for i, article in enumerate(articles):
            content = article.get('content')
            if content:
                file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{i}.txt"
                file_path = os.path.join(save_path, file_name)
                with open(file_path, 'w') as file:
                    file.write(content)
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

#@st.cache_data(ttl=86400)  # Cache for one day
def load_documents_and_prepare_index(directory):
    reader = SimpleDirectoryReader(directory)
    documents = reader.load_data()

    llm = get_model_and_tokenizer()

    service_context = ServiceContext.from_defaults(chunk_size=1024, llm=llm)
    index = VectorStoreIndex.from_documents(documents, service_context=service_context)

    return index

def query_response(index, query):
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    return response
