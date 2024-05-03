from transformers import BertModel, BertTokenizer
import torch

class DocumentEmbedder:
    def __init__(self, model_name='bert-base-uncased'):
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name)
        self.model.eval()  # Set the model to evaluation mode

    def get_embeddings(self, text):
        # Tokenize the input text and convert to input IDs
        encoded_input = self.tokenizer(text, padding=True, truncation=True, return_tensors='pt')
        # Compute token embeddings
        with torch.no_grad():
            outputs = self.model(**encoded_input)
        # Take the mean of the token embeddings to get sentence embeddings
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings

# Example usage
# embedder = DocumentEmbedder()
# text = "Here is some sample text to encode"
# embeddings = embedder.get_embeddings(text)
# print(embeddings)
