The Lenny Growth Assistant

**Project Description-**
The Lenny Growth Assistant is an AI-powered chatbot that helps users explore product management, startup growth, and business strategy. It uses knowledge from Lenny’s Podcast transcripts to find relevant information and generate helpful answers.
The project combines transcript search with a locally running language model, so answers can be based on relevant podcast content.

**Workflow-**
1.Podcast transcript files are placed in the project's transcript folder.

2.The ingestion script reads the files and splits long transcripts into smaller text chunks.

3.The transcript chunks are saved in PostgreSQL so the application can retrieve them later.

4.Ask a question  The user submits a question through the application.

5.The retrieval component searches for transcript chunks related to the question.

6.Ollama runs the configured language model locally. The application provides the question and relevant transcript content to the model.

7.The application returns the generated answer to the user.

**Tech Stack**
Python-	Main programming language used to build the application.

FastAPI	-Creates the backend API and handles user requests.

PostgreSQL-	Stores transcript chunks and other application data defined by the project.

SQLAlchemy	-Connects Python code to the database and helps manage database operations.

Ollama	-Runs a language model locally to generate answers.

TF-IDF - text retrieval	Helps identify transcript chunks relevant to a user's question, if enabled in the current retrieval implementation.

Uvicorn	Runs the FastAPI application server.

**What Is RAG?**
RAG stands for Retrieval-Augmented Generation.
Instead of asking an AI model to answer using only its general knowledge, the application first retrieves relevant information from the podcast transcripts. It then provides that information to the language model as context for generating an answer.

In this project:
Retrieval: Finds useful transcript passages.

Augmentation: Adds those passages to the model's input.

Generation: The model writes a response using the question and supplied context.

**Main Features**
Ingest podcast transcript files.

Split transcripts into smaller chunks.

Store transcript content in PostgreSQL.

Retrieve content relevant to a user's question.

Generate answers using a locally running Ollama model.

Build a foundation for a podcast-based knowledge assistant.

**Run Locally**
Start PostgreSQL and make sure the project database is configured.

Start Ollama and ensure the configured model is available.

Activate your Python virtual environment.

Install dependencies from `requirements.txt`.

Run the transcript ingestion script if the transcript data has not yet been loaded.

Start the FastAPI server:

```powershell

   uvicorn app.main:app --reload

   ```

