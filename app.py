import streamlit as st
import os
from src.utils import *

# TO DO:

# implement trustworthly scores/source citing
# implement pathway for cloud connections
# let users select models (add placeholder for privately hosted)
# let agent render plots
# llamaParse with gpt4o
# toggle to give users access to outside info vs restrict to context


def main():
    # Set theme
    st._config.set_option(f'theme.base' ,"light" )
    st._config.set_option(f'theme.primaryColor',"#f63366")
    st._config.set_option(f'theme.backgroundColor',"#FFFFFF")
    st._config.set_option(f'theme.secondaryBackgroundColor', "#f0f2f6")
    st._config.set_option(f'theme.textColor',"#262730")
    # Setting up the Streamlit page configuration
    st.set_page_config(page_title="Chat with Your Knowledge Base", page_icon="🦙", layout="centered", initial_sidebar_state="auto")
    
    st.title("Personal Knowledge Base Agent")
    st.caption("RAG Powered by LlamaIndex and Pathway")
    st.divider()
    
    # Create a 'data' directory if it doesn't already exist
    create_dir_if_not_exists('data')
    
    # Sidebar for selecting the knowledge base source
    with st.sidebar:
        # Display logo in sidebar
        st.image('https://assets-global.website-files.com/659c81c957e77aeea1809418/65b2f184ee9f42f63bc2c651_TORA%20Logo%20(No%20Background)-p-800.png', width=225)
        st.header('About')
        st.caption('''Welcome to the Personal Knowledge Base Agent, powered by LlamaIndex and RAG (Retrieval-Augmented Generation) technology. 
                   This interactive platform allows you to seamlessly fetch, index, and query a vast array of documents, 
                   enhancing your ability to quickly access and utilize information. Whether you're integrating local data, 
                   connecting to a cloud document management system, or fetching public articles, 
                   our tool is designed to streamline your information management processes, 
                   making knowledge discovery as intuitive as having a conversation.''')
        st.divider()
        st.header("Select your Knowledge Base")
        knowledge_base_type = st.radio('Select knowledge base type', ['Document Repository','Database'])
        if knowledge_base_type == 'Document Repository':
            document_repository_type = make_document_repository_selections()
            
            # Handling public data fetching
            if document_repository_type == 'Fetch Public Documents':
                company_name, start_date, end_date, file_path = make_public_document_selections()
                fetch_documents = st.button("Fetch and Load Documents")
                if fetch_documents:
                    api_key = st.secrets["news_api"]
                    create_dir_if_not_exists(file_path)
                    fetched_status = fetch_public_documents(company_name, start_date, end_date, api_key, file_path)
                    if fetched_status:
                        st.session_state.num_docs = count_files_in_directory(file_path)
                        st.success(f"{st.session_state.num_docs} documents for {company_name} successfully fetched and saved in {file_path}.")
                        st.session_state['path_saved'] = True
                    else:
                        st.error("Failed to fetch articles. Please check the company name or try again later.")
            else:
                # Handle local or cloud directory path input
                st.session_state.file_path = enter_path()
                st.session_state['path_saved'] = st.button('Save File Path')
                st.session_state.num_docs = 0 # initialize num docs
                if st.session_state['path_saved']:
                    st.session_state.num_docs = count_files_in_directory(st.session_state.file_path)
                    st.success(f'Path has been sucessfully saved. {st.session_state.num_docs} documents are available in {st.session_state.file_path}')
        elif knowledge_base_type == 'Database':
            database_type = make_database_selections()
            st.session_state['database_connected'] = st.button('Connect Database')


    # Indexing control
    if ('file_path' in st.session_state) & (knowledge_base_type == 'Document Repository'):
        st.subheader('Index Your Knowledge Base')
        st.caption('Indexing is the process of organizing a vast amount of text data in a way that allows the RAG system to quickly find the most relevant pieces of information for a given query.')
        st.markdown(f'Current Knowledge Base Directory: `{st.session_state.file_path}`')
        if st.session_state.num_docs > 0:
            index_documents = st.button('Index Knowledge Base',)
            if index_documents:
                with st.spinner('Indexing documents...'):
                    index, files_df = load_documents_and_prepare_index(st.session_state.file_path)
                    st.session_state['index'] = index
                    st.session_state.num_docs = count_files_in_directory(st.session_state.file_path)
                    st.success(f"{st.session_state.num_docs} documents successfully indexed. Start a chat with your knowledge base agent below!")
                    st.dataframe(files_df)
                    # Reset chat upon new indexing
                    st.session_state.messages = [{"role": "assistant", "content": f"Hello! I am your personal knowledge base agent. Ask me anything about your knowledge base. I currently have access to {st.session_state.num_docs} indexed files in the following directory: `{st.session_state.file_path}`"}]
        else:
            st.warning('No documents available for index. Please enter a valid file path using the left control panel.')

    # Main chat interface
    st.subheader("Interactive Chat")
    if knowledge_base_type == 'Document Repository':
        if 'index' in st.session_state:
            user_input = st.chat_input("Your question:")
            if user_input:
                if "messages" not in st.session_state:
                    st.session_state.messages = []
                st.session_state.messages.append({"role": "user", "content": format_message(user_input)})
                response = query_response(st.session_state['index'], user_input).response
                st.session_state.messages.append({"role": "assistant", "content": format_message(response)})

            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        else:
            st.warning("No indexed data available for chat. Please use the left control panel to connect a document repository and click the button above to index your documents.")
    else:
        st.warning("No database available for chat. Please use the left control panel to connect a database.")
if __name__ == "__main__":
    main()