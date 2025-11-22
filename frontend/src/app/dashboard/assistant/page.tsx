'use client';

import { AIChatAssistant } from '@/components/ai/AIChatAssistant';

export default function AssistantPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">AI Grant Writing Assistant</h1>
      <p className="text-gray-600 mb-6">
        Get AI-powered help with your grant proposals, compliance questions, and writing challenges.
      </p>
      <AIChatAssistant contextType="general" />
    </div>
  );
}
