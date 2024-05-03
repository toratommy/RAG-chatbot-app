import streamlit as st
import os
from src.utils import create_dir_if_not_exists, fetch_articles, load_documents_and_prepare_index, query_response, make_article_selections

# TO DO:
# sequential chat messages (check latest streamlit features)
# add memory
# let user select local folder OR cloud folder

def main():
    # set theme
    st._config.set_option(f'theme.base' ,"light" )
    st._config.set_option(f'theme.primaryColor',"#f63366")
    st._config.set_option(f'theme.backgroundColor',"#FFFFFF")
    st._config.set_option(f'theme.secondaryBackgroundColor', "#f0f2f6")
    st._config.set_option(f'theme.textColor',"#262730")

    st.set_page_config(page_title="Chat with Company Articles", page_icon="🦙", layout="centered", initial_sidebar_state="auto", menu_items=None)
    st.title("Company News Chat - Powered by LlamaIndex and OpenAI")

    create_dir_if_not_exists('data')

    # Sidebar for specifying parameters for fetching articles
    with st.sidebar:
        st.image('https://assets-global.website-files.com/659c81c957e77aeea1809418/65b2f184ee9f42f63bc2c651_TORA%20Logo%20(No%20Background)-p-800.png', width=225)
        st.title("Fetch Company Articles")
        company_name, start_date, end_date = make_article_selections()
        fetch_and_index_articles = st.button("Fetch and Index Articles")

    if fetch_and_index_articles:
        api_key = st.secrets["news_api"]
        company_folder = os.path.join('data', company_name.replace(" ", "_"))  # Normalize folder name
        create_dir_if_not_exists(company_folder)
        articles_fetched = fetch_articles(company_name, start_date, end_date, api_key, company_folder)
        if articles_fetched:
            st.success(f"Articles for {company_name} successfully fetched and saved in {company_folder}.")
            with st.spinner('Indexing documents...'):
                index = load_documents_and_prepare_index(company_folder)
            st.session_state['index'] = index
        else:
            st.error("Failed to fetch articles. Please check the company name or try again later.")

    # Main chat interface
    st.header("Interactive Chat")
    if 'index' in st.session_state:
        user_query = st.text_input("Enter your question:")
        if user_query:
            response = query_response(st.session_state['index'], user_query)
            st.text_area("Response", response, height=150)
    else:
        st.warning("No indexed data available for chat. Please fetch and prepare articles first.")

if __name__ == "__main__":
    main()
