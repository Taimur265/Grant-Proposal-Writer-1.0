'use client';

import { RiskMatrix } from '@/components/risk/RiskMatrix';

export default function RisksPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Risk Assessment</h1>
      <p className="text-gray-600 mb-6">
        Identify, assess, and mitigate project risks using a comprehensive risk matrix.
      </p>
      <RiskMatrix />
    </div>
  );
}
