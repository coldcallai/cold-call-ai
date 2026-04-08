import { MessageSquare } from "lucide-react";

const TrustLine = ({ className = "" }) => {
  return (
    <p className={`text-cyan-600 text-sm flex items-center gap-2 ${className}`}>
      <MessageSquare className="w-4 h-4" />
      Questions about setup? Chat with us anytime—we'll help you get live in minutes.
    </p>
  );
};

export default TrustLine;
