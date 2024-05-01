import requests
import json
import os

def fetch_articles(company_name, api_key, save_path='data'):
    url = f"https://newsapi.org/v2/everything?q={company_name}&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        articles = response.json()['articles']
        for i, article in enumerate(articles):
            content = article['content']
            if content:
                file_path = os.path.join(save_path, f"{company_name}_{i}.txt")
                with open(file_path, 'w') as file:
                    file.write(content)
        return True
    else:
        return False

def create_dir_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
