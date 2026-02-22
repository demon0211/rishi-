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
                    <p><strong>Selected File:</strong></p>
                    <p>{selectedFile.name}</p>
                    <p className="text-sm text-gray-500">Click to change</p>
                </div>
            ) : (
                <div>
                    <p><strong>Click to Upload</strong> or Drag & Drop</p>
                    <p>Supported formats: <span style={{ color: '#ef4444' }}>PDF, Word (.docx)</span></p>
                </div>
            )}
        </div>
    )
}

export default UploadArea
