# 🔐 Streamlit Cloud Configuration Guide

## Adding Snowflake Credentials to Streamlit Cloud

1. **Go to your Streamlit Cloud dashboard**
   - Visit: https://share.streamlit.io/
   - Select your app: `StockPulse-AI`

2. **Open App Settings**
   - Click the menu (⋮) next to your app
   - Select "Settings"

3. **Add Secrets**
   - Go to the "Secrets" section
   - Paste the following configuration:

```toml
SNOWFLAKE_ACCOUNT = "FA76495.ap-south-1"
SNOWFLAKE_USERNAME = "Yash151005"
SNOWFLAKE_PASSWORD = "Yash@1234512345"
SNOWFLAKE_WAREHOUSE = "STOCKPULSE_WH"
SNOWFLAKE_DATABASE = "STOCKPULSE_AI"
SNOWFLAKE_ROLE = "STOCKPULSE_USER"
```

4. **Save and Reboot**
   - Click "Save"
   - Your app will automatically restart with the new credentials

## Local Development

For local development, keep using your `.env` file (already configured).

## Security Notes

- ✅ Secrets are encrypted on Streamlit Cloud
- ✅ Never commit secrets to GitHub
- ✅ `.env` and `secrets.toml` are in `.gitignore`
- ⚠️ Change passwords regularly for production use
