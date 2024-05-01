import streamlit as st
import openai
from llama_index.llms.openai import OpenAI
from src.utils import fetch_articles, create_dir_if_not_exists
try:
    from llama_index import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader
except ImportError:
    from llama_index.core import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader

st.set_page_config(page_title="RAG Chat with Company Articles", page_icon="📄", layout="centered", initial_sidebar_state="auto", menu_items=None)
openai.api_key = st.secrets.openai_key
st.title("Company News Chat - Powered by RAG and News API")

create_dir_if_not_exists('data')

if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Ask me anything about the companies you're interested in. Just enter a company name below to fetch and engage with the latest articles."}
    ]

@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Preparing documents... Please wait as we index the latest articles."):
        reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
        docs = reader.load_data()
        service_context = ServiceContext.from_defaults(llm=OpenAI(model="gpt-3.5-turbo", temperature=0.5, system_prompt='''You are an expert on the company's news articles. Provide detailed responses based on the content of these documents, and ensure all answers are factual and derived directly from the source material.'''))
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index

index = load_data()

if "chat_engine" not in st.session_state.keys():
    st.session_state.chat_engine = index.as_chat_engine(chat_mode="condense_question", verbose=True)

company_name = st.text_input("Enter a company name to fetch relevant news articles:")
if st.button("Fetch Articles"):
    api_key = st.secrets["news_api"]
    if fetch_articles(company_name, api_key):
        st.success(f"News articles for {company_name} successfully fetched and indexed.")
        index = load_data()  # Reload the index with new data
    else:
        st.error("Failed to fetch articles. Please check the company name or try again later.")

if prompt := st.chat_input("Your question about the company"):
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Generating response..."):
            response = st.session_state.chat_engine.chat(prompt)
            st.write(response.response)
            message = {"role": "assistant", "content": response.response}
            st.session_state.messages.append(message)
