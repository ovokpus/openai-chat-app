# 🚀 OpenAI Chat App with RAG Superpowers! 

Hey there, awesome developer! 👋 Welcome to our super-cool chat application that's not just your average chatbot - it's a document-devouring, context-understanding AI assistant! 

## ✨ What Makes This App Special?

- 🤖 Powered by OpenAI's latest models
- 📚 RAG (Retrieval-Augmented Generation) capabilities
- 📄 Multi-format document support (PDF, DOCX, TXT, MD, CSV)
- 🎨 Beautiful, responsive UI with real-time updates
- 🔄 Smart session management
- 🎯 Toggle between regular chat and RAG mode

## 🛠️ Tech Stack

- **Frontend**: React + TypeScript + Vite 🏗️
- **Backend**: Flask + Python 🐍
- **AI**: OpenAI API 🤖
- **Deployment**: Vercel 🚀

## 🏃‍♂️ Quick Start

### Local Development

1. **Clone this bad boy:**
   ```bash
   git clone https://github.com/yourusername/openai-chat-app.git
   cd openai-chat-app
   ```

2. **Set up the backend:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r api/requirements.txt
   ```

3. **Fire up the frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Start the backend server:**
   ```bash
   cd api
   python app.py
   ```

5. **Add your magic (API key):**
   - Create a `.env` file in the `api` directory
   - Add your OpenAI API key: `OPENAI_API_KEY=your-key-here`

### 🚀 Deployment to Vercel

Ready to show your creation to the world? Let's deploy this beast to Vercel! 

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to your Vercel account:**
   ```bash
   vercel login
   ```

3. **Deploy to the cloud:**
   ```bash
   vercel
   ```

4. **Set up your environment variables:**
   - Head to the Vercel dashboard
   - Find your project
   - Go to Settings > Environment Variables
   - Add `OPENAI_API_KEY` with your API key
   - Add `PYTHONPATH=.`

5. **Verify your deployment:**
   - Check the deployment URL
   - Test document upload
   - Verify RAG functionality
   - Monitor performance

### 🔍 Post-Deployment Checklist

- [ ] API endpoints responding correctly
- [ ] Document upload working
- [ ] RAG mode functioning
- [ ] UI looking fresh and clean
- [ ] Environment variables set
- [ ] Error tracking enabled
- [ ] Analytics configured

## 🎮 Features

### Document Chat
Upload your documents and chat with them! The app supports:
- 📄 PDFs
- 📝 Word documents
- ✍️ Text files
- 📊 CSV files
- 📋 Markdown files

### RAG Mode
Toggle between:
- 🎯 Regular chat mode
- 📚 RAG mode (chat with your documents)

### Smart UI
- 🎨 Beautiful, responsive design
- ⚡ Real-time updates
- 📱 Mobile-friendly
- 🔄 Clear loading states
- 🗑️ Document management

## 🤝 Contributing

Got ideas? We'd love to hear them! Here's how you can help make this app even more awesome:

1. Fork it! 🍴
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Submit a pull request 🎉

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙌 Acknowledgments

- OpenAI for their amazing API
- The awesome open-source community
- Coffee ☕ - lots and lots of coffee

## 🐛 Troubleshooting

### Common Issues

1. **API Key Issues:**
   ```
   Error: OpenAI API key not found
   ```
   ➡️ Make sure your API key is set in the environment variables!

2. **Upload Problems:**
   ```
   Error: File too large
   ```
   ➡️ Check your file size (max 10MB) and format!

3. **RAG Not Working:**
   - Verify document upload success
   - Check RAG mode toggle
   - Confirm API key permissions

Need more help? Open an issue! We're here to help! 🤗

---

Made with ❤️ by developers, for developers!
