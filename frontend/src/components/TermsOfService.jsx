import React from 'react';
import { motion } from 'framer-motion';

const TermsOfService = () => {
  const lastUpdated = "December 2024";

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <button
            onClick={() => window.history.back()}
            className="inline-flex items-center gap-2 text-white/80 hover:text-white mb-6 transition-colors"
          >
            ← Back
          </button>
          
          <h1 className="text-4xl font-bold text-white mb-4">Terms of Service</h1>
          <p className="text-white/80">Last updated: {lastUpdated}</p>
        </motion.div>

        {/* Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20"
        >
          <div className="prose prose-invert max-w-none">
            
            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">1. Acceptance of Terms</h2>
              <p className="text-white/90 mb-4">
                By accessing and using ShareSync ("the Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
              </p>
              <p className="text-white/90">
                ShareSync is a file sharing platform that allows users to share files both locally (peer-to-peer) and through cloud storage. These terms govern your use of our service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">2. Description of Service</h2>
              <p className="text-white/90 mb-4">
                ShareSync provides the following services:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Cloud-based file sharing with temporary storage</li>
                <li>Peer-to-peer (P2P) local file sharing</li>
                <li>File encryption and password protection</li>
                <li>QR code generation for easy sharing</li>
                <li>Analytics and usage tracking</li>
                <li>Automated file cleanup and expiry</li>
              </ul>
              <p className="text-white/90">
                We reserve the right to modify, suspend, or discontinue any aspect of the service at any time.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">3. User Responsibilities</h2>
              <p className="text-white/90 mb-4">
                As a user of ShareSync, you agree to:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Use the service only for lawful purposes</li>
                <li>Not upload, share, or transmit any illegal, harmful, or offensive content</li>
                <li>Respect intellectual property rights of others</li>
                <li>Not attempt to gain unauthorized access to our systems</li>
                <li>Not use the service to distribute malware, viruses, or harmful code</li>
                <li>Comply with all applicable laws and regulations</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">4. File Storage and Retention</h2>
              <p className="text-white/90 mb-4">
                ShareSync provides temporary file storage with the following policies:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Files are automatically deleted after their specified expiry time</li>
                <li>Maximum file size limit is 100MB per file</li>
                <li>We reserve the right to remove files that violate our terms</li>
                <li>Users are responsible for maintaining their own backups</li>
                <li>We do not guarantee permanent storage of any files</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">5. Privacy and Data Protection</h2>
              <p className="text-white/90 mb-4">
                Your privacy is important to us. Our data practices include:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Files are encrypted during transmission and storage</li>
                <li>We collect minimal personal information necessary for service operation</li>
                <li>Usage analytics are anonymized and aggregated</li>
                <li>We do not sell or share your personal data with third parties</li>
                <li>You can request deletion of your account and associated data</li>
              </ul>
              <p className="text-white/90">
                For detailed information, please review our Privacy Policy.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">6. Prohibited Content</h2>
              <p className="text-white/90 mb-4">
                The following types of content are strictly prohibited:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Copyrighted material without proper authorization</li>
                <li>Illegal or harmful content</li>
                <li>Malware, viruses, or malicious code</li>
                <li>Content that violates privacy rights</li>
                <li>Spam or unsolicited commercial content</li>
                <li>Content that promotes violence or hatred</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">7. Service Availability</h2>
              <p className="text-white/90 mb-4">
                While we strive to maintain high availability:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>We do not guarantee 100% uptime</li>
                <li>Maintenance may require temporary service interruptions</li>
                <li>We are not liable for any losses due to service unavailability</li>
                <li>Emergency maintenance may occur without prior notice</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">8. Limitation of Liability</h2>
              <p className="text-white/90 mb-4">
                ShareSync and its operators shall not be liable for:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Any direct, indirect, incidental, or consequential damages</li>
                <li>Loss of data, files, or business opportunities</li>
                <li>Damages resulting from unauthorized access to your files</li>
                <li>Issues arising from third-party integrations</li>
                <li>Any damages exceeding the amount paid for the service</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">9. Account Termination</h2>
              <p className="text-white/90 mb-4">
                We reserve the right to terminate accounts that:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Violate these terms of service</li>
                <li>Engage in abusive or harmful behavior</li>
                <li>Attempt to compromise system security</li>
                <li>Remain inactive for extended periods</li>
              </ul>
              <p className="text-white/90">
                Users may also delete their accounts at any time through the settings page.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">10. Intellectual Property</h2>
              <p className="text-white/90 mb-4">
                ShareSync and its original content, features, and functionality are owned by ShareSync and are protected by international copyright, trademark, patent, trade secret, and other intellectual property laws.
              </p>
              <p className="text-white/90">
                Users retain ownership of their uploaded files but grant ShareSync a limited license to store, process, and transmit files as necessary to provide the service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">11. Changes to Terms</h2>
              <p className="text-white/90 mb-4">
                We reserve the right to modify these terms at any time. Changes will be effective immediately upon posting. Continued use of the service after changes constitutes acceptance of the new terms.
              </p>
              <p className="text-white/90">
                We will notify users of significant changes through the service or via email.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">12. Governing Law</h2>
              <p className="text-white/90 mb-4">
                These terms shall be governed by and construed in accordance with the laws of [Your Jurisdiction], without regard to its conflict of law provisions.
              </p>
              <p className="text-white/90">
                Any disputes arising from these terms or the use of ShareSync shall be resolved through binding arbitration.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">13. Contact Information</h2>
              <p className="text-white/90 mb-4">
                If you have any questions about these Terms of Service, please contact us:
              </p>
              <ul className="list-disc list-inside text-white/90 space-y-2">
                <li>Email: anjiteshshandilya@gmail.com</li>
                <li>Website: https://sharesync.app/contact</li>
                <li>Address: No Address Lol</li>
                <li>Data Protection Officer: anjiteshshandilya@gmail.com</li>
              </ul>
            </section>

            <div className="mt-12 pt-8 border-t border-white/20">
              <p className="text-white/60 text-sm text-center">
                By using ShareSync, you acknowledge that you have read, understood, and agree to be bound by these Terms of Service.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default TermsOfService;

