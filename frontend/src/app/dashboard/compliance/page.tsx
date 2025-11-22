'use client';

import { ComplianceChecker } from '@/components/compliance/ComplianceChecker';

export default function CompliancePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Compliance Checker</h1>
      <p className="text-gray-600 mb-6">
        Verify your proposals meet all grant requirements and guidelines.
      </p>
      <ComplianceChecker />
    </div>
  );
}
