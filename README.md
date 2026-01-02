---
title: AI Supplier Invoice Processing System
emoji: 🧾
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.28.0
app_file: app.py
pinned: false
license: mit
short_description: AI-powered invoice processing with analytics dashboard
tags:
  - streamlit
  - openai
  - pdf-processing
  - invoice-automation
  - analytics
  - supabase
models:
  - gpt-4o
---

# 🧾 AI Supplier Invoice Processing System

An intelligent invoice processing platform that uses AI to extract, analyze, and manage supplier data from PDF invoices.

## 🚀 Features

- **AI-Powered PDF Processing**: Extract supplier and product data from invoices using OpenAI GPT-4
- **Analytics Dashboard**: Comprehensive supplier cost analysis, price comparisons, and performance metrics
- **Contextual UI**: Smart sidebar that adapts to your current workflow
- **Currency Support**: Multi-currency handling with automatic conversion
- **Database Integration**: Supabase backend for data persistence
- **Clean Architecture**: Modular design with 28 essential components

## 📊 Analytics Features

- **Supplier Cost Analysis**: Track spending patterns and costs by supplier
- **Price Comparison**: Compare prices across different suppliers and time periods
- **Category Breakdown**: Analyze spending by product categories
- **Performance Metrics**: Monitor supplier performance and delivery trends

## 🛠️ Setup Instructions

### Environment Variables

You need to set up the following environment variables in Hugging Face Spaces settings:

```bash
# OpenAI Configuration (Required)
OPENAI_API_KEY=your-openai-api-key

# Supabase Configuration (Required)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-key

# Optional Configuration
DATABASE_ENABLED=true
```

### Getting API Keys

1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Supabase**: Create project at [Supabase](https://supabase.com) and get URL and service key

## 🎯 How to Use

1. **Upload PDFs**: Add your invoice PDFs through the upload interface
2. **AI Processing**: The system automatically extracts supplier and product data
3. **Review Data**: Verify and edit extracted information before saving
4. **Analytics**: View comprehensive analytics on the dashboard
5. **Export Data**: Download processed data for further analysis

## 🏗️ Architecture

- **Frontend**: Streamlit web application
- **AI Engine**: OpenAI GPT-4 for text extraction and processing
- **Database**: Supabase for data storage
- **File Processing**: PDF text extraction and analysis
- **Currency Management**: Multi-currency support with conversion

## 📁 Project Structure

```
├── app.py                 # Main Streamlit application
├── src/
│   ├── models/           # Data models (suppliers, products, documents)
│   ├── services/         # Core services (AI, database, PDF processing)
│   └── currency_utils.py # Currency handling utilities
├── requirements.txt      # Python dependencies
└── .env.example         # Environment variables template
```

## 🔧 Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and configure your API keys
4. Run: `streamlit run app.py`

## 📈 Analytics Dashboard

The analytics dashboard provides:
- Real-time supplier cost tracking
- Price trend analysis
- Category-wise spending breakdown
- Supplier performance metrics
- Export capabilities for further analysis

## 🔐 Security

- All API keys are externalized to environment variables
- Secure database connections through Supabase
- No sensitive data stored in code

## 📝 License

MIT License - Feel free to use and modify for your projects!