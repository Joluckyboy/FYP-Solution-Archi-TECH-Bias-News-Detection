'use client'

import { useState, useEffect } from 'react'

const API_URL = 'http://localhost:8000'

interface HealthStatus {
  api?: string
  supabase?: string
  redis?: string
  elasticsearch?: string
}

export default function Home() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus>({})
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<string | null>(null)

  // Test basic connection on load
  useEffect(() => {
    testConnection()
  }, [])

  const testConnection = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/health`)
      const data = await response.json()
      setTestResult(`✅ Backend connected: ${data.status}`)
    } catch (err) {
      setError(`❌ Cannot connect to backend at ${API_URL}`)
      setTestResult(null)
    } finally {
      setLoading(false)
    }
  }

  const testFullHealth = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/v1/health/full`)
      const data = await response.json()
      setHealthStatus(data)
      setTestResult('✅ Full health check completed')
    } catch (err) {
      setError(`❌ Health check failed: ${err}`)
      setHealthStatus({})
    } finally {
      setLoading(false)
    }
  }

  const testCreateArticle = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/v1/news/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: 'Frontend Test Article',
          content: 'This article was created from the Next.js frontend to test the connection.',
          source: 'Frontend Test',
          author: 'Test User',
        }),
      })
      const data = await response.json()
      setTestResult(`✅ Article created with ID: ${data.id}`)
    } catch (err) {
      setError(`❌ Failed to create article: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  const testGetArticles = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_URL}/api/v1/news/`)
      const data = await response.json()
      setTestResult(`✅ Found ${data.length} articles in database`)
    } catch (err) {
      setError(`❌ Failed to fetch articles: ${err}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <div className="z-10 max-w-5xl w-full items-center justify-center">
        <h1 className="text-4xl font-bold text-center mb-4">
          Bias News Detection System
        </h1>
        <p className="text-center text-lg mb-8">
          AI-powered analysis to detect bias in news articles
        </p>

        {/* Connection Test Section */}
        <div className="mb-8 p-6 border rounded-lg bg-blue-50 dark:bg-blue-900">
          <h2 className="text-2xl font-semibold mb-4">🔌 Connection Tests</h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <button
              onClick={testConnection}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
            >
              Basic Health
            </button>
            <button
              onClick={testFullHealth}
              disabled={loading}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
            >
              Full Health
            </button>
            <button
              onClick={testGetArticles}
              disabled={loading}
              className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400"
            >
              Get Articles
            </button>
            <button
              onClick={testCreateArticle}
              disabled={loading}
              className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:bg-gray-400"
            >
              Create Article
            </button>
          </div>

          {loading && (
            <div className="text-center text-gray-600 dark:text-gray-300">
              Testing connection...
            </div>
          )}

          {testResult && (
            <div className="mt-4 p-3 bg-green-100 dark:bg-green-800 rounded">
              <p className="text-green-800 dark:text-green-100">{testResult}</p>
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-100 dark:bg-red-800 rounded">
              <p className="text-red-800 dark:text-red-100">{error}</p>
              <p className="text-sm mt-2">Make sure backend is running: cd backend && docker-compose up -d</p>
            </div>
          )}

          {Object.keys(healthStatus).length > 0 && (
            <div className="mt-4 p-4 bg-white dark:bg-gray-800 rounded">
              <h3 className="font-semibold mb-2">Service Health Status:</h3>
              <ul className="space-y-1">
                {Object.entries(healthStatus).map(([service, status]) => (
                  <li key={service} className="flex items-center">
                    <span className="font-mono text-sm w-32">{service}:</span>
                    <span className={`ml-2 ${status === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
                      {status === 'healthy' ? '✅' : '❌'} {status}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Tech Stack Section */}
        <div className="mt-8 p-6 border rounded-lg bg-white dark:bg-gray-800">
          <h2 className="text-2xl font-semibold mb-4">Tech Stack</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="font-semibold text-blue-600">Frontend</h3>
              <ul className="list-disc list-inside">
                <li>Next.js 14</li>
                <li>TypeScript</li>
                <li>Tailwind CSS</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-blue-600">Backend</h3>
              <ul className="list-disc list-inside">
                <li>FastAPI</li>
                <li>Python 3.11</li>
                <li>Dramatiq</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-blue-600">Databases</h3>
              <ul className="list-disc list-inside">
                <li>Supabase (PostgreSQL)</li>
                <li>Redis</li>
                <li>Elasticsearch</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-blue-600">Orchestration</h3>
              <ul className="list-disc list-inside">
                <li>Docker Compose</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="mt-6 text-center space-x-4">
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Backend API Docs →
          </a>
          <a
            href="https://app.supabase.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Supabase Dashboard →
          </a>
        </div>
      </div>
    </main>
  )
}
