"""
تست مستقل کلید API - بدون LangGraph / LangChain
اگر این اسکریپت هم خطای 401 بدهد، مشکل قطعاً خود کلید است نه کد عامل.
اجرا: python test_api_key.py
"""
import os
from dotenv import load_dotenv

load_dotenv()

key = os.environ.get("ANTHROPIC_API_KEY", "")
print(f"طول کلید خوانده‌شده: {len(key)} کاراکتر")
print(f"شروع کلید: {key[:15]}...")
print(f"آیا فاصله/خط جدید اضافه دارد؟ {key != key.strip()}")

import anthropic

client = anthropic.Anthropic(api_key=key.strip())

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=50,
    messages=[{"role": "user", "content": "فقط بنویس: تست موفق بود"}],
)
print("\nپاسخ مدل:", response.content[0].text)
