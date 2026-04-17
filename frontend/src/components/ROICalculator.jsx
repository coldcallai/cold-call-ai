import { useState, useEffect } from "react";
import { Calculator, Phone, DollarSign, TrendingUp, Calendar, Clock, CheckCircle, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";

const ROICalculator = ({ industry = "dental", onGetStarted }) => {
  // Industry presets
  const industryDefaults = {
    dental: {
      name: "Dental Practice",
      avgAppointmentValue: 285,
      missedCallsPerWeek: 12,
      conversionRate: 35,
      monthlyPlanCost: 99,
      icon: "🦷"
    },
    hvac: {
      name: "HVAC Service",
      avgAppointmentValue: 350,
      missedCallsPerWeek: 15,
      conversionRate: 40,
      monthlyPlanCost: 99,
      icon: "🔧"
    },
    salon: {
      name: "Salon/Spa",
      avgAppointmentValue: 95,
      missedCallsPerWeek: 20,
      conversionRate: 45,
      monthlyPlanCost: 49,
      icon: "💇"
    },
    legal: {
      name: "Law Firm",
      avgAppointmentValue: 500,
      missedCallsPerWeek: 8,
      conversionRate: 25,
      monthlyPlanCost: 199,
      icon: "⚖️"
    },
    general: {
      name: "Service Business",
      avgAppointmentValue: 200,
      missedCallsPerWeek: 10,
      conversionRate: 30,
      monthlyPlanCost: 99,
      icon: "📞"
    }
  };

  const defaults = industryDefaults[industry] || industryDefaults.general;

  const [missedCalls, setMissedCalls] = useState(defaults.missedCallsPerWeek);
  const [avgValue, setAvgValue] = useState(defaults.avgAppointmentValue);
  const [conversionRate, setConversionRate] = useState(defaults.conversionRate);
  const [monthlyPlanCost, setMonthlyPlanCost] = useState(defaults.monthlyPlanCost);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Calculations
  const missedCallsPerMonth = missedCalls * 4.33;
  const potentialBookingsPerMonth = missedCallsPerMonth * (conversionRate / 100);
  const monthlyLostRevenue = potentialBookingsPerMonth * avgValue;
  const annualLostRevenue = monthlyLostRevenue * 12;
  
  // With AI Receptionist (assumes 85% answer rate, same conversion)
  const aiAnswerRate = 0.85;
  const recoveredCallsPerMonth = missedCallsPerMonth * aiAnswerRate;
  const recoveredBookingsPerMonth = recoveredCallsPerMonth * (conversionRate / 100);
  const monthlyRecoveredRevenue = recoveredBookingsPerMonth * avgValue;
  const annualRecoveredRevenue = monthlyRecoveredRevenue * 12;
  
  // ROI
  const annualPlanCost = monthlyPlanCost * 12;
  const netAnnualGain = annualRecoveredRevenue - annualPlanCost;
  const roiPercentage = ((netAnnualGain / annualPlanCost) * 100).toFixed(0);
  const paybackDays = ((monthlyPlanCost / (monthlyRecoveredRevenue / 30))).toFixed(0);

  const formatCurrency = (num) => {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(num);
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <Card className="bg-gradient-to-br from-slate-900 to-slate-800 border-slate-700 text-white overflow-hidden">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-cyan-500 rounded-xl flex items-center justify-center text-2xl">
              {defaults.icon}
            </div>
            <div>
              <CardTitle className="text-2xl font-bold text-white">
                {defaults.name} ROI Calculator
              </CardTitle>
              <CardDescription className="text-slate-400">
                See how much revenue you're losing to missed calls
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Input Section */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* Left: Inputs */}
            <div className="space-y-5">
              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                <Label className="text-slate-300 text-sm font-medium mb-3 block">
                  Missed Calls Per Week
                </Label>
                <div className="flex items-center gap-4">
                  <Slider
                    value={[missedCalls]}
                    onValueChange={(val) => setMissedCalls(val[0])}
                    min={1}
                    max={50}
                    step={1}
                    className="flex-1"
                  />
                  <div className="bg-slate-700 px-3 py-1.5 rounded-lg min-w-[60px] text-center">
                    <span className="text-xl font-bold text-emerald-400">{missedCalls}</span>
                  </div>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Industry avg: {defaults.missedCallsPerWeek} calls/week go unanswered
                </p>
              </div>

              <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                <Label className="text-slate-300 text-sm font-medium mb-3 block">
                  Average Appointment Value
                </Label>
                <div className="flex items-center gap-4">
                  <Slider
                    value={[avgValue]}
                    onValueChange={(val) => setAvgValue(val[0])}
                    min={50}
                    max={1000}
                    step={25}
                    className="flex-1"
                  />
                  <div className="bg-slate-700 px-3 py-1.5 rounded-lg min-w-[80px] text-center">
                    <span className="text-xl font-bold text-emerald-400">${avgValue}</span>
                  </div>
                </div>
              </div>

              {/* Advanced Toggle */}
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-sm text-slate-400 hover:text-slate-300 flex items-center gap-1"
              >
                {showAdvanced ? "Hide" : "Show"} advanced settings
                <ArrowRight className={`w-3 h-3 transition-transform ${showAdvanced ? "rotate-90" : ""}`} />
              </button>

              {showAdvanced && (
                <div className="space-y-4 animate-in slide-in-from-top-2">
                  <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                    <Label className="text-slate-300 text-sm font-medium mb-3 block">
                      Call-to-Booking Rate: {conversionRate}%
                    </Label>
                    <Slider
                      value={[conversionRate]}
                      onValueChange={(val) => setConversionRate(val[0])}
                      min={10}
                      max={60}
                      step={5}
                    />
                  </div>
                  
                  <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
                    <Label className="text-slate-300 text-sm font-medium mb-2 block">
                      AI Receptionist Plan
                    </Label>
                    <div className="flex gap-2">
                      {[
                        { price: 49, name: "Lite" },
                        { price: 99, name: "Pro" },
                        { price: 199, name: "Plus" }
                      ].map((plan) => (
                        <button
                          key={plan.price}
                          onClick={() => setMonthlyPlanCost(plan.price)}
                          className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                            monthlyPlanCost === plan.price
                              ? "bg-emerald-500 text-white"
                              : "bg-slate-700 text-slate-300 hover:bg-slate-600"
                          }`}
                        >
                          ${plan.price}/mo
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Results */}
            <div className="space-y-4">
              {/* Lost Revenue Card */}
              <div className="bg-gradient-to-br from-red-500/20 to-red-600/10 rounded-xl p-5 border border-red-500/30">
                <div className="flex items-center gap-2 mb-3">
                  <Phone className="w-5 h-5 text-red-400" />
                  <span className="text-red-300 font-medium">Without AI Receptionist</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Missed calls/month</span>
                    <span className="text-white font-semibold">{missedCallsPerMonth.toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Lost bookings/month</span>
                    <span className="text-white font-semibold">{potentialBookingsPerMonth.toFixed(1)}</span>
                  </div>
                  <div className="border-t border-red-500/30 pt-2 mt-2">
                    <div className="flex justify-between items-center">
                      <span className="text-red-300 font-medium">Monthly Lost Revenue</span>
                      <span className="text-red-400 font-bold text-xl">{formatCurrency(monthlyLostRevenue)}</span>
                    </div>
                    <div className="flex justify-between items-center mt-1">
                      <span className="text-red-300/70 text-sm">Annual Lost Revenue</span>
                      <span className="text-red-400/80 font-semibold">{formatCurrency(annualLostRevenue)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recovered Revenue Card */}
              <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 rounded-xl p-5 border border-emerald-500/30">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <span className="text-emerald-300 font-medium">With AI Receptionist</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Calls answered by AI</span>
                    <span className="text-white font-semibold">{recoveredCallsPerMonth.toFixed(0)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Additional bookings/month</span>
                    <span className="text-white font-semibold">{recoveredBookingsPerMonth.toFixed(1)}</span>
                  </div>
                  <div className="border-t border-emerald-500/30 pt-2 mt-2">
                    <div className="flex justify-between items-center">
                      <span className="text-emerald-300 font-medium">Monthly Recovered Revenue</span>
                      <span className="text-emerald-400 font-bold text-xl">{formatCurrency(monthlyRecoveredRevenue)}</span>
                    </div>
                    <div className="flex justify-between items-center mt-1">
                      <span className="text-emerald-300/70 text-sm">Annual Recovered Revenue</span>
                      <span className="text-emerald-400/80 font-semibold">{formatCurrency(annualRecoveredRevenue)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ROI Summary */}
          <div className="bg-gradient-to-r from-cyan-500/10 via-emerald-500/10 to-cyan-500/10 rounded-xl p-6 border border-emerald-500/30">
            <div className="grid md:grid-cols-4 gap-4 text-center">
              <div>
                <p className="text-slate-400 text-sm mb-1">Plan Cost</p>
                <p className="text-2xl font-bold text-white">{formatCurrency(monthlyPlanCost)}<span className="text-sm text-slate-400">/mo</span></p>
              </div>
              <div>
                <p className="text-slate-400 text-sm mb-1">Net Annual Gain</p>
                <p className="text-2xl font-bold text-emerald-400">{formatCurrency(netAnnualGain)}</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm mb-1">ROI</p>
                <p className="text-2xl font-bold text-cyan-400">{roiPercentage}%</p>
              </div>
              <div>
                <p className="text-slate-400 text-sm mb-1">Pays for Itself</p>
                <p className="text-2xl font-bold text-amber-400">{paybackDays} days</p>
              </div>
            </div>
            
            <div className="mt-4 pt-4 border-t border-emerald-500/20 text-center">
              <p className="text-slate-300">
                For every <span className="text-white font-semibold">$1</span> you invest, 
                you get back <span className="text-emerald-400 font-bold">${(netAnnualGain / annualPlanCost + 1).toFixed(2)}</span>
              </p>
            </div>
          </div>

          {/* CTA */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
            <Button 
              onClick={onGetStarted}
              className="bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white px-8 py-6 text-lg font-semibold rounded-xl"
            >
              Get Started
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
            <Button 
              variant="outline"
              className="border-slate-600 text-slate-300 hover:bg-slate-800 px-8 py-6 text-lg rounded-xl"
              onClick={() => window.open("https://calendly.com/intentbrain/15-30min", "_blank")}
            >
              <Calendar className="w-5 h-5 mr-2" />
              Book a Demo
            </Button>
          </div>

          {/* Trust Badge */}
          <p className="text-center text-slate-500 text-sm">
            Setup in minutes • No long-term contracts • Cancel anytime
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default ROICalculator;
