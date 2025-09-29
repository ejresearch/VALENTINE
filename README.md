# Screenplay Formatter

A comprehensive Python tool that automatically converts raw text into properly formatted screenplays following industry standards. Includes both a modern web interface and CLI tools.

**Developed by YT Research LLC**

## Features

### Web Application
- **Modern Web Interface**: Clean, minimalistic UI with light/dark mode support
- **Drag & Drop Upload**: Easy file upload with visual feedback
- **Real-time Processing**: Live progress updates during formatting
- **Multiple Format Export**: Download as .txt, .docx, or .pdf
- **Three Formatting Modes**:
  - Standard Format: Professional formatting for well-structured scripts
  - AI-Powered Fix: Automatic correction of formatting issues
  - Smart Format: Auto-detect and apply best formatting method
- **Private Processing**: All files processed locally - content stays private
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Theme Support**: Light and dark mode with persistent preferences

### Core Features
- **Multiple Output Formats**: Plain text, DOCX, and PDF
- **Industry-Standard Formatting**: Follows standard screenplay formatting rules
  - Courier 12pt font
  - Proper margins (1.5" left, 1" right/top/bottom)
  - Correct indentation for dialogue, parentheticals, and transitions
- **Smart Parsing**: Automatically detects screenplay elements
- **Validation**: Built-in validator to ensure proper formatting
- **LLM Post-Processing**: Optional AI-powered correction for formatting errors (OpenAI API)
- **CLI Interface**: Easy-to-use command-line tool

## Installation

```bash
pip install -e .
```

## Usage

### Web Application

1. **Start the web server**:
```bash
python webapp/app.py
```

2. **Open your browser** to `http://127.0.0.1:5001`

3. **Upload your screenplay** (.txt file with screenplay content)

4. **Configure options**:
   - Choose formatting mode (Standard, AI-Powered Fix, or Smart Format)
   - Select output formats (Text, Word Document, PDF)
   - Configure AI settings (optional OpenAI API key for AI corrections)
   - Set confidence threshold for AI corrections

5. **Process and download** your formatted screenplay

**Web Interface Features**:
- Theme toggle (light/dark mode) in the top-right of the sidebar
- Drag & drop file upload
- Live processing progress
- Multiple file format downloads
- Audit log generation (optional)

### Command Line Interface

#### Basic Text Formatting
```bash
screenplay-format format input.txt output.txt
```

#### Generate DOCX
```bash
screenplay-format format input.txt output.docx --format docx
```

#### Generate PDF
```bash
screenplay-format format input.txt output.pdf --format pdf
```

#### Validate Screenplay
```bash
screenplay-format validate screenplay.txt
```

#### Fix with LLM (requires API key)
```bash
screenplay-format fix screenplay.txt --output fixed.txt
```

## Screenplay Elements

The formatter recognizes and properly formats:
- **Scene Headings**: INT./EXT. LOCATION - TIME
- **Action Lines**: Description of what's happening
- **Character Names**: Centered, ALL CAPS
- **Dialogue**: Properly indented conversation
- **Parentheticals**: Acting directions in parentheses
- **Transitions**: CUT TO:, FADE OUT., etc.

## Example Input

```
INT. COFFEE SHOP - DAY

The bustling coffee shop is filled with the morning rush. SARAH (30s, professional attire) enters, scanning the room.

SARAH
(to barista)
Large coffee, black please.

BARISTA
Coming right up!

CUT TO:
```

## Configuration

### OpenAI API Key (Optional)
For AI-powered formatting corrections, you can provide an OpenAI API key:
- **Web Interface**: Enter your API key in the sidebar and click "Save"
- **CLI**: Set the `OPENAI_API_KEY` environment variable

The API key is stored locally in your browser's localStorage (web) or environment variables (CLI).

### AI Settings
- **Dry Run**: Preview AI corrections without applying them
- **Generate Audit Log**: Create detailed logs of all AI corrections
- **Confidence Threshold**:
  - Low (0.6): More aggressive corrections
  - Medium (0.8): Balanced approach (recommended)
  - High (0.9): Conservative, only high-confidence fixes

## Development

### Project Structure
```
screenplay_formatter/
├── src/                    # Core Python package
│   └── screenplay_formatter/
├── webapp/                 # Web application
│   ├── app.py             # Flask server
│   ├── index.html         # Web interface
│   └── logo.png           # Branding
├── tests/                 # Test suite
└── requirements.txt       # Dependencies
```

### Run Web Server (Development)
```bash
python webapp/app.py
```

### Run Tests
```bash
pytest tests/
```

### Format Code
```bash
black src/ tests/
ruff check src/ tests/
```

### Type Checking
```bash
mypy src/
```

## Design

The web interface features a modern, minimalistic design with:
- **Color Palette**: Clean blues (#5b7fff) with neutral grays
- **Light Mode**: White backgrounds with subtle gray accents
- **Dark Mode**: True black backgrounds (#0f0f0f, #1a1a1a) with high contrast
- **Typography**: System fonts for optimal performance and readability
- **Animations**: Smooth transitions and micro-interactions

## License

MIT License

---

**Developed by YT Research LLC**