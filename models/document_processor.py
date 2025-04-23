import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.base import Embeddings
from langchain_community.vectorstores import FAISS
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Generative AI with API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class GeminiEmbeddings(Embeddings):
    """
    Custom class for Gemini embeddings
    """
    def __init__(self, model_name="models/embedding-001"):
        self.model_name = model_name

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using Gemini API"""
        embeddings = []
        try:
            for text in texts:
                embedding = genai.embed_content(
                    model=self.model_name,
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(embedding['embedding'])
            return embeddings
        except Exception as e:
            print(f"Error embedding documents: {e}")
            return [[0.0] * 768] * len(texts)  # Return empty embeddings in case of failure

    def embed_query(self, text: str) -> List[float]:
        """Embed a query text using Gemini API"""
        try:
            embedding = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_query"
            )
            return embedding['embedding']
        except Exception as e:
            print(f"Error embedding query: {e}")
            return [0.0] * 768  # Return empty embedding in case of failure

class DocumentProcessor:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.pdf_dir = os.path.join(data_dir, "pdfs")
        self.vector_dir = os.path.join(data_dir, "vector_store")
        self.metadata_file = os.path.join(data_dir, "document_metadata.json")
        self.embeddings = GeminiEmbeddings()
        
        # Create directories if they don't exist
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.vector_dir, exist_ok=True)
        
        # Load metadata if exists
        self.metadata = self._load_metadata()
        
        # Initialize vector store
        self.vector_store = self._load_or_create_vector_store()
        
        # Ensure vector store has actual documents (not just placeholder)
        self._ensure_vector_store_populated()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load document metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
                return {"documents": {}}
        return {"documents": {}}
    
    def _save_metadata(self):
        """Save document metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
        except Exception as e:
            print(f"Error saving metadata: {e}")
    
    def _load_or_create_vector_store(self):
        """Load existing vector store or create a new one"""
        if os.path.exists(os.path.join(self.vector_dir, "index.faiss")):
            try:
                return FAISS.load_local(self.vector_dir, self.embeddings)
            except Exception as e:
                print(f"Error loading vector store: {e}")
                # If loading fails, create a new one with a placeholder text
                return FAISS.from_texts(["placeholder content"], self.embeddings, 
                                        metadatas=[{"source": "placeholder", "doc_id": "placeholder"}])
        else:
            # Create a vector store with placeholder content to avoid "content must not be empty" error
            return FAISS.from_texts(["placeholder content"], self.embeddings,
                                   metadatas=[{"source": "placeholder", "doc_id": "placeholder"}])
    
    def _ensure_vector_store_populated(self):
        """Ensure the vector store contains all documents from metadata"""
        # Check if we need to rebuild the vector store
        need_rebuild = False
        
        # If no documents in metadata but PDFs exist, or only placeholder content exists
        if (not self.metadata["documents"] and os.listdir(self.pdf_dir)) or len(self.vector_store.docstore._dict) <= 1:
            need_rebuild = True
        
        # If documents in metadata but not in vector store
        doc_count = len(self.metadata["documents"])
        if doc_count > 0 and len(self.vector_store.docstore._dict) < doc_count + 1:  # +1 for placeholder
            need_rebuild = True
            
        # If rebuild needed, do it
        if need_rebuild:
            print("Rebuilding vector store with existing documents...")
            self._rebuild_vector_store()
            print(f"Vector store rebuilt with {len(self.vector_store.docstore._dict)} documents")
    
    def process_pdf(self, pdf_file, filename=None) -> bool:
        """
        Process a PDF file: extract text, split into chunks, embed and store
        """
        try:
            # Generate a unique ID for the document
            doc_id = str(uuid.uuid4())
            
            # If filename not provided, generate one
            if not filename:
                filename = f"{doc_id}.pdf"
            else:
                # Ensure filename has .pdf extension
                if not filename.lower().endswith('.pdf'):
                    filename += '.pdf'
            
            # Save PDF file
            pdf_path = os.path.join(self.pdf_dir, filename)
            with open(pdf_path, "wb") as f:
                f.write(pdf_file.read())
            
            # Extract text from PDF
            pdf_reader = PdfReader(pdf_path)
            raw_text = ""
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    raw_text += text
            
            if not raw_text.strip():
                print(f"No text could be extracted from {filename}")
                return False
            
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                length_function=len,
            )
            chunks = text_splitter.split_text(raw_text)
            
            # Create metadata for each chunk
            metadatas = [{"source": filename, "doc_id": doc_id} for _ in chunks]
            
            # Add to vector store
            self.vector_store.add_texts(chunks, metadatas)
            
            # Save vector store
            self.vector_store.save_local(self.vector_dir)
            
            # Update metadata
            self.metadata["documents"][doc_id] = {
                "filename": filename,
                "uploaded_at": datetime.now().isoformat(),
                "chunk_count": len(chunks),
                "file_path": pdf_path
            }
            self._save_metadata()
            
            return True
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return False
    
    def search_documents(self, query, k=3):
        """
        Search for documents relevant to the query
        """
        try:
            # Ensure we have documents before searching
            if len(self.metadata["documents"]) == 0:
                print("No documents available for search")
                return []
                
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Filter out placeholder documents from results
            filtered_results = [(doc, score) for doc, score in results 
                               if doc.metadata.get('doc_id') != 'placeholder']
            
            if not filtered_results:
                print("No relevant documents found in search")
                
            return filtered_results
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    def get_all_documents(self):
        """
        Get metadata for all documents
        """
        return self.metadata["documents"]
    
    def delete_document(self, doc_id):
        """
        Delete a document and its vectors
        """
        if doc_id in self.metadata["documents"]:
            # Get filename
            filename = self.metadata["documents"][doc_id]["filename"]
            
            # Delete PDF file
            pdf_path = os.path.join(self.pdf_dir, filename)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            
            # Remove from metadata
            del self.metadata["documents"][doc_id]
            self._save_metadata()
            
            # Recreate vector store without the deleted document
            # This is a simple approach - in a production system you would want
            # to implement a more efficient way to remove vectors
            self._rebuild_vector_store()
            
            return True
        return False
    
    def _rebuild_vector_store(self):
        """
        Rebuild the vector store from scratch using the PDFs in the pdf_dir
        """
        # Create a new vector store with placeholder
        self.vector_store = FAISS.from_texts(["placeholder content"], self.embeddings,
                                            metadatas=[{"source": "placeholder", "doc_id": "placeholder"}])
        
        # Process each PDF file from metadata
        for doc_id, doc_info in self.metadata["documents"].items():
            filename = doc_info["filename"]
            pdf_path = os.path.join(self.pdf_dir, filename)
            
            if not os.path.exists(pdf_path):
                print(f"Warning: PDF file {filename} not found, skipping")
                continue
            
            try:
                # Extract text
                pdf_reader = PdfReader(pdf_path)
                raw_text = ""
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        raw_text += text
                
                if not raw_text.strip():
                    print(f"No text could be extracted from {filename}")
                    continue
                
                # Split text
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000,
                    chunk_overlap=100,
                    length_function=len,
                )
                chunks = text_splitter.split_text(raw_text)
                
                # Create metadata
                metadatas = [{"source": filename, "doc_id": doc_id} for _ in chunks]
                
                # Add to vector store
                self.vector_store.add_texts(chunks, metadatas)
                
                # Update chunk count in metadata
                self.metadata["documents"][doc_id]["chunk_count"] = len(chunks)
                
                print(f"Added {len(chunks)} chunks from {filename} to vector store")
                
            except Exception as e:
                print(f"Error processing {filename} during rebuild: {e}")
        
        # Save updated vector store
        self.vector_store.save_local(self.vector_dir)
        # Save updated metadata
        self._save_metadata()
        
        print(f"Vector store rebuilt with {len(self.vector_store.docstore._dict)} documents")