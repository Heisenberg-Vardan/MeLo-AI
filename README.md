# Me-Lo AI: RAG Medical Information Assistant

Me-Lo AI (Medical AI by LongevAI) is a chatbot application designed to provide helpful medical information using a Retrieval-Augmented Generation (RAG) approach. It combines a local Large Language Model (LLM) with a vector database containing medical context to answer user queries.

**Core Features:**

*   **Flask Backend:** Serves the LLM and manages the RAG pipeline.
*   **React Frontend:** Provides a user-friendly chat interface.
*   **Local LLM:** Uses a locally run model (e.g., Llama 3 via Ollama) for generation.
*   **ChromaDB Vector Store:** Stores and retrieves relevant medical information embeddings from the **Hugging Face dataset 'ruslanmv/ai-medical-chatbot'**.
*   **Streaming Responses:** Delivers answers chunk by chunk for a more interactive experience.
*   **Safety Focused:** Includes prompts designed to avoid giving medical advice and direct users to professionals.

## Project Structure

```
RAG_Chatbot/
├── backend/             # Python Flask backend
│   ├── app.py           # Main Flask application logic, RAG pipeline
│   ├── requirements.txt # Python dependencies
│   ├── chroma_medical/  # Vector database (created/used by app.py)
│   └── models/          # Location for local LLM models (e.g., .gguf files)
├── frontend/            # React frontend application
│   ├── public/          # Static assets (index.html, icons)
│   ├── src/             # React source code
│   │   ├── App.js       # Main application component (layout, theme)
│   │   ├── Chatbot.js   # Chat interface logic and display
│   │   ├── App.css      # Main styling
│   │   └── index.js     # Entry point for React app
│   ├── package.json     # Frontend dependencies (React, etc.) and scripts
│   └── .gitignore       # Ignores node_modules, build files, etc.
├── .gitignore           # Root ignore file (Python venv, models, etc.)
└── README.md            # This file
```

## Setup and Running

**Prerequisites:**

*   **Python:** Python 3.x is required. You can download it from [python.org](https://www.python.org/downloads/). Ensure `pip` is installed with your Python installation.
*   **Node.js and NPM:** Node.js is required to run the frontend. Download it from [nodejs.org](https://nodejs.org/). NPM (Node Package Manager) is included with Node.js. To verify installation, run `node -v` and `npm -v` in your terminal. If not installed, follow the instructions on the Node.js website to install both Node.js and NPM.
*   **Ollama:** Ollama is required to run the local Large Language Model (LLM). Install Ollama by following the instructions on [ollama.com](https://ollama.com/). After installing Ollama, run it to ensure it's running in the background. You will also need to pull the required models using Ollama CLI:
    *   `ollama pull llama3` (for the language model)
    *   `ollama pull mxbai-embed-large` (for embeddings)

**Steps:**

1.  **Clone/Download:** Get the project files onto your local machine.
2.  **Backend Setup:**
    *   Navigate to the backend directory: `cd backend`
    *   Create a virtual environment (recommended): `python -m venv venv`
    *   Activate the virtual environment:
        *   Windows: `.\venv\Scripts\activate`
        *   macOS/Linux: `source venv/bin/activate`
    *   Install Python dependencies: `pip install -r requirements.txt`
    *   Run the Flask server: `python app.py`

3.  **Frontend Setup:**
    *   Open a *new* terminal window.
    *   Navigate to the frontend directory: `cd frontend`
    *   Install Node.js dependencies: `npm install`
    *   Start the React development server: `npm start`

4.  **Access:** Open your web browser and go to `http://localhost:3000`.
