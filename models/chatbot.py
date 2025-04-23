import os
from typing import List, Dict, Any, Tuple
import google.generativeai as genai
from dotenv import load_dotenv
from .document_processor import DocumentProcessor

# Load environment variables
load_dotenv()

# Configure Google Generative AI with API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class ComplianceChatbot:
    def __init__(self, document_processor: DocumentProcessor):
        self.document_processor = document_processor
        self.model_name = "gemini-1.5-pro"
        self.chat_history = []
    
    def generate_response(self, query: str, k: int = 5) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Generate a response to the user's query using RAG approach with the Gemini API
        Returns the response and the sources used
        """
        # Search for relevant documents
        search_results = self.document_processor.search_documents(query, k=k)
        print(f"Search results: {search_results}")
        
        if not search_results:
            return ("I'm sorry, I couldn't find any relevant information in the compliance documents. "
                    "Please consider uploading relevant PDFs if they're not already in our system."), []
        
        # Extract document content and sources
        contexts = []
        sources = []
        
        for doc, score in search_results:
            contexts.append(doc.page_content)
            sources.append({
                "source": doc.metadata.get("source", "Unknown"),
                "score": score,
                "doc_id": doc.metadata.get("doc_id", "Unknown")
            })
        
        # Combine contexts
        context_text = "\n\n".join(contexts)
        
        # Create system prompt
        system_instructions = """
        You are a compliance assistant for a financial institution. Your role is to provide accurate 
        information based on the company's compliance documents. Answer the user's query using ONLY the 
        information provided in the context. If the answer is not in the provided context, say that you 
        don't have enough information from the compliance documents to answer. Do not make up answers.
        Always cite the specific document source you used for your answer.
        """
        
        # Create user prompt with context
        full_prompt = f"""
        {system_instructions}
        
        Context information from compliance documents:
        {context_text}
        
        User question: {query}
        
        Please provide a response based only on the context information provided.
        """
        
        try:
            # Generate response using Gemini API
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(full_prompt)
            response_text = response.text
            print(f"Response: {response_text}")
            
            # Update chat history
            self.chat_history.append({"role": "user", "content": query})
            self.chat_history.append({"role": "assistant", "content": response_text})
            
            # Limit chat history to last 10 exchanges
            if len(self.chat_history) > 20:
                self.chat_history = self.chat_history[-20:]
            
            return response_text, sources
        except Exception as e:
            error_message = f"Error generating response: {str(e)}"
            print(error_message)
            return "I'm sorry, I encountered an error while generating a response. Please try again later.", []
    
    def reset_chat_history(self):
        """Reset the chat history"""
        self.chat_history = []
