'use client';

import { MetricsDashboard } from '@/components/reporting/MetricsDashboard';

export default function MetricsPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Metrics Dashboard</h1>
      <p className="text-gray-600 mb-6">
        Track key performance indicators and project metrics.
      </p>
      <MetricsDashboard />
    </div>
  );
}
