# AI Research Paper Formatter

This web application automates the formatting of research papers into standard academic styles (e.g., IEEE).

## Prerequisites
- Python 3.8+
- Node.js 14+

## Setup

### 1. Backend Setup
Navigate to the project root directory:
```bash
cd "c:/Users/gokul/OneDrive/Desktop/rishi 2"
```

Create a virtual environment and install dependencies:
```bash
python -m venv backend/venv
.\backend\venv\Scripts\pip install -r backend/requirements.txt
```

### 2. Frontend Setup
Navigate to the frontend directory:
```bash
cd frontend
npm install
```

## Running the Application

### Start the Backend API
From the project root:
```bash
.\backend\venv\Scripts\python backend/app.py
```
The server will start at `http://localhost:5000`.

### Start the Frontend Interface
Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
npm run dev
```
The application will be accessible at `http://localhost:5173`.

## Usage
1. Open the web interface.
2. Upload your raw text file (`.txt` or `.md`).
3. Select the desired template (e.g., IEEE).
4. Click "Format Document".
5. Download the resulting PDF.
