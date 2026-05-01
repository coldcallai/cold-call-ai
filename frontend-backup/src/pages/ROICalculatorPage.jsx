import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowLeft, Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import ROICalculator from "@/components/ROICalculator";

const ROICalculatorPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const industry = searchParams.get("industry") || "dental";

  const handleGetStarted = () => {
    navigate("/register");
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate("/")}
              className="text-slate-400 hover:text-white"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold text-white">IntentBrain.ai</span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrint}
            className="border-slate-700 text-slate-300 hover:bg-slate-800 print:hidden"
          >
            <Printer className="w-4 h-4 mr-2" />
            Print Report
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="py-12 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Page Title */}
          <div className="text-center mb-10">
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-3">
              Calculate Your ROI
            </h1>
            <p className="text-slate-400 text-lg max-w-2xl mx-auto">
              See exactly how much revenue you're losing to missed calls—and how much 
              you could recover with an AI Receptionist.
            </p>
          </div>

          {/* Calculator */}
          <ROICalculator industry={industry} onGetStarted={handleGetStarted} />

          {/* Additional Info */}
          <div className="mt-12 grid md:grid-cols-3 gap-6">
            <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
              <h3 className="text-white font-semibold mb-2">Why Calls Get Missed</h3>
              <ul className="text-slate-400 text-sm space-y-1">
                <li>• Staff busy with patients/customers</li>
                <li>• After-hours calls (evenings/weekends)</li>
                <li>• High call volume during peak times</li>
                <li>• Staff on lunch breaks or PTO</li>
              </ul>
            </div>
            
            <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
              <h3 className="text-white font-semibold mb-2">What Happens Next</h3>
              <ul className="text-slate-400 text-sm space-y-1">
                <li>• 80% of callers won't leave voicemail</li>
                <li>• They call your competitor instead</li>
                <li>• You never know you lost them</li>
                <li>• The cycle repeats daily</li>
              </ul>
            </div>
            
            <div className="bg-slate-800/50 rounded-xl p-5 border border-slate-700">
              <h3 className="text-white font-semibold mb-2">AI Receptionist Solution</h3>
              <ul className="text-slate-400 text-sm space-y-1">
                <li>• Answers 100% of calls, 24/7</li>
                <li>• Books appointments in real-time</li>
                <li>• Answers FAQs about your services</li>
                <li>• Sends confirmations automatically</li>
              </ul>
            </div>
          </div>

          {/* Industry Selector */}
          <div className="mt-10 text-center">
            <p className="text-slate-500 text-sm mb-3">Calculate for other industries:</p>
            <div className="flex flex-wrap justify-center gap-2">
              {[
                { id: "dental", label: "🦷 Dental" },
                { id: "hvac", label: "🔧 HVAC" },
                { id: "salon", label: "💇 Salon" },
                { id: "legal", label: "⚖️ Legal" },
                { id: "general", label: "📞 General" }
              ].map((ind) => (
                <Button
                  key={ind.id}
                  variant={industry === ind.id ? "default" : "outline"}
                  size="sm"
                  onClick={() => navigate(`/roi-calculator?industry=${ind.id}`)}
                  className={industry === ind.id 
                    ? "bg-emerald-600 hover:bg-emerald-700" 
                    : "border-slate-700 text-slate-300 hover:bg-slate-800"
                  }
                >
                  {ind.label}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Print Styles */}
      <style>{`
        @media print {
          body { 
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          header { position: relative !important; }
        }
      `}</style>
    </div>
  );
};

export default ROICalculatorPage;
