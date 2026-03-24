import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Bot, User, Loader2, Sparkles } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import axios from "axios";

const API = process.env.REACT_APP_BACKEND_URL + "/api";

const HelpChat = ({ currentPage = "dashboard" }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Hi! I'm your ColdCall.ai assistant. I can help you:\n\n• Set up your first campaign\n• Find high-intent leads\n• Configure AI calling scripts\n• Understand your analytics\n\nWhat would you like help with?"
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setLoading(true);

    try {
      const token = localStorage.getItem("session_token");
      const response = await axios.post(
        `${API}/help/chat`,
        { message: userMessage, context: currentPage },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMessages(prev => [
        ...prev,
        { role: "assistant", content: response.data.response }
      ]);
    } catch (error) {
      setMessages(prev => [
        ...prev,
        {
          role: "assistant",
          content: "Sorry, I'm having trouble connecting. Try refreshing the page or check the Help docs."
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickQuestions = [
    "How do I find leads?",
    "Set up my first campaign",
    "What are good keywords?",
    "How does AI calling work?"
  ];

  return (
    <>
      {/* Chat Toggle Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-20 right-6 z-50 w-14 h-14 bg-gradient-to-r from-cyan-500 to-teal-500 rounded-full shadow-lg hover:shadow-xl transition-all flex items-center justify-center group"
        data-testid="help-chat-toggle"
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <>
            <MessageCircle className="w-6 h-6 text-white" />
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-amber-400 rounded-full flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-amber-900" />
            </span>
          </>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-36 right-6 z-50 w-96 h-[500px] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col overflow-hidden"
          data-testid="help-chat-window">
          {/* Header */}
          <div className="bg-gradient-to-r from-cyan-500 to-teal-500 px-4 py-3 flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-white font-semibold">ColdCall Assistant</h3>
              <p className="text-cyan-100 text-xs">Ask me anything about the platform</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.role === "assistant" && (
                  <div className="w-8 h-8 bg-cyan-100 rounded-full flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-cyan-600" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] px-4 py-2 rounded-2xl whitespace-pre-wrap text-sm ${
                    msg.role === "user"
                      ? "bg-cyan-500 text-white rounded-br-md"
                      : "bg-white text-gray-800 border border-gray-200 rounded-bl-md"
                  }`}
                >
                  {msg.content}
                </div>
                {msg.role === "user" && (
                  <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-2 justify-start">
                <div className="w-8 h-8 bg-cyan-100 rounded-full flex items-center justify-center">
                  <Bot className="w-4 h-4 text-cyan-600" />
                </div>
                <div className="bg-white px-4 py-3 rounded-2xl rounded-bl-md border border-gray-200">
                  <Loader2 className="w-4 h-4 animate-spin text-cyan-500" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions (show only if few messages) */}
          {messages.length <= 2 && (
            <div className="px-4 py-2 border-t border-gray-100 bg-white">
              <p className="text-xs text-gray-500 mb-2">Quick questions:</p>
              <div className="flex flex-wrap gap-1">
                {quickQuestions.map((q, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setInput(q);
                    }}
                    className="text-xs px-2 py-1 bg-cyan-50 text-cyan-700 rounded-full hover:bg-cyan-100 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-3 border-t border-gray-200 bg-white">
            <div className="flex gap-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                placeholder="Ask a question..."
                className="flex-1"
                disabled={loading}
                data-testid="help-chat-input"
              />
              <Button
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="bg-cyan-500 hover:bg-cyan-600"
                data-testid="help-chat-send"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default HelpChat;
