# 🚀 Hugging Face Spaces Deployment Guide

## Quick Deployment Steps

### 1. Create a New Space on Hugging Face

1. Go to [Hugging Face Spaces](https://huggingface.co/new-space)
2. Fill in the details:
   - **Owner**: Your Hugging Face username
   - **Space name**: `ai-supplier-invoice-processor` (or your preferred name)
   - **License**: MIT
   - **Select the SDK**: Streamlit
   - **Hardware**: CPU Basic (free tier)
   - **Visibility**: Public or Private (your choice)

### 2. Clone and Configure the Space

```bash
# Clone your new space (replace with your actual space URL)
git clone https://huggingface.co/spaces/YOUR_USERNAME/ai-supplier-invoice-processor
cd ai-supplier-invoice-processor

# Add this repository as a remote and pull the code
git remote add supplier-app https://github.com/rahul6000/SUPPLIERS.git
git pull supplier-app main --allow-unrelated-histories
```

### 3. Set Up Environment Variables

In your Hugging Face Space settings, add these environment variables:

**Required Variables:**
```
OPENAI_API_KEY = your-openai-api-key-here
SUPABASE_URL = https://your-project.supabase.co
SUPABASE_KEY = your-supabase-service-key-here
```

**Optional Variables:**
```
DATABASE_ENABLED = true
```

### 4. Push to Your Space

```bash
git add .
git commit -m "Deploy AI Supplier Invoice Processing System"
git push origin main
```

## 🔑 Getting API Keys

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Copy the key (starts with `sk-proj-...`)

### Supabase Configuration
1. Go to [Supabase](https://supabase.com)
2. Create a new project
3. Go to Settings → API
4. Copy:
   - **URL**: Your project URL
   - **Service Role Key**: Your service key (not the anon key)

## 🎯 Alternative: Direct Git Push

If you prefer to push directly from this repository:

```bash
# Add your Hugging Face Space as a remote
git remote add huggingface https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME

# Push to Hugging Face
git push huggingface main
```

## ✅ Verification

Once deployed, your app will be available at:
`https://huggingface.co/spaces/YOUR_USERNAME/SPACE_NAME`

The app should:
- Display the Streamlit interface
- Show both "🧾 Invoice Processing" and "📊 Analytics Dashboard" buttons
- Allow PDF uploads
- Display analytics when configured with API keys

## 🔧 Troubleshooting

**App won't start?**
- Check the logs in your Hugging Face Space
- Ensure all environment variables are set correctly
- Verify your API keys are valid

**Database errors?**
- Check your Supabase project is active
- Verify the SUPABASE_URL and SUPABASE_KEY are correct
- Ensure your database has the required tables (use database_schema.sql)

**AI extraction not working?**
- Verify your OpenAI API key is valid and has credits
- Check the OpenAI usage limits

## 📊 Features Available After Deployment

✅ PDF Invoice Upload and Processing
✅ AI-Powered Data Extraction  
✅ Supplier and Product Management
✅ Analytics Dashboard
✅ Cost Analysis and Reporting
✅ Multi-Currency Support
✅ Data Export Capabilities

Your AI-powered invoice processing system will be live and ready to use! 🎉