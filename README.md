# CineMorph AI - Intelligent Multilingual Movie Dubbing Platform

**AI-powered cinematic localization platform for natural conversational movie dubbing**

[![Status](https://img.shields.io/badge/status-MVP-success)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 🎬 Overview

CineMorph AI transforms movies and videos into any language using advanced AI dubbing with:
- Natural native-language cinematic dubbing
- Human-like conversational dialogues
- Region-specific speaking style adaptation
- Emotional voice synchronization
- Seamless movie watching experience

---

## ✨ Features

### Core Functionality
- 🎥 **Video Upload**: Drag-and-drop support for MP4, MKV, AVI formats
- 🗣️ **AI Dubbing**: Automated speech recognition, translation, and voice generation
- 🌍 **Multi-Language**: Support for Tamil, Telugu, Malayalam, Kannada, Hindi, English, Spanish, French, German, Japanese, Korean, Chinese, Arabic, Portuguese, Russian
- 🎬 **Video Preview**: Built-in player with play/pause, volume, progress bar, fullscreen
- 📥 **Download**: Download dubbed movies in original quality
- 📊 **Analytics**: Track processing jobs, costs, and usage statistics

### User Experience
- 🔐 Google OAuth authentication (via Emergent)
- 💳 Cost estimation before processing
- 🎯 Real-time processing progress tracking
- 🗑️ Delete movies and dubbing jobs
- 📱 Responsive mobile-friendly design
- 🌙 Dark cinematic Netflix-inspired UI

---

## 🏗️ Tech Stack

### Frontend
- **React** - UI framework
- **Tailwind CSS** - Styling
- **Framer Motion** - Animations
- **Shadcn UI** - Component library
- **Axios** - HTTP client

### Backend
- **FastAPI** - Python web framework
- **MongoDB** (Motor) - Async database
- **Emergent Integrations** - AI services (Whisper, GPT-4o, TTS)
- **FFmpeg** - Video/audio processing
- **Pydub** - Audio manipulation

### AI Services (via Emergent LLM Key)
- **OpenAI Whisper** - Speech-to-text transcription
- **GPT-4o** - Conversational translation
- **OpenAI TTS** - Voice generation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- MongoDB
- FFmpeg

### Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your configuration

# Run backend
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
yarn install

# Configure environment
cp .env.example .env
# Edit .env with backend URL

# Run frontend
yarn start
```

### Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

---

## 📁 Project Structure

```
cinemorph-ai/
├── backend/
│   ├── server.py              # Main FastAPI application
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables
│   └── storage/              # Video storage
│       ├── uploads/          # Original videos
│       ├── processed/        # Dubbed videos
│       └── temp/             # Temporary files
│
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── contexts/        # React contexts
│   │   ├── App.js           # Main app component
│   │   └── index.js         # Entry point
│   ├── package.json         # Node dependencies
│   └── .env                 # Frontend config
│
├── design_guidelines.json    # UI/UX specifications
├── auth_testing.md          # Authentication guide
└── README.md               # This file
```

---

## 🔧 Configuration

### Backend Environment Variables

```bash
# Database
MONGO_URL=mongodb://localhost:27017
DB_NAME=cinemorph_ai

# AI Processing
AI_MODE=mock  # Options: 'mock' or 'real'

# Cost Limits (INR)
ENABLE_COST_LIMITS=true
DAILY_COST_LIMIT_INR=200.00
PER_VIDEO_COST_LIMIT_INR=50.00
MONTHLY_COST_BUDGET_INR=500.00

# Video Duration Limits (seconds)
MIN_VIDEO_DURATION=10
MAX_VIDEO_DURATION=120

# OpenAI TTS
OPENAI_TTS_MODEL=tts-1
OPENAI_TTS_VOICE=nova

# CORS
CORS_ORIGINS=http://localhost:3000
```

### Frontend Environment Variables

```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## 💰 Cost Estimation

### Per-Minute Processing Cost (with Emergent LLM Key)

| Service | Cost (INR) |
|---------|------------|
| Whisper (Speech-to-text) | ₹0.50 |
| GPT-4o (Translation) | ₹2.50 |
| OpenAI TTS (Voice) | ₹1.25 |
| **Total** | **₹4.25/min** |

### Example Costs
- 30-second clip: ₹2.12
- 1-minute clip: ₹4.25
- 5-minute clip: ₹21.25

---

## 🧪 Testing

### Run Backend Tests
```bash
cd backend
pytest tests/
```

### Run Frontend Tests
```bash
cd frontend
yarn test
```

### Manual Testing
1. Upload a test video (30 seconds recommended)
2. Select target language (e.g., Tamil)
3. Review cost estimate
4. Start dubbing process
5. Monitor progress in Jobs page
6. Preview dubbed video
7. Download result

---

## 📖 API Documentation

### Key Endpoints

#### Authentication
- `POST /api/auth/session` - Exchange session ID
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

#### Movies
- `POST /api/movies/upload` - Upload video
- `GET /api/movies` - List user's movies
- `GET /api/movies/{id}/stream` - Stream video
- `DELETE /api/movies/{id}` - Delete movie

#### Dubbing
- `POST /api/dubbing/create` - Create dubbing job
- `GET /api/dubbing/jobs` - List jobs
- `GET /api/dubbing/{id}` - Get job status
- `GET /api/dubbing/{id}/stream` - Stream dubbed video
- `GET /api/dubbing/{id}/download` - Download dubbed video
- `DELETE /api/dubbing/{id}` - Delete job

#### Analytics
- `GET /api/analytics/user` - User statistics
- `GET /api/languages` - Supported languages

Full API documentation: http://localhost:8001/docs

---

## 🌍 Supported Languages

### South Indian Languages (Primary)
- தமிழ் Tamil
- తెలుగు Telugu  
- മലയാളം Malayalam
- ಕನ್ನಡ Kannada

### Other Languages
- हिन्दी Hindi
- English
- Español Spanish
- Français French
- Deutsch German
- 日本語 Japanese
- 한국어 Korean
- 中文 Chinese
- العربية Arabic
- Português Portuguese
- Русский Russian

---

## 🎯 Roadmap

### Current (MVP)
- ✅ Mock AI dubbing pipeline
- ✅ Video upload and management
- ✅ Cost estimation and tracking
- ✅ Video preview and playback

### Phase 1 (In Progress)
- 🔄 Real AI integration (Whisper + GPT-4o + TTS)
- 🔄 Conversational translation (cinema-style Tamil)
- 🔄 Cost management and limits

### Phase 2 (Planned)
- 📋 User payment system
- 📋 Batch processing
- 📋 Voice cloning
- 📋 Subtitle generation
- 📋 Advanced analytics

### Phase 3 (Future)
- 📋 ElevenLabs integration (premium voices)
- 📋 Lip-sync alignment (Wav2Lip)
- 📋 Multi-speaker detection
- 📋 Background music preservation
- 📋 Full-length movie support (2+ hours)

---

## 🛡️ Security

- 🔒 Google OAuth authentication
- 🔒 httpOnly cookies for sessions
- 🔒 CORS protection
- 🔒 File upload validation
- 🔒 Cost limits enforcement
- 🔒 User data isolation

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **Emergent AI** - LLM key and AI integrations
- **OpenAI** - Whisper, GPT-4o, TTS services
- **Shadcn UI** - Beautiful component library
- **FFmpeg** - Video processing

---

## 📞 Support

For issues and questions:
- 📧 Email: support@your-domain.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/cinemorph-ai/issues)
- 📖 Docs: [Documentation](https://docs.your-domain.com)

---

**Built with ❤️ for cinematic localization**
