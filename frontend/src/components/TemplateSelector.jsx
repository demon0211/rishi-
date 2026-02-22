function TemplateSelector({ selected, onSelect, selectedFormat, onSelectFormat }) {
    const templates = [
        { id: 'IEEE', name: 'IEEE Standard' },
        { id: 'ACM', name: 'ACM Conference' },
        { id: 'Springer', name: 'Springer Lecture Notes' }
    ]

    return (
        <div className="template-selector-container">
            <div className="template-selector">
                <label htmlFor="template-select">Formatting Style:</label>
                <select
                    id="template-select"
                    value={selected}
                    onChange={(e) => onSelect(e.target.value)}
                >
                    {templates.map(t => (
                        <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                </select>
            </div>

            <div className="format-selector" style={{ marginTop: '1rem' }}>
                <label>Output Format:</label>
                <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                        <input
                            type="radio"
                            name="format"
                            value="pdf"
                            checked={selectedFormat === 'pdf'}
                            onChange={(e) => onSelectFormat(e.target.value)}
                        />
                        PDF Document
                    </label>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
                        <input
                            type="radio"
                            name="format"
                            value="docx"
                            checked={selectedFormat === 'docx'}
                            onChange={(e) => onSelectFormat(e.target.value)}
                        />
                        Word Document (.docx)
                    </label>
                </div>
            </div>
        </div>
    )
}

export default TemplateSelector
