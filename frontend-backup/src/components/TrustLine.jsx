import { MessageSquare, Sparkles } from "lucide-react";

const TrustLine = ({ className = "" }) => {
  return (
    <div className={`group flex items-center gap-2 cursor-pointer transition-all duration-300 hover:scale-[1.02] ${className}`}>
      <div className="relative">
        <MessageSquare className="w-4 h-4 text-cyan-500 group-hover:text-cyan-400 transition-colors" />
        <Sparkles className="w-3 h-3 text-yellow-400 absolute -top-1 -right-1 animate-pulse opacity-80" />
      </div>
      <p className="text-cyan-600 text-sm group-hover:text-cyan-500 transition-colors">
        Questions about setup? <span className="font-medium">Chat with us anytime</span>—we'll help you get live in minutes.
      </p>
    </div>
  );
};

export default TrustLine;
