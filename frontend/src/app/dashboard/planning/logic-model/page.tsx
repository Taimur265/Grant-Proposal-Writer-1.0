'use client';

import { LogicModelBuilder } from '@/components/logic-model/LogicModelBuilder';

export default function LogicModelPage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Logic Model / Theory of Change</h1>
      <p className="text-gray-600 mb-6">
        Build a visual representation of your project's theory of change, mapping inputs to impacts.
      </p>
      <LogicModelBuilder projectId="" />
    </div>
  );
}
