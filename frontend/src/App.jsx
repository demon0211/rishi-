import { useState } from 'react'
import UploadArea from './components/UploadArea'
import TemplateSelector from './components/TemplateSelector'
import './index.css'

function App() {
  const [file, setFile] = useState(null)
  const [template, setTemplate] = useState('IEEE')
  const [format, setFormat] = useState('pdf') // New state for format
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile)
    setResult(null)
    setError(null)
  }

  const handleProcess = async () => {
    if (!file) {
      setError("Please select a file first.")
      return
    }

    setProcessing(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('template', template)
    formData.append('format', format) // Send format to backend

    try {
      const response = await fetch('http://localhost:5000/process', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`)
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      console.error(err)
      setError("Failed to process document. Is the backend running?")
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>AI Research Paper Formatter</h1>
        <p>Transform raw text into publication-ready Documents</p>
      </header>

      <main className="app-main">
        <section className="control-panel">
          <UploadArea onFileSelect={handleFileSelect} selectedFile={file} />

          <div className="options-area">
            <TemplateSelector
              selected={template}
              onSelect={setTemplate}
              selectedFormat={format}
              onSelectFormat={setFormat}
            />

            <button
              className="process-btn"
              onClick={handleProcess}
              disabled={!file || processing}
            >
              {processing ? 'Formatting...' : `Format as ${format.toUpperCase()}`}
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}
        </section>

        {result && (
          <section className="results-panel">
            <h2>Success!</h2>
            <p>Your document has been formatted successfully.</p>

            <div className="sections-list">
              <h3>Detected Sections:</h3>
              <ul>
                {result.sections_found.map(sec => (
                  <li key={sec}>{sec}</li>
                ))}
              </ul>
            </div>

            <a
              href={`http://localhost:5000${result.download_url}`}
              className="download-link"
              target="_blank"
              rel="noreferrer"
            >
              Download {format.toUpperCase()}
            </a>
          </section>
        )}
      </main>
    </div>
  )
}

export default App
