import React, { useState, useEffect, useRef } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPaperPlane, faSpinner } from '@fortawesome/free-solid-svg-icons';

/**
 * Chatbot component that handles user input, displays conversation history,
 * and interacts with the backend streaming API.
 */
const Chatbot = () => {
  const [query, setQuery] = useState(''); // Current user input
  const [messages, setMessages] = useState([]); // Array of { text: string, sender: 'user' | 'bot' }
  const [loading, setLoading] = useState(false); // Indicates if waiting for backend response
  const [error, setError] = useState(''); // Stores any error messages
  const responseRef = useRef(null); // Ref for the message container div to enable auto-scrolling

  /**
   * Effect hook to automatically scroll the message container to the bottom
   * whenever the messages state updates.
   */
  useEffect(() => {
    if (responseRef.current) {
      responseRef.current.scrollTop = responseRef.current.scrollHeight;
    }
  }, [messages]);

  /**
   * Effect to add a welcome message when the chatbot loads.
   */
  useEffect(() => {
    const addWelcomeMessage = () => {
      setMessages([
        { sender: 'bot', text: "Hello! I'm Me-Lo AI, your medical assistant. Ask me anything about health and medicine." }
      ]);
    };
    addWelcomeMessage();
  }, []);


  /**
   * Handles the submission of the user's query.
   * Sends the query and history to the backend streaming endpoint,
   * updates the message list with the user's message and a placeholder for the bot,
   * and processes the streamed response chunks.
   * @param {React.FormEvent<HTMLFormElement>} e - The form submission event.
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || loading) return; // Prevent empty submissions or while loading

    const userMessage = { text: query, sender: 'user' };
    const updatedMessages = [...messages, userMessage, { text: '', sender: 'bot' }];
    setMessages(updatedMessages);
    setQuery('');
    setLoading(true);
    setError('');

    try {
      const res = await fetch('http://127.0.0.1:5000/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query,
          history: messages
        })
      });

      if (!res.ok || !res.body) {
        throw new Error('Failed to connect to server.');
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder('utf-8');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(line => line.startsWith('data: '));

        for (const line of lines) {
          const text = line.replace(/^data: /, '');
          if (text.trim() === '[DONE]') {
            setLoading(false);
            return;
          }

          setMessages(prev => {
            const newMessages = [...prev];
            const lastIndex = newMessages.length - 1;
            if (newMessages[lastIndex].sender === 'bot') {
              newMessages[lastIndex] = {
                ...newMessages[lastIndex],
                text: newMessages[lastIndex].text + text
              };
            }
            return newMessages;
          });
        }
      }

      setLoading(false);
    } catch (err) {
      console.error("Streaming error:", err);
      setError('Something went wrong while generating response.');
      setMessages(prev => prev.slice(0, -1)); // Remove placeholder
      setLoading(false);
    }
  };

  return (
    <div className="chatbot-container">
      <div className="response-container" ref={responseRef}>
        {messages.map((message, index) => (
          <div key={index} className={`response ${message.sender}`}>
            {(message.text || '').split('\n').map((line, i) => (
              <span key={i}>{line}<br /></span>
            ))}
          </div>
        ))}
        {error && <p className="error">{error}</p>}
      </div>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask Me-Lo AI anything..."
        />
        <button type="submit" disabled={loading} className="send-button"> {/* Added class for potential styling */}
          {loading ? <FontAwesomeIcon icon={faSpinner} spin /> : <FontAwesomeIcon icon={faPaperPlane} />}
        </button>
      </form>
    </div>
  );
};

export default Chatbot;