# Compliance Department RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot specifically designed for compliance departments. This application allows users to upload PDF documents containing compliance information and query the content through a user-friendly chat interface.

## Features

- **Document Upload & Management**: Super Admins can upload, manage, and delete PDF documents
- **RAG-based Q&A**: Ask questions about compliance documents and get accurate answers
- **User Access Control**: Role-based access with admin and regular user privileges
- **Citation**: Responses include source citations from relevant documents
- **Modern UI**: Clean and responsive interface built with Streamlit

## Technology Stack

- **Streamlit**: Web interface
- **LangChain**: Retrieval and generation pipeline
- **FAISS (CPU)**: Vector storage and similarity search
- **PyPDF**: PDF text extraction
- **Google Gemini**: Language model for embedding and generation
- **PostgreSQL**: User authentication and metadata storage

## Setup Instructions

### 1. Environment Setup

1. Clone this repository or download the source code
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your API key for Gemini:
     ```
     GEMINI_API_KEY=your_api_key_here
     DB_NAME=compliance_bot
     DB_USER=postgres
     DB_PASSWORD=post123
     DB_HOST=localhost
     DB_PORT=8502
     ```

### 2. Database Setup

1. Install PostgreSQL if not already installed
2. Create a database called `compliance_bot`:
   ```
   createdb compliance_bot
   ```

3. The application will automatically create necessary tables on first run

### 3. Running the Application

1. Start the application:
   ```
   streamlit run app.py
   ```

2. Access the application in your browser at `http://localhost:8501`

3. Initial login credentials:
   - Username: `admin`
   - Password: `adminpassword`

## Usage Guide

### For Administrators

1. **Login**: Use your admin credentials
2. **Upload Documents**: Navigate to "Document Management" to upload PDF files
3. **Manage Users**: Create new users or modify existing ones in the "User Management" section

### For Regular Users

1. **Login**: Use your assigned credentials
2. **Query Documents**: Ask questions in the chat interface
3. **View Sources**: Expand the "View Sources" section to see where information was retrieved from

## Document Processing

The RAG system processes documents as follows:

1. PDF files are uploaded and text is extracted
2. Text is split into smaller chunks
3. Chunks are embedded using Gemini's embedding model
4. Embeddings are stored in a FAISS vector database
5. When queried, relevant chunks are retrieved and sent to the LLM for answer generation

## Security Considerations

- All passwords are hashed with SHA-256 and a unique salt
- Role-based access control prevents unauthorized document uploads
- Activity logging tracks all system usage

## Future Improvements

- Implement more advanced document chunking strategies
- Add document type categorization
- Improve PDF preprocessing for better text extraction
- Implement multi-factor authentication
- Add document analytics (most queried documents, etc.)

## Troubleshooting

- If you encounter database connection issues, ensure PostgreSQL is running and the credentials are correct
- For Gemini API issues, verify your API key and internet connectivity