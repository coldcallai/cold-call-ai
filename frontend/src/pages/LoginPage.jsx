import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Phone, Mail, Lock, User, Loader2, CheckCircle2, ArrowLeft, Shield } from "lucide-react";
import { toast } from "sonner";

const API_URL = process.env.REACT_APP_BACKEND_URL;

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, loginWithGoogle, isAuthenticated, user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("login");
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  
  // Registration flow state (multi-step with phone verification)
  const [registerStep, setRegisterStep] = useState(1); // 1: info, 2: verify phone, 3: complete
  const [registerForm, setRegisterForm] = useState({ 
    name: "", 
    email: "", 
    password: "", 
    confirmPassword: "",
    phoneNumber: "",
    verificationCode: "",
    verificationToken: ""
  });
  const [codeSent, setCodeSent] = useState(false);
  const [resendTimer, setResendTimer] = useState(0);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const needsSetup = !user?.setup_wizard_completed;
      const destination = needsSetup ? "/app/getting-started" : (location.state?.from?.pathname || "/app");
      navigate(destination, { replace: true });
    }
  }, [isAuthenticated, user, navigate, location.state]);

  // Resend timer countdown
  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(loginForm.email, loginForm.password);
      toast.success("Welcome back!");
      const pendingPlan = localStorage.getItem('selected_plan');
      if (pendingPlan) {
        navigate("/app/packs", { replace: true });
      } else {
        navigate("/app/getting-started", { replace: true });
      }
    } catch (error) {
      console.error("Login failed:", error);
      toast.error(error.response?.data?.detail || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleSendVerificationCode = async () => {
    // Validate form before sending
    if (!registerForm.name || !registerForm.email || !registerForm.password || !registerForm.phoneNumber) {
      toast.error("Please fill in all fields");
      return;
    }
    
    if (registerForm.password !== registerForm.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }
    
    if (registerForm.password.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }

    // Format phone number
    let phone = registerForm.phoneNumber.replace(/\D/g, '');
    if (phone.length === 10) {
      phone = '+1' + phone;
    } else if (phone.length === 11 && phone.startsWith('1')) {
      phone = '+' + phone;
    } else if (!phone.startsWith('+')) {
      phone = '+' + phone;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/auth/send-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          phone_number: phone,
          email: registerForm.email 
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || "Failed to send verification code");
      }
      
      setCodeSent(true);
      setRegisterStep(2);
      setResendTimer(60); // 60 second cooldown
      toast.success("Verification code sent to your phone!");
    } catch (error) {
      console.error("Failed to send code:", error);
      toast.error(error.message || "Failed to send verification code");
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    if (registerForm.verificationCode.length !== 6) {
      toast.error("Please enter the 6-digit code");
      return;
    }

    let phone = registerForm.phoneNumber.replace(/\D/g, '');
    if (phone.length === 10) {
      phone = '+1' + phone;
    } else if (phone.length === 11 && phone.startsWith('1')) {
      phone = '+' + phone;
    } else if (!phone.startsWith('+')) {
      phone = '+' + phone;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/auth/verify-phone`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          phone_number: phone,
          code: registerForm.verificationCode 
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || "Invalid verification code");
      }
      
      // Store the verification token
      setRegisterForm(prev => ({ ...prev, verificationToken: data.verification_token }));
      toast.success("Phone verified! Creating your account...");
      
      // Now complete registration
      await completeRegistration(data.verification_token, phone);
    } catch (error) {
      console.error("Verification failed:", error);
      toast.error(error.message || "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  const completeRegistration = async (verificationToken, phone) => {
    try {
      const response = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ 
          email: registerForm.email,
          password: registerForm.password,
          name: registerForm.name,
          phone_number: phone,
          verification_code: verificationToken
        })
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || "Registration failed");
      }
      
      // Store session token and redirect
      if (data.session_token) {
        localStorage.setItem("session_token", data.session_token);
      }
      
      toast.success("Account created! Welcome to DialGenix.ai");
      const pendingPlan = localStorage.getItem('selected_plan');
      if (pendingPlan) {
        navigate("/app/packs", { replace: true });
      } else {
        navigate("/app/getting-started", { replace: true });
      }
      // Refresh to load user data
      window.location.reload();
    } catch (error) {
      console.error("Registration failed:", error);
      toast.error(error.message || "Registration failed");
      // Go back to step 1 on failure
      setRegisterStep(1);
      setCodeSent(false);
    }
  };

  const handleGoogleLogin = () => {
    setLoading(true);
    loginWithGoogle();
  };

  const formatPhoneDisplay = (value) => {
    // Format as (XXX) XXX-XXXX for US numbers
    const cleaned = value.replace(/\D/g, '');
    if (cleaned.length <= 3) return cleaned;
    if (cleaned.length <= 6) return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3)}`;
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6, 10)}`;
  };

  return (
    <div className="min-h-screen bg-[#0B1628] flex items-center justify-center p-4">
      {/* Background gradient */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[600px] bg-gradient-to-r from-cyan-500/10 via-teal-500/5 to-transparent rounded-full blur-3xl" />
      </div>

      <div className="w-full max-w-md relative">
        {/* Logo */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-12 bg-gradient-to-br from-cyan-400 to-teal-500 rounded-xl flex items-center justify-center">
            <Phone className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl font-bold text-white">DialGenix.ai</span>
        </div>

        <Card className="bg-white/5 border-white/10 backdrop-blur-xl">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-2xl text-white">Welcome</CardTitle>
            <CardDescription className="text-gray-400">
              Sign in to access your AI sales automation dashboard
            </CardDescription>
          </CardHeader>
          
          <CardContent className="pt-4">
            {/* Google OAuth Button */}
            <Button
              onClick={handleGoogleLogin}
              disabled={loading}
              className="w-full bg-white hover:bg-gray-100 text-gray-900 mb-6 py-6"
              data-testid="google-login-btn"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin mr-2" />
              ) : (
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
              )}
              Continue with Google
            </Button>

            <div className="relative mb-6">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-white/10" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-[#0B1628] px-2 text-gray-500">Or continue with email</span>
              </div>
            </div>

            <Tabs value={activeTab} onValueChange={(v) => { setActiveTab(v); setRegisterStep(1); setCodeSent(false); }} className="w-full">
              <TabsList className="grid w-full grid-cols-2 bg-white/5 mb-4">
                <TabsTrigger value="login" className="data-[state=active]:bg-white/10 text-white">
                  Sign In
                </TabsTrigger>
                <TabsTrigger value="register" className="data-[state=active]:bg-white/10 text-white">
                  Sign Up
                </TabsTrigger>
              </TabsList>

              <TabsContent value="login">
                <form onSubmit={handleLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email" className="text-gray-300">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                      <Input
                        id="login-email"
                        type="email"
                        placeholder="you@company.com"
                        value={loginForm.email}
                        onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                        required
                        className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                        data-testid="login-email-input"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="login-password" className="text-gray-300">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                      <Input
                        id="login-password"
                        type="password"
                        placeholder="••••••••"
                        value={loginForm.password}
                        onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                        required
                        className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                        data-testid="login-password-input"
                      />
                    </div>
                  </div>

                  <Button
                    type="submit"
                    disabled={loading}
                    className="w-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white py-6"
                    data-testid="login-submit-btn"
                  >
                    {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Sign In"}
                  </Button>
                </form>
              </TabsContent>

              <TabsContent value="register">
                {/* Step 1: Enter Info + Phone */}
                {registerStep === 1 && (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="register-name" className="text-gray-300">Full Name</Label>
                      <div className="relative">
                        <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <Input
                          id="register-name"
                          type="text"
                          placeholder="John Doe"
                          value={registerForm.name}
                          onChange={(e) => setRegisterForm({ ...registerForm, name: e.target.value })}
                          required
                          className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                          data-testid="register-name-input"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-email" className="text-gray-300">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <Input
                          id="register-email"
                          type="email"
                          placeholder="you@company.com"
                          value={registerForm.email}
                          onChange={(e) => setRegisterForm({ ...registerForm, email: e.target.value })}
                          required
                          className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                          data-testid="register-email-input"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-phone" className="text-gray-300">Phone Number</Label>
                      <div className="relative">
                        <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <Input
                          id="register-phone"
                          type="tel"
                          placeholder="(555) 123-4567"
                          value={formatPhoneDisplay(registerForm.phoneNumber)}
                          onChange={(e) => setRegisterForm({ ...registerForm, phoneNumber: e.target.value.replace(/\D/g, '').slice(0, 10) })}
                          required
                          className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                          data-testid="register-phone-input"
                        />
                      </div>
                      <p className="text-xs text-gray-500 flex items-center gap-1">
                        <Shield className="w-3 h-3" />
                        We'll send a verification code to prevent trial abuse
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-password" className="text-gray-300">Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <Input
                          id="register-password"
                          type="password"
                          placeholder="••••••••"
                          value={registerForm.password}
                          onChange={(e) => setRegisterForm({ ...registerForm, password: e.target.value })}
                          required
                          className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                          data-testid="register-password-input"
                        />
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="register-confirm" className="text-gray-300">Confirm Password</Label>
                      <div className="relative">
                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                        <Input
                          id="register-confirm"
                          type="password"
                          placeholder="••••••••"
                          value={registerForm.confirmPassword}
                          onChange={(e) => setRegisterForm({ ...registerForm, confirmPassword: e.target.value })}
                          required
                          className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                          data-testid="register-confirm-input"
                        />
                      </div>
                    </div>

                    <Button
                      type="button"
                      onClick={handleSendVerificationCode}
                      disabled={loading || !registerForm.phoneNumber || registerForm.phoneNumber.length < 10}
                      className="w-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white py-6"
                      data-testid="register-send-code-btn"
                    >
                      {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : "Send Verification Code"}
                    </Button>
                  </div>
                )}

                {/* Step 2: Verify Phone Code */}
                {registerStep === 2 && (
                  <div className="space-y-4">
                    <button
                      type="button"
                      onClick={() => { setRegisterStep(1); setCodeSent(false); }}
                      className="flex items-center gap-2 text-gray-400 hover:text-white text-sm transition-colors"
                    >
                      <ArrowLeft className="w-4 h-4" />
                      Back to form
                    </button>

                    <div className="text-center py-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-cyan-500/20 to-teal-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Phone className="w-8 h-8 text-cyan-400" />
                      </div>
                      <h3 className="text-lg font-semibold text-white mb-2">Verify Your Phone</h3>
                      <p className="text-gray-400 text-sm">
                        We sent a 6-digit code to<br />
                        <span className="text-white font-medium">{formatPhoneDisplay(registerForm.phoneNumber)}</span>
                      </p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="verification-code" className="text-gray-300">Verification Code</Label>
                      <Input
                        id="verification-code"
                        type="text"
                        placeholder="123456"
                        value={registerForm.verificationCode}
                        onChange={(e) => setRegisterForm({ ...registerForm, verificationCode: e.target.value.replace(/\D/g, '').slice(0, 6) })}
                        maxLength={6}
                        className="text-center text-2xl tracking-widest bg-white/5 border-white/10 text-white placeholder:text-gray-500"
                        data-testid="verification-code-input"
                      />
                    </div>

                    <Button
                      type="button"
                      onClick={handleVerifyCode}
                      disabled={loading || registerForm.verificationCode.length !== 6}
                      className="w-full bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white py-6"
                      data-testid="verify-code-btn"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin mr-2" />
                          Verifying...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-5 h-5 mr-2" />
                          Verify & Create Account
                        </>
                      )}
                    </Button>

                    <div className="text-center">
                      {resendTimer > 0 ? (
                        <p className="text-gray-500 text-sm">
                          Resend code in {resendTimer}s
                        </p>
                      ) : (
                        <button
                          type="button"
                          onClick={handleSendVerificationCode}
                          disabled={loading}
                          className="text-cyan-400 hover:text-cyan-300 text-sm underline"
                        >
                          Resend code
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </TabsContent>
            </Tabs>

            <p className="text-center text-gray-500 text-sm mt-6">
              By continuing, you agree to our Terms of Service and Privacy Policy
            </p>
          </CardContent>
        </Card>

      </div>
    </div>
  );
};

export default LoginPage;
