import React from 'react';
import { motion } from 'framer-motion';

const PrivacyPolicy = () => {
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
          
          <h1 className="text-4xl font-bold text-white mb-4">Privacy Policy</h1>
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
              <h2 className="text-2xl font-semibold text-white mb-4">1. Introduction</h2>
              <p className="text-white/90 mb-4">
                ShareSync ("we," "our," or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our file sharing service.
              </p>
              <p className="text-white/90">
                Please read this privacy policy carefully. If you do not agree with the terms of this privacy policy, please do not access the service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">2. Information We Collect</h2>
              
              <h3 className="text-xl font-semibold text-white mb-3">2.1 Personal Information</h3>
              <p className="text-white/90 mb-4">
                We may collect personal information that you voluntarily provide to us when you:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Register for an account</li>
                <li>Use our Google OAuth authentication</li>
                <li>Contact us for support</li>
                <li>Subscribe to our newsletter</li>
              </ul>
              
              <h3 className="text-xl font-semibold text-white mb-3">2.2 File Information</h3>
              <p className="text-white/90 mb-4">
                When you upload files to ShareSync, we collect:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>File metadata (name, size, type, upload date)</li>
                <li>File content (temporarily stored and encrypted)</li>
                <li>Expiry settings and password protection preferences</li>
                <li>Download statistics and access logs</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3">2.3 Usage Information</h3>
              <p className="text-white/90 mb-4">
                We automatically collect certain information when you use our service:
              </p>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>IP address and location data</li>
                <li>Browser type and version</li>
                <li>Device information and operating system</li>
                <li>Usage patterns and feature interactions</li>
                <li>Performance metrics and error logs</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">3. How We Use Your Information</h2>
              <p className="text-white/90 mb-4">
                We use the information we collect for the following purposes:
              </p>
              
              <h3 className="text-xl font-semibold text-white mb-3">3.1 Service Provision</h3>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Provide, operate, and maintain our file sharing service</li>
                <li>Process file uploads, downloads, and sharing</li>
                <li>Manage user accounts and authentication</li>
                <li>Enable P2P connections and cloud storage</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3">3.2 Service Improvement</h3>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Analyze usage patterns to improve our service</li>
                <li>Develop new features and functionality</li>
                <li>Monitor and analyze performance metrics</li>
                <li>Conduct research and analytics</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3">3.3 Communication</h3>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Send service-related notifications</li>
                <li>Respond to customer support inquiries</li>
                <li>Provide updates about our service</li>
                <li>Send security alerts and important notices</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">4. Data Security</h2>
              <p className="text-white/90 mb-4">
                We implement robust security measures to protect your information:
              </p>
              
              <h3 className="text-xl font-semibold text-white mb-3">4.1 Encryption</h3>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>All files are encrypted during transmission using TLS/SSL</li>
                <li>Files are encrypted at rest in our storage systems</li>
                <li>Password-protected files use additional encryption layers</li>
                <li>P2P connections use end-to-end encryption</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3">4.2 Access Controls</h3>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Multi-factor authentication for admin access</li>
                <li>Role-based access controls for our systems</li>
                <li>Regular security audits and penetration testing</li>
                <li>Automated monitoring for suspicious activities</li>
              </ul>

              <h3 className="text-xl font-semibold text-white mb-3">4.3 Data Minimization</h3>
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>We collect only necessary information</li>
                <li>Files are automatically deleted after expiry</li>
                <li>Personal data is anonymized where possible</li>
                <li>Regular cleanup of old logs and temporary data</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">5. Data Sharing and Disclosure</h2>
              <p className="text-white/90 mb-4">
                We do not sell, trade, or rent your personal information to third parties. We may share your information only in the following circumstances:
              </p>
              
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li><strong>Service Providers:</strong> With trusted third-party service providers who assist in operating our service</li>
                <li><strong>Legal Requirements:</strong> When required by law, court order, or government request</li>
                <li><strong>Safety and Security:</strong> To protect the rights, property, or safety of ShareSync, our users, or others</li>
                <li><strong>Business Transfers:</strong> In connection with a merger, acquisition, or sale of assets</li>
                <li><strong>Consent:</strong> With your explicit consent for specific purposes</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">6. Data Retention</h2>
              <p className="text-white/90 mb-4">
                Our data retention practices include:
              </p>
              
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li><strong>Files:</strong> Automatically deleted after specified expiry time (2 hours to 1 day)</li>
                <li><strong>Account Data:</strong> Retained while your account is active</li>
                <li><strong>Usage Logs:</strong> Retained for up to 90 days for security and analytics</li>
                <li><strong>Download Records:</strong> Retained for up to 90 days for analytics</li>
                <li><strong>Support Communications:</strong> Retained for up to 2 years</li>
              </ul>
              
              <p className="text-white/90">
                You can request deletion of your account and associated data at any time.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">7. Your Privacy Rights</h2>
              <p className="text-white/90 mb-4">
                Depending on your location, you may have the following rights:
              </p>
              
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li><strong>Access:</strong> Request access to your personal information</li>
                <li><strong>Correction:</strong> Request correction of inaccurate information</li>
                <li><strong>Deletion:</strong> Request deletion of your personal information</li>
                <li><strong>Portability:</strong> Request a copy of your data in a portable format</li>
                <li><strong>Restriction:</strong> Request restriction of processing</li>
                <li><strong>Objection:</strong> Object to certain types of processing</li>
                <li><strong>Withdrawal:</strong> Withdraw consent for data processing</li>
              </ul>
              
              <p className="text-white/90">
                To exercise these rights, please contact us using the information provided below.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">8. Cookies and Tracking</h2>
              <p className="text-white/90 mb-4">
                We use cookies and similar tracking technologies to:
              </p>
              
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Maintain user sessions and authentication</li>
                <li>Remember user preferences and settings</li>
                <li>Analyze usage patterns and improve our service</li>
                <li>Provide personalized experiences</li>
              </ul>
              
              <p className="text-white/90">
                You can control cookie settings through your browser preferences. However, disabling cookies may affect the functionality of our service.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">9. Third-Party Services</h2>
              <p className="text-white/90 mb-4">
                ShareSync integrates with the following third-party services:
              </p>
              
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li><strong>Google OAuth:</strong> For user authentication (subject to Google's Privacy Policy)</li>
                <li><strong>Cloudflare R2:</strong> For cloud file storage (subject to Cloudflare's Privacy Policy)</li>
                <li><strong>Analytics Services:</strong> For usage analytics and performance monitoring</li>
              </ul>
              
              <p className="text-white/90">
                These services have their own privacy policies, and we encourage you to review them.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">10. International Data Transfers</h2>
              <p className="text-white/90 mb-4">
                Your information may be transferred to and processed in countries other than your own. We ensure that such transfers comply with applicable data protection laws and implement appropriate safeguards.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">11. Children's Privacy</h2>
              <p className="text-white/90 mb-4">
                ShareSync is not intended for children under 13 years of age. We do not knowingly collect personal information from children under 13. If we become aware that we have collected personal information from a child under 13, we will take steps to delete such information.
              </p>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">12. Changes to This Privacy Policy</h2>
              <p className="text-white/90 mb-4">
                We may update this Privacy Policy from time to time. We will notify you of any changes by:
              </p>
              
              <ul className="list-disc list-inside text-white/90 mb-4 space-y-2">
                <li>Posting the new Privacy Policy on this page</li>
                <li>Updating the "Last updated" date</li>
                <li>Sending you an email notification for significant changes</li>
                <li>Displaying a prominent notice on our service</li>
              </ul>
            </section>

            <section className="mb-8">
              <h2 className="text-2xl font-semibold text-white mb-4">13. Contact Us</h2>
              <p className="text-white/90 mb-4">
                If you have any questions about this Privacy Policy or our data practices, please contact us:
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
                This Privacy Policy is effective as of the date stated above and will remain in effect except with respect to any changes in its provisions in the future.
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default PrivacyPolicy;

