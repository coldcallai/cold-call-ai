import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Phone, ArrowLeft } from "lucide-react";

const TermsPage = () => {
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  return (
    <div className="min-h-screen bg-[#0B1628]">
      {/* Header */}
      <header className="border-b border-gray-800">
        <div className="max-w-4xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-teal-500 rounded-xl flex items-center justify-center">
              <Phone className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">DialGenix.ai</span>
          </Link>
          <Link to="/" className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold text-white mb-2">Terms of Service</h1>
        <p className="text-gray-400 mb-8">Effective Date: March 27, 2025</p>

        <div className="prose prose-invert max-w-none">
          <p className="text-gray-300 leading-relaxed mb-8">
            Welcome to DialGenix AI. These Terms of Service ("Terms") govern your access to and use of our AI-powered communication platform, including any related services, applications, and features (collectively, the "Service"). By using DialGenix AI, you agree to these Terms.
          </p>

          {/* Section 1 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">1. Use of Service</h2>
            <p className="text-gray-300 leading-relaxed mb-4">
              You agree to use the Service only in compliance with applicable laws and regulations. You are responsible for all activities conducted under your account.
            </p>
            <p className="text-gray-300 mb-2">You must not:</p>
            <ul className="list-disc list-inside text-gray-300 space-y-2 ml-4">
              <li>Use the Service for unlawful, fraudulent, or abusive purposes</li>
              <li>Misrepresent identity or intent during communications</li>
              <li>Interfere with or disrupt the Service</li>
            </ul>
          </section>

          {/* Section 2 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">2. AI-Generated Communications</h2>
            <p className="text-gray-300 leading-relaxed mb-4">
              DialGenix AI enables automated and AI-assisted communications. You acknowledge that:
            </p>
            <ul className="list-disc list-inside text-gray-300 space-y-2 ml-4">
              <li>AI-generated responses may not always be accurate or appropriate</li>
              <li>You are solely responsible for how the Service is used in outreach</li>
              <li>DialGenix AI is a technology provider only and is not responsible for your compliance with any laws or regulations</li>
            </ul>
            
            <div className="bg-gray-800/50 rounded-lg p-4 mt-4 border border-gray-700">
              <p className="text-gray-400 text-sm font-medium mb-2">Optional Sample Language (For Convenience Only)</p>
              <p className="text-gray-300 text-sm mb-2">
                <strong>Sample Consent Language:</strong> "By providing your phone number, you agree to receive communications from [Your Company Name], which may include automated or AI-assisted calls or messages. Consent is not a condition of purchase."
              </p>
              <p className="text-gray-300 text-sm mb-2">
                <strong>Sample AI Call Opening Script:</strong> "Hello, this is an automated system calling on behalf of [Your Company Name]."
              </p>
              <p className="text-gray-400 text-xs italic">
                These samples are provided for convenience only and do not constitute legal advice. You are responsible for reviewing and ensuring compliance with applicable laws.
              </p>
            </div>
          </section>

          {/* Section 3 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">3. Account Registration</h2>
            <p className="text-gray-300 leading-relaxed mb-4">
              To access certain features, you must create an account. You agree to:
            </p>
            <ul className="list-disc list-inside text-gray-300 space-y-2 ml-4">
              <li>Provide accurate and complete information</li>
              <li>Maintain the security of your account credentials</li>
              <li>Notify us immediately of unauthorized use</li>
            </ul>
            <p className="text-gray-300 leading-relaxed mt-4">
              We reserve the right to suspend or terminate accounts that violate these Terms.
            </p>
          </section>

          {/* Section 4 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">4. Payment and Billing</h2>
            <p className="text-gray-300 leading-relaxed mb-4">
              Some features require payment. By subscribing, you agree to:
            </p>
            <ul className="list-disc list-inside text-gray-300 space-y-2 ml-4">
              <li>Pay all applicable fees</li>
              <li>Authorize recurring billing where applicable</li>
              <li>Provide accurate billing information</li>
            </ul>
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mt-4">
              <p className="text-red-400 font-medium mb-2">No Refund Policy</p>
              <p className="text-gray-300 text-sm">
                All payments made to DialGenix AI are final and non-refundable. We do not provide refunds or credits for partial subscription periods, unused services, or cancellations, unless required by applicable law. Cancellation will only take effect at the end of the current billing cycle.
              </p>
            </div>
            <p className="text-gray-300 leading-relaxed mt-4">
              We may change pricing with reasonable notice.
            </p>
          </section>

          {/* Section 5 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">5. Data and Privacy</h2>
            <p className="text-gray-300 leading-relaxed">
              Your use of the Service is also governed by our <Link to="/privacy" className="text-cyan-400 hover:underline">Privacy Policy</Link>. By using the Service, you consent to the collection and use of information as described therein.
            </p>
          </section>

          {/* Section 6 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">6. Intellectual Property</h2>
            <p className="text-gray-300 leading-relaxed">
              All rights, title, and interest in the Service remain with DialGenix AI. You retain ownership of your data, but grant us a license to use it to operate and improve the Service.
            </p>
          </section>

          {/* Section 7 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">7. Prohibited Conduct</h2>
            <p className="text-gray-300 leading-relaxed mb-4">You agree not to:</p>
            <ul className="list-disc list-inside text-gray-300 space-y-2 ml-4">
              <li>Reverse engineer or attempt to extract source code</li>
              <li>Use the Service to generate spam or harassment</li>
              <li>Upload malicious code or content</li>
            </ul>
          </section>

          {/* Section 8 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">8. Termination</h2>
            <p className="text-gray-300 leading-relaxed">
              We may suspend or terminate your access at any time if you violate these Terms or pose a risk to the Service or others.
            </p>
          </section>

          {/* Section 9 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">9. Disclaimers</h2>
            <p className="text-gray-300 leading-relaxed">
              The Service is provided "as is" without warranties of any kind. DialGenix AI does not guarantee uninterrupted or error-free operation.
            </p>
          </section>

          {/* Section 10 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">10. Limitation of Liability</h2>
            <p className="text-gray-300 leading-relaxed">
              To the fullest extent permitted by law, DialGenix AI shall not be liable for any damages arising from your use of the Service.
            </p>
          </section>

          {/* Section 11 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">11. Changes to Terms</h2>
            <p className="text-gray-300 leading-relaxed">
              We may update these Terms from time to time. Continued use of the Service constitutes acceptance of the revised Terms.
            </p>
          </section>

          {/* Section 12 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">12. Contact</h2>
            <p className="text-gray-300 leading-relaxed">
              For questions, contact us at: <a href="mailto:support@dialgenix.ai" className="text-cyan-400 hover:underline">support@dialgenix.ai</a>
            </p>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8">
        <div className="max-w-4xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-gray-500 text-sm">© 2025 DialGenix.ai. All rights reserved.</p>
          <div className="flex gap-6">
            <Link to="/terms" className="text-gray-400 hover:text-white text-sm">Terms of Service</Link>
            <Link to="/privacy" className="text-gray-400 hover:text-white text-sm">Privacy Policy</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default TermsPage;
