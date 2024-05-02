import streamlit as st
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM
import torch
import os
from llama_index import VectorStoreIndex, ServiceContext, Document, SimpleDirectoryReader
from src.utils import fetch_articles, create_dir_if_not_exists

st.set_page_config(page_title="RAG Chat with Company Articles", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)
st.title("Company News Chat - Powered by LlamaIndex and Hugging Face Llama-3")

create_dir_if_not_exists('data')

# Summarization model setup
tokenizer_sum = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
model_sum = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")

tokenizer = AutoTokenizer.from_pretrained("allenai/llama3")
model = AutoModelForCausalLM.from_pretrained("allenai/llama3")

@st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner("Indexing documents... This may take a moment."):
        reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
        docs = reader.load_data()
        service_context = ServiceContext.from_defaults(llm=model)
        index = VectorStoreIndex.from_documents(docs, service_context=service_context)
        return index

index = load_data()

if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Ask me anything about the companies you're interested in. Just enter a company name below to fetch and engage with the latest articles."}
    ]

company_name = st.text_input("Enter a company name to fetch relevant news articles:")
if st.button("Fetch Articles"):
    api_key = st.secrets["news_api"]
    if fetch_articles(company_name, api_key):
        st.success(f"News articles for {company_name} successfully fetched and indexed.")
        index = load_data()  # Reload the index with new data
        # Generate and display summaries
        docs_to_summarize = [doc.content for doc in index.documents.values()]
        summaries = [model_sum.generate(tokenizer_sum.encode(doc, return_tensors="pt", truncation=True, max_length=512)) for doc in docs_to_summarize[:5]]  # Limit to first 5 documents for simplicity
        summarized_texts = [tokenizer_sum.decode(g[0], skip_special_tokens=True) for g in summaries]
        summary_section = "\n\n".join(summarized_texts)
        st.subheader("Summaries of fetched articles:")
        st.write(summary_section)
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
            query_vector = index.encode_query(prompt)
            relevant_docs = index.retrieve_documents(query_vector, top_k=3)
            combined_context = " ".join(doc.content for doc in relevant_docs)
            inputs = tokenizer.encode(prompt + tokenizer.eos_token + combined_context, return_tensors="pt")
            outputs = model.generate(inputs, max_length=1024)
            response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            st.write(response_text)
            message = {"role": "assistant", "content": response_text}
            st.session_state.messages.append(message)
