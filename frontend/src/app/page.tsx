'use client';

import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import {
  FlaskConical,
  ArrowRight,
  Lightbulb,
  FileSearch,
  BarChart3,
  Zap,
  Brain,
  BookOpen,
} from 'lucide-react';

export default function HomePage() {
  return (
    <Layout>
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white">
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="max-w-2xl">
            <h1 className="text-4xl font-bold mb-4">
              Background Scientific Cognition System
            </h1>
            <p className="text-xl text-blue-100 mb-8">
              A persistent, autonomous research platform that functions like a researcher&apos;s brain.
              Monitors literature, generates ideas, detects conflicts, and forms hypotheses.
            </p>
            <div className="flex gap-4">
              <Link href="/projects">
                <Button size="lg" className="bg-white text-blue-600 hover:bg-blue-50">
                  Get Started
                  <ArrowRight className="ml-2" size={18} />
                </Button>
              </Link>
              <Button size="lg" variant="ghost" className="text-white border-white/30 hover:bg-white/10">
                Learn More
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="max-w-7xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-12">
          Powerful Research Capabilities
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card hover className="p-6">
            <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center mb-4">
              <Lightbulb className="text-blue-600" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Idea Generation</h3>
            <p className="text-gray-600">
              Autonomous idle research generates new ideas from literature gaps and cross-domain connections.
            </p>
          </Card>

          <Card hover className="p-6">
            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center mb-4">
              <FileSearch className="text-green-600" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Literature Analysis</h3>
            <p className="text-gray-600">
              Searches 5+ academic sources, extracts structured information, and identifies conflicts.
            </p>
          </Card>

          <Card hover className="p-6">
            <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center mb-4">
              <Brain className="text-purple-600" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Hypothesis Formation</h3>
            <p className="text-gray-600">
              Converts research questions into testable hypotheses with validation plans.
            </p>
          </Card>

          <Card hover className="p-6">
            <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center mb-4">
              <BarChart3 className="text-orange-600" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Idea Scoring</h3>
            <p className="text-gray-600">
              Evaluates every idea on 12 dimensions with transparent, explainable scores.
            </p>
          </Card>

          <Card hover className="p-6">
            <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center mb-4">
              <Zap className="text-red-600" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Skill Learning</h3>
            <p className="text-gray-600">
              Creates reusable research skills from successful cycles for future acceleration.
            </p>
          </Card>

          <Card hover className="p-6">
            <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center mb-4">
              <BookOpen className="text-indigo-600" size={24} />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Knowledge Base</h3>
            <p className="text-gray-600">
              Auto-generates research wiki with insights, decisions, and methodology.
            </p>
          </Card>
        </div>
      </div>

      {/* CTA */}
      <div className="bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-6 py-16 text-center">
          <FlaskConical className="mx-auto mb-6 text-blue-400" size={48} />
          <h2 className="text-3xl font-bold mb-4">Ready to Accelerate Your Research?</h2>
          <p className="text-gray-400 mb-8 max-w-2xl mx-auto">
            Start your first research project and let the system monitor literature,
            detect conflicts, and generate novel hypotheses while you focus on what matters.
          </p>
          <Link href="/projects">
            <Button size="lg" className="bg-blue-600 hover:bg-blue-700">
              Start a Project
              <ArrowRight className="ml-2" size={18} />
            </Button>
          </Link>
        </div>
      </div>
    </Layout>
  );
}
