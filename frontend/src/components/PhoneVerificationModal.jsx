import { useState, useEffect } from "react";
import { Phone, Loader2, CheckCircle2, Shield, X } from "lucide-react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { toast } from "sonner";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const PhoneVerificationModal = ({ isOpen, onClose, onVerified, userEmail }) => {
  const [step, setStep] = useState(1); // 1: enter phone, 2: enter code
  const [phoneNumber, setPhoneNumber] = useState("");
  const [verificationCode, setVerificationCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);

  // Resend timer countdown
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  const formatPhoneDisplay = (value) => {
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length <= 3) return cleaned;
    if (cleaned.length <= 6) return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3)}`;
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6, 10)}`;
  };

  const normalizePhone = (value) => {
    let phone = value.replace(/\D/g, '');
    if (phone.length === 10) {
      phone = '+1' + phone;
    } else if (phone.length === 11 && phone.startsWith('1')) {
      phone = '+' + phone;
    } else if (!phone.startsWith('+')) {
      phone = '+' + phone;
    }
    return phone;
  };

  const handleSendCode = async () => {
    if (phoneNumber.length < 10) {
      toast.error("Please enter a valid phone number");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/auth/send-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          phone_number: normalizePhone(phoneNumber),
          email: userEmail 
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || "Failed to send verification code");
      }
      
      setStep(2);
      setResendTimer(60);
      toast.success("Verification code sent to your phone!");
    } catch (error) {
      console.error("Failed to send code:", error);
      toast.error(error.message || "Failed to send verification code");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (verificationCode.length !== 6) {
      toast.error("Please enter the 6-digit code");
      return;
    }

    setLoading(true);
    try {
      // First verify the code
      const verifyResponse = await fetch(`${API_URL}/api/auth/verify-phone`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          phone_number: normalizePhone(phoneNumber),
          code: verificationCode 
        })
      });
      
      const verifyData = await verifyResponse.json();
      
      if (!verifyResponse.ok) {
        throw new Error(verifyData.detail || "Invalid verification code");
      }

      // Now complete OAuth phone verification
      const completeResponse = await fetch(`${API_URL}/api/auth/verify-phone-oauth`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ 
          phone_number: normalizePhone(phoneNumber),
          verification_code: verifyData.verification_token 
        })
      });
      
      const completeData = await completeResponse.json();
      
      if (!completeResponse.ok) {
        throw new Error(completeData.detail || "Failed to complete verification");
      }

      toast.success("Phone verified! You can now use your free trial.");
      onVerified();
    } catch (error) {
      console.error("Verification failed:", error);
      toast.error(error.message || "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#0F1A2E] border border-white/10 rounded-2xl max-w-md w-full p-6 relative">
        {/* Close button - only show if not required */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-cyan-500/20 to-teal-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <Shield className="w-8 h-8 text-cyan-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Verify Your Phone</h2>
          <p className="text-gray-400 text-sm">
            {step === 1 
              ? "To prevent trial abuse, please verify your phone number to activate your 15 free minutes."
              : `We sent a code to ${formatPhoneDisplay(phoneNumber)}`
            }
          </p>
        </div>

        {/* Step 1: Enter Phone */}
        {step === 1 && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="phone" className="text-gray-300">Phone Number</Label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <Input
                  id="phone"
                  type="tel"
                  placeholder="(555) 123-4567"
                  value={formatPhoneDisplay(phoneNumber)}
                  onChange={(e) => setPhoneNumber(e.target.value.replace(/\D/g, '').slice(0, 10))}
                  className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                  data-testid="oauth-phone-input"
                />
              </div>
            </div>

            <Button
              onClick={handleSendCode}
              disabled={loading || phoneNumber.length < 10}
              className="w-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white py-6"
              data-testid="oauth-send-code-btn"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Send Verification Code"}
            </Button>
          </div>
        )}

        {/* Step 2: Enter Code */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="code" className="text-gray-300">Verification Code</Label>
              <Input
                id="code"
                type="text"
                placeholder="123456"
                value={verificationCode}
                onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                maxLength={6}
                className="text-center text-2xl tracking-widest bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                data-testid="oauth-verification-code-input"
              />
            </div>

            <Button
              onClick={handleVerifyCode}
              disabled={loading || verificationCode.length !== 6}
              className="w-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white py-6"
              data-testid="oauth-verify-code-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  Verifying...
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-5 h-5 mr-2" />
                  Verify & Activate Trial
                </>
              )}
            </Button>

            <div className="flex items-center justify-between text-sm">
              <button
                type="button"
                onClick={() => { setStep(1); setVerificationCode(""); }}
                className="text-gray-400 hover:text-white"
              >
                Change number
              </button>
              
              {resendTimer > 0 ? (
                <span className="text-gray-500">
                  Resend in {resendTimer}s
                </span>
              ) : (
                <button
                  type="button"
                  onClick={handleSendCode}
                  disabled={loading}
                  className="text-cyan-400 hover:text-cyan-300"
                >
                  Resend code
                </button>
              )}
            </div>
          </div>
        )}

        {/* Info note */}
        <p className="text-center text-gray-500 text-xs mt-4">
          Each phone number can only be used for one free trial.
        </p>
      </div>
    </div>
  );
};

export default PhoneVerificationModal;
