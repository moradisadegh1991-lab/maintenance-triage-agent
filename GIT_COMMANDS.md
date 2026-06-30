# دستورات GitHub — گام‌به‌گام

## ۱. ساخت ریپو در GitHub

1. به github.com برو و Login کن
2. روی **"+"** بالای صفحه کلیک کن → **New repository**
3. تنظیمات:
   - **Repository name:** `maintenance-triage-agent`
   - **Description:** `LangGraph ReAct agent for petrochemical equipment failure triage`
   - **Public** (برای LinkedIn بهتر است Public باشد)
   - ❌ **Initialize with README** را تیک نزن (خودمان داریم)
4. **Create repository** بزن

---

## ۲. Push کردن از ترمینال

```bash
cd C:\Users\sadegh\AppData\Roaming\Claude\local-agent-mode-sessions\...\outputs\maintenance-triage-agent

# یا اگر فایل‌ها را کپی کرده‌ای به پوشه my_work:
cd C:\Users\sadegh\Documents\my_work\maintenance-triage-agent

# مقداردهی اولیه git
git init
git add .
git commit -m "Initial commit: LangGraph maintenance triage agent"

# اتصال به ریپو GitHub (URL ریپوی خودت را جایگزین کن)
git remote add origin https://github.com/YOUR_USERNAME/maintenance-triage-agent.git

# push
git branch -M main
git push -u origin main
```

---

## ۳. اضافه کردن تصاویر به ریپو

تصاویر LinkedIn را به‌صورت Screenshot از مرورگر ذخیره کن (PNG با ابعاد 1200×628) و در پوشه `images/` قرار بده:

```bash
# بعد از اضافه کردن فایل‌های PNG به پوشه images/
git add images/
git commit -m "Add LinkedIn cover images"
git push
```

---

## ۴. تنظیمات نهایی GitHub

بعد از push:
- **About** (گوشه راست ریپو): توضیحات + topic های `langgraph`, `predictive-maintenance`, `agentic-ai`, `petrochemical` را اضافه کن
- **README** را پیش‌نمایش کن تا همه چیز درست نمایش داده شود
- URL ریپو را در پست LinkedIn اضافه کن
