import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Phone, ArrowLeft } from "lucide-react";

const PrivacyPage = () => {
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
        <h1 className="text-4xl font-bold text-white mb-2">Privacy Policy</h1>
        <p className="text-gray-400 mb-8">Effective Date: March 27, 2025</p>

        <div className="prose prose-invert max-w-none">
          <p className="text-gray-300 leading-relaxed mb-8">
            DialGenix AI ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, and safeguard your information.
          </p>

          {/* Section 1 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">1. Information We Collect</h2>
            <p className="text-gray-300 leading-relaxed mb-4">We may collect:</p>
            <ul className="list-disc list-inside text-gray-300 space-y-2 ml-4">
              <li>Personal information (name, email, phone number)</li>
              <li>Account and billing details</li>
              <li>Communication data (call logs, transcripts, recordings where applicable)</li>
              <li>Device and usage information</li>
            </ul>
          </section>

          {/* Section 2 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">2. How We Use Information</h2>
            <p className="text-gray-300 leading-relaxed mb-4">We use your information to:</p>
            <ul className="list-disc list-inside text-gray-300 space-y-2 ml-4">
              <li>Provide and improve the Service</li>
              <li>Process transactions</li>
              <li>Personalize user experience</li>
              <li>Ensure compliance with legal obligations</li>
              <li>Detect and prevent fraud or abuse</li>
            </ul>
          </section>

          {/* Section 3 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">3. Sharing of Information</h2>
            <p className="text-gray-300 leading-relaxed mb-4">
              We do not sell your personal data. We may share information with:
            </p>
            <ul className="list-disc list-inside text-gray-300 space-y-2 ml-4">
              <li>Service providers and infrastructure partners</li>
              <li>Legal authorities when required</li>
              <li>Business transfers (e.g., merger or acquisition)</li>
            </ul>
          </section>

          {/* Section 4 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">4. Data Retention</h2>
            <p className="text-gray-300 leading-relaxed">
              We retain information only as long as necessary to provide the Service or comply with legal obligations.
            </p>
          </section>

          {/* Section 5 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">5. Security</h2>
            <p className="text-gray-300 leading-relaxed">
              We implement industry-standard security measures, but no system is completely secure.
            </p>
          </section>

          {/* Section 6 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">6. Your Rights</h2>
            <p className="text-gray-300 leading-relaxed mb-4">
              Depending on your location, you may have rights to:
            </p>
            <ul className="list-disc list-inside text-gray-300 space-y-2 ml-4">
              <li>Access or correct your data</li>
              <li>Request deletion</li>
              <li>Object to processing</li>
              <li>Withdraw consent</li>
            </ul>
          </section>

          {/* Section 7 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">7. Cookies and Tracking</h2>
            <p className="text-gray-300 leading-relaxed">
              We may use cookies and similar technologies to enhance user experience and analyze usage.
            </p>
          </section>

          {/* Section 8 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">8. Third-Party Services</h2>
            <p className="text-gray-300 leading-relaxed">
              The Service may integrate with third-party tools. We are not responsible for their privacy practices.
            </p>
          </section>

          {/* Section 9 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">9. Children's Privacy</h2>
            <p className="text-gray-300 leading-relaxed">
              The Service is not intended for individuals under 18.
            </p>
          </section>

          {/* Section 10 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">10. Changes to Privacy Policy</h2>
            <p className="text-gray-300 leading-relaxed">
              We may update this policy periodically. Continued use indicates acceptance of changes.
            </p>
          </section>

          {/* Section 11 */}
          <section className="mb-8">
            <h2 className="text-2xl font-semibold text-white mb-4">11. Contact Us</h2>
            <p className="text-gray-300 leading-relaxed">
              For privacy-related inquiries, contact: <a href="mailto:support@dialgenix.ai" className="text-cyan-400 hover:underline">support@dialgenix.ai</a>
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

export default PrivacyPage;
