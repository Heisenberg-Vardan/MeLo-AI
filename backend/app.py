import os
from flask import Flask, request, jsonify, stream_with_context
from flask_cors import CORS, cross_origin
from langchain_ollama.chat_models import ChatOllama
from langchain_ollama.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from datasets import load_dataset
import traceback

app = Flask(__name__)
"""
Main Flask application for the RAG Medical Chatbot Backend.

Handles model loading, vector store initialization, and the streaming chat endpoint.
"""
CORS(app, resources={r"/stream": {"origins": "*"}})

# --- Initialize LLM ---
print("Loading ChatOllama model...")
# Keep temp low
llm = ChatOllama(model="llama3", temperature=0.4)
print("Model loaded!")

# --- Embedding & Vector Store Setup ---
CHROMA_PATH = "chroma_medical"
print("Initializing Ollama embedding model...")
embedding_model = OllamaEmbeddings(model="mxbai-embed-large")
print("Embedding model initialized.")

# --- Dataset Loading & Indexing (Keep previous safe logic) ---
if not os.path.exists(CHROMA_PATH):
    print("Loading dataset and building ChromaDB index...")
    dataset = load_dataset("ruslanmv/ai-medical-chatbot", split="train[:1000]") # Small subset
    texts, metadatas = [], []
    print(f"Processing {len(dataset)} records...")
    skipped = 0
    for row in dataset:
        doctor_response, patient_input = row.get("Doctor"), row.get("Patient")
        if isinstance(doctor_response, str) and doctor_response.strip() and isinstance(patient_input, str) and patient_input.strip():
            texts.append(doctor_response)
            metadatas.append({"patient_query": patient_input})
        else: skipped += 1
    print(f"Finished processing. Added {len(texts)} docs, skipped {skipped} rows.")
    if not texts: print("Error: No valid text data found."); exit(1)
    print(f"Creating ChromaDB index with {len(texts)} documents...")
    vectorstore = Chroma.from_texts(texts=texts, embedding=embedding_model, metadatas=metadatas, persist_directory=CHROMA_PATH)
    vectorstore.persist()
    print("ChromaDB index built and saved.")
else:
    print("Loading existing ChromaDB index...")
    vectorstore = Chroma(embedding_function=embedding_model, persist_directory=CHROMA_PATH)
    print("ChromaDB index loaded.")

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
print("Retriever created.")


# --- FINAL REVISION - CORE SYSTEM PROMPT ---
CORE_SYSTEM_PROMPT = (
    "You are an AI assistant providing medical information. Follow these rules **ABSOLUTELY** and **LITERALLY**:\n\n"
    "**HOW TO START YOUR RESPONSE:**\n"
    "1.  **FIRST TURN ONLY (No History):** If this is the very first message from the user (no chat history provided), start your response *ONLY* with: 'Hello! How can I help you with your medical questions today?' Do not add any other introductory text.\n"
    "2.  **SUBSEQUENT TURNS (History Exists):** If there IS chat history, start your response *DIRECTLY* addressing the user's latest message. **DO NOT** use *any* greetings (Hi, Hello) or meta-commentary ('I understand...', 'Based on history...', 'I'm not aware...', 'Okay...'). Get straight to the point.\n\n"
    "**RESPONSE CONTENT RULES:**\n"
    "3.  **FOCUS ON CONVERSATION:** Base your response primarily on the user's direct statements and the conversation history. Acknowledge what the user tells you.\n"
    "4.  **ASK FOCUSED QUESTIONS:** If more information is needed, ask **one or two specific**, relevant follow-up questions based on what's missing from the conversation. Do not ask redundant questions.\n\n"
    "**SAFETY & CONTEXT RULES (CRITICAL):**\n"
    "5.  **NO MEDICAL ADVICE/DIAGNOSIS:** NEVER provide medical advice, diagnosis, or treatment plans. Do not suggest specific medications or dosages.\n"
    "6.  **REFER TO PROFESSIONALS:** ALWAYS end responses discussing symptoms by strongly recommending consultation with a qualified healthcare professional.\n"
    "7.  **CONTEXT IS BACKGROUND ONLY:** Background context provided is from *unrelated past cases*. **NEVER EVER mention specific conditions, treatments, or details from the background context in your response to the user.** Ignore context completely if it seems irrelevant or if using it risks violating Rule #5. General knowledge derived from context must be stated neutrally (e.g., 'Some rashes can be itchy...').\n"
    "8.  **NEUTRAL TONE / NO PERSONA:** Maintain a helpful, neutral tone. Do not invent a persona."
)


# --- Streaming Endpoint ---
@app.route('/stream', methods=['POST'])
@cross_origin()
def stream():
    """
    Handles POST requests to the /stream endpoint for chat interactions.

    Expects a JSON body with 'query' (user's message) and optional 'history'
    (list of previous {'sender': 'user'/'bot', 'text': message} dicts).

    Streams back Server-Sent Events (SSE) with the LLM's response.
    Events:
        - data: A chunk of the response text.
        - error: An error message if something goes wrong.
        - done: Signals the end of the stream with data "[DONE]".
    """
    data = request.get_json()
    if not data: return jsonify({"error": "Request body must be JSON"}), 400
    query = data.get('query')
    history = data.get('history', []) # Check length for Rule #1/#2
    if not query or not query.strip(): return jsonify({"error": "Query parameter missing"}), 400

    print(f"\nReceived query: {query}")
    print(f"History length: {len(history)}")
    is_first_turn = len(history) == 0 # Explicitly check if it's the first turn

    # --- Generator Function ---
    def generate():
        """
        Generator function to handle RAG retrieval and LLM streaming.

        Formats the chat history and latest query, retrieves relevant context
        from ChromaDB, constructs the final prompt, and streams the
        LLM's response chunk by chunk. Handles errors gracefully.
        """
        try:
            # 1. Format Messages
            messages_to_llm = [SystemMessage(content=CORE_SYSTEM_PROMPT)]
            for msg in history: # Add history if it exists
                role = msg.get('sender')
                content = msg.get('text')
                if role == 'user' and content:
                    messages_to_llm.append(HumanMessage(content=content))
                elif role == 'bot' and content:
                    messages_to_llm.append(AIMessage(content=content))

            # 2. Retrieve Context (Optional)
            context_str = ""
            simple_greetings = ["hi", "hello", "hey", "yo", "greetings", "good morning", "good afternoon", "good evening"]
            # We retrieve context even for greetings now, but the prompt tells the LLM how to handle greetings regardless of context.
            # If the query is *not* a greeting, context *might* be useful (handled by Rule #7)
            print("Retrieving relevant documents...")
            docs = retriever.invoke(query)
            if docs:
                context_str = "\n\n---\n\n".join([doc.page_content for doc in docs])
                print(f"Retrieved {len(docs)} documents.")
                # print(f"Context Snippet:\n{context_str[:500]}...") # Debug
            else:
                print("No relevant documents found.")


            # 3. Add Final Human Message (Simplified - relies heavily on System Prompt)
            # Include context block marker even if empty, prompt handles it.
            turn_prompt_template = (
                "(Background Context - Informational Only - Follow Rule #7 Strictly:\n"
                "```\n{context}\n```)\n\n"
                "User's latest message: \"{user_query}\""
            )
            context_to_use = context_str if context_str else "None retrieved."
            final_human_message = HumanMessage(
                content=turn_prompt_template.format(context=context_to_use, user_query=query)
            )
            messages_to_llm.append(final_human_message)

            print(f"Sending {len(messages_to_llm)} messages to LLM.")

            # 4. Stream Response
            print("Streaming response from LLM...")
            stream_iterator = llm.stream(messages_to_llm)
            full_response = ""
            for chunk in stream_iterator:
                content_piece = chunk.content
                if content_piece:
                    full_response += content_piece
                    yield f"data: {content_piece}\n\n"

            # 5. Signal Completion
            yield "event: done\ndata: [DONE]\n\n"
            print(f"Completed response stream. Full response length: {len(full_response)}")
            # print(f"Full response:\n{full_response.strip()}") # Optional debug

        except Exception as e:
            print(f"Error during generation: {e}")
            print(traceback.format_exc())
            error_message = "Sorry, an error occurred while processing your request."
            yield f"event: error\ndata: {error_message}\n\n"
            yield "event: done\ndata: [DONE]\n\n"

    # --- Return Response ---
    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"
    }
    return app.response_class(stream_with_context(generate()), mimetype='text/event-stream', headers=headers)

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
