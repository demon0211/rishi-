import { useState } from 'react'
import UploadArea from './components/UploadArea'
import TemplateSelector from './components/TemplateSelector'
import './index.css'

function App() {
  const [file, setFile] = useState(null)
  const [pastedText, setPastedText] = useState('')
  const [usePastedText, setUsePastedText] = useState(false)

  const [template, setTemplate] = useState('IEEE')
  const [format, setFormat] = useState('pdf')
  const [processing, setProcessing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  // Styling States
  const [titleSize, setTitleSize] = useState(24)
  const [sectionSize, setSectionSize] = useState(10)
  const [subheadingSize, setSubheadingSize] = useState(10)
  const [bodySize, setBodySize] = useState(10)
  const [lineSpacing, setLineSpacing] = useState(1.0)
  const [fontFamily, setFontFamily] = useState('Times New Roman')

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile)
    setUsePastedText(false)
    setResult(null)
    setError(null)
  }

  const handleProcess = async () => {
    if (!file && !pastedText) {
      setError("Please select a file or paste text first.")
      return
    }

    setProcessing(true)
    setError(null)

    const formData = new FormData()
    if (usePastedText) {
      formData.append('text', pastedText)
    } else {
      formData.append('file', file)
    }

    formData.append('template', template)
    formData.append('format', format)

    // Append styling params
    formData.append('titleSize', titleSize)
    formData.append('sectionSize', sectionSize)
    formData.append('subheadingSize', subheadingSize)
    formData.append('bodySize', bodySize)
    formData.append('lineSpacing', lineSpacing)
    formData.append('fontFamily', fontFamily)

    try {
      const response = await fetch('http://127.0.0.1:5000/process', {
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
      setError(`Failed to process document. Is the backend running? (${err.message})`)
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
          <div className="input-toggle">
            <button
              className={!usePastedText ? 'active' : ''}
              onClick={() => setUsePastedText(false)}
            >
              Upload File
            </button>
            <button
              className={usePastedText ? 'active' : ''}
              onClick={() => setUsePastedText(true)}
            >
              Paste Text
            </button>
          </div>

          {!usePastedText ? (
            <UploadArea onFileSelect={handleFileSelect} selectedFile={file} />
          ) : (
            <div className="paste-area">
              <textarea
                placeholder="Paste your research content here (supporting Markdown or raw text)..."
                value={pastedText}
                onChange={(e) => setPastedText(e.target.value)}
              />
            </div>
          )}

          <div className="settings-grid">
            <div className="settings-column">
              <h3>Document Options</h3>
              <TemplateSelector
                selected={template}
                onSelect={setTemplate}
                selectedFormat={format}
                onSelectFormat={setFormat}
              />
            </div>

            <div className="settings-column">
              <h3>Styling Settings</h3>
              <div className="style-option">
                <label>Font Family:</label>
                <select value={fontFamily} onChange={(e) => setFontFamily(e.target.value)}>
                  <option value="Times New Roman">Times New Roman</option>
                  <option value="Arial">Arial</option>
                  <option value="Helvetica">Helvetica</option>
                </select>
              </div>
              <div className="style-option">
                <label>Title Size ({titleSize}pt):</label>
                <input type="range" min="12" max="48" value={titleSize} onChange={(e) => setTitleSize(e.target.value)} />
              </div>
              <div className="style-option">
                <label>Body Size ({bodySize}pt):</label>
                <input type="range" min="8" max="14" value={bodySize} onChange={(e) => setBodySize(e.target.value)} />
              </div>
              <div className="style-option">
                <label>Line Spacing ({lineSpacing}):</label>
                <select value={lineSpacing} onChange={(e) => setLineSpacing(e.target.value)}>
                  <option value="1.0">1.0 (Single)</option>
                  <option value="1.15">1.15</option>
                  <option value="1.5">1.5</option>
                  <option value="2.0">2.0 (Double)</option>
                </select>
              </div>
            </div>
          </div>

          <button
            className="process-btn"
            onClick={handleProcess}
            disabled={(!file && !pastedText) || processing}
          >
            {processing ? (
              <>
                <svg className="animate-spin" style={{ width: '1.25rem', height: '1.25rem', animation: 'logo-spin 1s linear infinite' }} fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" opacity="0.25"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Formatting...
              </>
            ) : (
              <>
                <svg style={{ width: '1.25rem', height: '1.25rem' }} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                </svg>
                Format as {format.toUpperCase()}
              </>
            )}
          </button>

          {error && <div className="error-message">{error}</div>}
        </section>

        {result && (
          <section className="results-panel">
            <h2>Success!</h2>
            <p>Your document has been formatted successfully.</p>

            <div className="sections-list">
              <h3>Detected Sections:</h3>
              <ul>
                {result.sections_found.map((sec, i) => (
                  <li key={i}>{sec}</li>
                ))}
              </ul>
            </div>

            <a
              href={`http://127.0.0.1:5000${result.download_url}`}
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
