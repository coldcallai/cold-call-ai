import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Package, CreditCard, Zap, Phone, ShoppingCart, CheckCircle, RefreshCw, Clock, Search
} from "lucide-react";
import TrustLine from "@/components/TrustLine";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CreditPacks = () => {
  const { user, refreshUser, sessionToken } = useAuth();
  const [packs, setPacks] = useState({ subscription_plans: {}, lead_packs: [], call_packs: [], topup_packs: [] });
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(null);
  const [activeTab, setActiveTab] = useState("subscriptions");
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [checkingPayment, setCheckingPayment] = useState(false);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('session_token');
      const [packsRes, historyRes] = await Promise.all([
        axios.get(`${API}/packs`),
        axios.get(`${API}/payments/history`, { headers: { Authorization: `Bearer ${token}` } }).catch(() => ({ data: { transactions: [] } }))
      ]);
      setPacks(packsRes.data);
      setPaymentHistory(historyRes.data.transactions || []);
    } catch (error) {
      toast.error("Failed to load packs");
    } finally {
      setLoading(false);
    }
  };

  // Check for payment success on page load
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    const success = urlParams.get('success');
    const canceled = urlParams.get('canceled');
    
    if (canceled) {
      toast.info("Payment was canceled");
      window.history.replaceState({}, '', window.location.pathname);
    } else if (sessionId && success) {
      checkPaymentStatus(sessionId);
    }
    
    fetchData();
  }, []);

  const checkPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 5;
    setCheckingPayment(true);
    
    if (attempts >= maxAttempts) {
      setCheckingPayment(false);
      toast.warning("Payment status check timed out. Please check your email for confirmation.");
      return;
    }
    
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.get(`${API}/checkout/status/${sessionId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.payment_status === 'paid') {
        toast.success(`Payment successful! ${response.data.leads_added > 0 ? `+${response.data.leads_added} leads` : ''} ${response.data.calls_added > 0 ? `+${response.data.calls_added} calls` : ''}`);
        refreshUser();
        fetchData();
        setCheckingPayment(false);
        window.history.replaceState({}, '', window.location.pathname);
      } else if (response.data.status === 'expired') {
        toast.error("Payment session expired. Please try again.");
        setCheckingPayment(false);
        window.history.replaceState({}, '', window.location.pathname);
      } else {
        // Still pending, poll again
        setTimeout(() => checkPaymentStatus(sessionId, attempts + 1), 2000);
      }
    } catch (error) {
      console.error('Error checking payment:', error);
      setCheckingPayment(false);
      toast.error("Error checking payment status");
    }
  };

  const initiateCheckout = async (itemType, itemId, billingCycle = 'monthly') => {
    setPurchasing(`${itemType}_${itemId}`);
    try {
      const token = localStorage.getItem('session_token');
      const response = await axios.post(`${API}/checkout/create-session`, {
        item_type: itemType,
        item_id: itemId,
        origin_url: window.location.origin,
        billing_cycle: billingCycle
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Redirect to Stripe checkout
      window.location.href = response.data.checkout_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create checkout session");
      setPurchasing(null);
    }
  };

  // Auto-trigger Stripe checkout if user came from landing page with a plan
  useEffect(() => {
    const pendingPlan = localStorage.getItem('selected_plan');
    if (pendingPlan && !loading && user) {
      localStorage.removeItem('selected_plan');
      initiateCheckout('subscription', pendingPlan);
    }
  }, [loading, user]);

  if (loading || checkingPayment) {
    return (
      <div className="p-6 md:p-8 space-y-6">
        <div className="text-center py-12">
          <Clock className="w-12 h-12 text-cyan-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">{checkingPayment ? "Verifying payment..." : "Loading..."}</p>
        </div>
      </div>
    );
  }

  const plans = Object.entries(packs.subscription_plans || {}).map(([key, plan]) => ({
    id: key,
    ...plan
  }));

  const isBYOL = user?.subscription_tier === 'byl' || user?.subscription_tier === 'byl_starter' || user?.subscription_tier === 'byl_pro' || user?.subscription_tier === 'byl_scale';

  return (
    <div className="p-6 md:p-8 space-y-6" data-testid="credit-packs-page">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-gray-900" style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
          Pricing & Plans
        </h1>
        <p className="text-gray-500 mt-1">Choose a plan or purchase additional credits</p>
        {!isBYOL && (
          <p className="text-xs text-blue-600 mt-1 bg-blue-50 px-2 py-1 rounded inline-block">
            💡 Subscriptions reset monthly. Buy top-ups anytime for extra leads or calls that never expire.
          </p>
        )}
      </div>

      {/* Current Balance */}
      <Card className="bg-gradient-to-r from-cyan-500 to-teal-500 text-white border-0 shadow-lg">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-cyan-100 text-sm font-medium">Your Current Balance</p>
              <div className="flex items-center gap-8 mt-3">
                <div>
                  <p className="text-4xl font-bold">{user?.lead_credits_remaining?.toLocaleString() || 0}</p>
                  <p className="text-cyan-100 text-sm">Lead Credits</p>
                </div>
                <div className="h-12 w-px bg-white/30" />
                <div>
                  <p className="text-4xl font-bold">{user?.call_credits_remaining?.toLocaleString() || 0}</p>
                  <p className="text-cyan-100 text-sm">Call Credits</p>
                </div>
              </div>
            </div>
            <div className="text-right">
              <Badge className="bg-white/20 text-white border-0 text-sm">
                {user?.subscription_tier ? packs.subscription_plans?.[user.subscription_tier]?.name || 'Free Trial' : 'Free Trial'}
              </Badge>
              <p className="text-cyan-100 text-sm mt-2">{user?.subscription_status === 'active' ? 'Active' : 'Inactive'}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className={`grid w-full max-w-2xl ${isBYOL ? 'grid-cols-1' : 'grid-cols-4'}`}>
          <TabsTrigger value="subscriptions">Subscriptions</TabsTrigger>
          {!isBYOL && <TabsTrigger value="leads">Lead Packs</TabsTrigger>}
          {!isBYOL && <TabsTrigger value="calls">Call Packs</TabsTrigger>}
          {!isBYOL && <TabsTrigger value="topups">Top-ups</TabsTrigger>}
        </TabsList>

        {/* Subscription Plans */}
        <TabsContent value="subscriptions" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan) => (
              <Card key={plan.id} className={`bg-white border relative ${plan.id === 'professional' ? 'border-cyan-500 shadow-lg' : 'border-gray-200'}`}>
                {plan.id === 'professional' && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-full text-xs font-medium">
                    Most Popular
                  </div>
                )}
                <CardContent className="p-6">
                  <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                  <div className="mt-3">
                    <span className="text-3xl font-bold text-gray-900">${plan.price}</span>
                    <span className="text-gray-500">/mo</span>
                  </div>
                  <ul className="mt-4 space-y-2">
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-cyan-500" />
                      <span>{plan.leads_per_month.toLocaleString()} leads/mo</span>
                    </li>
                    <li className="flex items-center gap-2 text-sm">
                      <CheckCircle className="w-4 h-4 text-cyan-500" />
                      <span>{plan.calls_per_month === -1 ? 'Unlimited' : plan.calls_per_month.toLocaleString()} calls/mo</span>
                    </li>
                    {plan.features?.slice(0, 3).map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-gray-600">
                        <CheckCircle className="w-4 h-4 text-gray-400" />
                        <span>{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button
                    className={`w-full mt-6 ${plan.id === 'professional' ? 'bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600' : 'bg-gray-900 hover:bg-gray-800'} text-white`}
                    onClick={() => initiateCheckout('subscription', plan.id)}
                    disabled={purchasing === `subscription_${plan.id}`}
                    data-testid={`buy-${plan.id}-btn`}
                  >
                    {purchasing === `subscription_${plan.id}` ? (
                      <Clock className="w-4 h-4 animate-spin" />
                    ) : user?.subscription_tier === plan.id ? (
                      'Current Plan'
                    ) : (
                      'Subscribe'
                    )}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
          <p className="text-center text-gray-500 text-sm mt-6">
            Save 5% with quarterly billing or 15% with annual billing
          </p>
        </TabsContent>

        {/* Lead Packs */}
        <TabsContent value="leads" className="mt-6">
          <p className="text-sm text-gray-600 mb-4">Auto-replenishing lead subscriptions for consistent prospecting.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {(packs.lead_packs || []).map((pack) => (
              <Card key={pack.id} className="bg-white border border-gray-200 hover:border-cyan-300 hover:shadow-md transition-all">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-cyan-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Search className="w-6 h-6 text-cyan-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900">{pack.name}</h3>
                  <p className="text-3xl font-bold text-gray-900 mt-2">${pack.price}</p>
                  <p className="text-sm text-gray-500 mt-1">${pack.per_lead?.toFixed(3) || (pack.price / pack.quantity).toFixed(3)}/lead</p>
                  {pack.recurring && <Badge className="mt-2 bg-cyan-100 text-cyan-700">Monthly</Badge>}
                  <Button
                    className="w-full mt-4 bg-gradient-to-r from-cyan-500 to-teal-500 hover:from-cyan-600 hover:to-teal-600 text-white"
                    onClick={() => initiateCheckout('lead_pack', pack.id)}
                    disabled={purchasing === `lead_pack_${pack.id}`}
                  >
                    {purchasing === `lead_pack_${pack.id}` ? <Clock className="w-4 h-4 animate-spin" /> : 'Subscribe'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Call Packs */}
        <TabsContent value="calls" className="mt-6">
          <p className="text-sm text-gray-600 mb-4">Overage protection - buy extra calls when you need them.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {(packs.call_packs || []).map((pack) => (
              <Card key={pack.id} className="bg-white border border-gray-200 hover:border-violet-300 hover:shadow-md transition-all">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-violet-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Phone className="w-6 h-6 text-violet-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900">{pack.name}</h3>
                  <p className="text-3xl font-bold text-gray-900 mt-2">${pack.price}</p>
                  <p className="text-sm text-gray-500 mt-1">${pack.per_call?.toFixed(4) || (pack.price / pack.quantity).toFixed(4)}/call</p>
                  <Button
                    className="w-full mt-4 bg-gradient-to-r from-violet-500 to-purple-500 hover:from-violet-600 hover:to-purple-600 text-white"
                    onClick={() => initiateCheckout('call_pack', pack.id)}
                    disabled={purchasing === `call_pack_${pack.id}`}
                  >
                    {purchasing === `call_pack_${pack.id}` ? <Clock className="w-4 h-4 animate-spin" /> : 'Buy Now'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* Top-up Packs */}
        <TabsContent value="topups" className="mt-6">
          <p className="text-sm text-gray-600 mb-4">One-time top-ups at premium rates. For occasional needs only.</p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {(packs.topup_packs || []).map((pack) => (
              <Card key={pack.id} className="bg-white border border-gray-200 hover:border-amber-300 hover:shadow-md transition-all">
                <CardContent className="p-6 text-center">
                  <div className="w-12 h-12 bg-amber-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                    <Zap className="w-6 h-6 text-amber-600" />
                  </div>
                  <h3 className="font-semibold text-gray-900">{pack.name}</h3>
                  <p className="text-3xl font-bold text-gray-900 mt-2">${pack.price}</p>
                  <p className="text-sm text-gray-500 mt-1">${pack.per_unit?.toFixed(2) || (pack.price / pack.quantity).toFixed(2)}/unit</p>
                  <Badge className="mt-2 bg-amber-100 text-amber-700">One-time</Badge>
                  <Button
                    className="w-full mt-4 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white"
                    onClick={() => initiateCheckout('topup', pack.id)}
                    disabled={purchasing === `topup_${pack.id}`}
                  >
                    {purchasing === `topup_${pack.id}` ? <Clock className="w-4 h-4 animate-spin" /> : 'Top Up'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* Payment History */}
      {paymentHistory.length > 0 && (
        <Card className="bg-white border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle style={{ fontFamily: "'Barlow Condensed', sans-serif" }}>
              Payment History
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {paymentHistory.slice(0, 10).map((tx, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                      tx.item_type === 'subscription' ? 'bg-cyan-100' :
                      tx.item_type === 'lead_pack' ? 'bg-cyan-100' :
                      tx.item_type === 'call_pack' ? 'bg-violet-100' : 'bg-amber-100'
                    }`}>
                      {tx.item_type === 'subscription' ? <CreditCard className="w-4 h-4 text-cyan-600" /> :
                       tx.item_type === 'lead_pack' ? <Search className="w-4 h-4 text-cyan-600" /> :
                       tx.item_type === 'call_pack' ? <Phone className="w-4 h-4 text-violet-600" /> :
                       <Zap className="w-4 h-4 text-amber-600" />}
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{tx.item_name}</p>
                      <p className="text-xs text-gray-500">{new Date(tx.created_at).toLocaleDateString()}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-gray-900">${tx.amount}</p>
                    <Badge className={tx.payment_status === 'paid' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>
                      {tx.payment_status}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Protected Route Component

export default CreditPacks;
