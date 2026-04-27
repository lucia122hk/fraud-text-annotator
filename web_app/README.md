# Fraud Text Annotation System

A web-based system for annotating fraud-related text with 16 labels and generating time series labels.

## Features

- **16label Annotation**: Annotate fraud text with 16 detailed labels
- **Time Series Generation**: Generate time series labels based on the annotation results
- **File Upload**: Support for uploading CSV and Excel files for batch processing
- **Drag & Drop**: Easy file upload via drag and drop
- **API Configuration**: Save API configuration for future use
- **Results Download**: Download annotation results as CSV file

## Project Structure

```
fraud_annotation_system/
├── backend/           # Backend server (Flask)
│   └── app.py         # Main backend code
├── frontend/          # Frontend files
│   └── final.html     # Main frontend page
├── requirements.txt   # Python dependencies
├── start_backend.sh   # Backend startup script
├── start_frontend.sh  # Frontend startup script
└── README.md          # This file
```

## Setup

### Prerequisites

- Python 3.7+
- Internet connection for API calls

### Installation

1. **Clone or download** this repository to your local machine.

2. **Navigate** to the project directory:
   ```bash
   cd fraud_annotation_system
   ```

3. **Make scripts executable**:
   ```bash
   chmod +x start_backend.sh start_frontend.sh
   ```

## Usage

### 1. Start Backend Server

Run the backend startup script:

```bash
./start_backend.sh
```

This script will:
- Create a virtual environment (if not exists)
- Install required dependencies
- Start the backend server on `http://localhost:5001`

### 2. Start Frontend Server

Open a new terminal window and run:

```bash
./start_frontend.sh
```

This will start the frontend server on `http://localhost:8000`

### 3. Access the System

Open your web browser and go to `http://localhost:8000/final.html`

### 4. Configure API

1. Enter your API key in the "API Configuration" section
2. Click "Save Configuration" to save your settings

### 5. Annotate Text

- **Single Text**: Enter fraud text and click "Start Annotation"
- **Batch File**: Upload a CSV/Excel file or drag and drop it into the drop zone

### 6. Download Results

After annotation, click "Download Results" to get the annotated data as a CSV file.

## File Format Requirements

- **Supported formats**: CSV, Excel (.xlsx)
- **Structure**: First column should contain the text content
- **Limit**: Maximum 1000 rows per file

## API Configuration

- **API Key**: Your API key for the language model
- **API URL**: Default: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **Model Name**: Default: `qwen-plus`

## Technical Details

- **Backend**: Flask-based API server
- **Frontend**: HTML5 with JavaScript
- **API**: Uses OpenAI-compatible API
- **Data Processing**: Pandas for file handling

## Troubleshooting

- **API Connection Error**: Check your API key and internet connection
- **File Upload Error**: Ensure your file is in the correct format
- **Server Issues**: Make sure both backend and frontend servers are running

## License

MIT
