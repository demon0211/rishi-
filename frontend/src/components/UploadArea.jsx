import { useRef } from 'react'

function UploadArea({ onFileSelect, selectedFile }) {
    const fileInputRef = useRef(null)

    const handleClick = () => {
        fileInputRef.current.click()
    }

    const handleChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            onFileSelect(e.target.files[0])
        }
    }

    const handleDragOver = (e) => {
        e.preventDefault()
    }

    const handleDrop = (e) => {
        e.preventDefault()
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            onFileSelect(e.dataTransfer.files[0])
        }
    }

    return (
        <div
            className={`upload-area ${selectedFile ? 'active' : ''}`}
            onClick={handleClick}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
        >
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleChange}
                style={{ display: 'none' }}
                accept=".pdf,.docx"
            />

            {selectedFile ? (
                <div>
                    <svg className="upload-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p style={{ fontWeight: 600, fontSize: '1.05rem', color: 'var(--primary-color)' }}>{selectedFile.name}</p>
                    <p className="text-muted">Click to change file</p>
                </div>
            ) : (
                <div>
                    <svg className="upload-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                    </svg>
                    <p><strong>Click to Upload</strong> or Drag & Drop</p>
                    <p className="text-muted">Supported formats: <span style={{ color: 'var(--primary-color)' }}>PDF, Word (.docx)</span></p>
                </div>
            )}
        </div>
    )
}

export default UploadArea
