# GCEM Translation Evaluator - Replit Deployment Guide

## 🚀 خطوات النشر على Replit

### 1. إنشاء Repl جديد

1. اذهب إلى [Replit.com](https://replit.com)
2. اضغط "Create Repl"
3. اختر Template: **Python**
4. اسم المشروع: `gcem-evaluator`

---

### 2. رفع الملفات

رتب الملفات كالتالي:

```
gcem-evaluator/
├── app.py
├── requirements.txt
├── README.md
└── templates/
    └── index.html
```

---

### 3. إعداد المتغيرات البيئية (Secrets)

في Replit، اذهب إلى **Tools → Secrets** وأضف:

```
# اختياري - إذا أردت قاعدة بيانات
PGHOST=your-postgres-host
PGPORT=5432
PGDATABASE=gcem_db
PGUSER=postgres
PGPASSWORD=your-password
```

**ملاحظة:** قاعدة البيانات اختيارية في البداية!

---

### 4. تشغيل المشروع

في Replit Shell:

```bash
# تثبيت المكتبات
pip install -r requirements.txt

# تشغيل التطبيق
python app.py
```

أو ببساطة اضغط زر **Run** الأخضر!

---

### 5. الوصول للتطبيق

بعد التشغيل، ستحصل على رابط مثل:
```
https://gcem-evaluator.username.repl.co
```

شارك هذا الرابط مع المستخدمين! 🎉

---

## 🔑 API Key

المستخدمون يحتاجون Claude API Key:
- احصل عليه من: https://console.anthropic.com
- كل مستخدم يدخل API key الخاص به

---

## 💰 خطط التسعير المستقبلية

### النسخة الحالية (Free):
- ✅ المستخدم يدخل API key الخاص به
- ✅ لا تكاليف على السيرفر
- ✅ مثالية للاختبار

### النسخة المدفوعة (المستقبل):
- 🔐 API key مخفي في السيرفر
- 💳 اشتراك شهري: $29-$99
- 📊 Dashboard لإدارة الحسابات
- 💾 حفظ التقييمات في قاعدة بيانات

---

## 🎨 التخصيص

### تغيير الألوان:
في `templates/index.html`، عدّل:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

### إضافة شعار:
```html
<img src="your-logo.png" alt="GCEM Logo">
```

---

## 📈 التطوير المستقبلي

- [ ] إضافة قاعدة بيانات لحفظ التقييمات
- [ ] نظام حسابات المستخدمين
- [ ] تصدير النتائج إلى PDF/Excel
- [ ] API للتكامل مع أدوات أخرى
- [ ] دعم لغات إضافية

---

## 🆘 المساعدة

### مشاكل شائعة:

**1. خطأ "Module not found":**
```bash
pip install -r requirements.txt
```

**2. الواجهة لا تظهر:**
- تأكد من وجود مجلد `templates/`
- تأكد من اسم الملف: `index.html`

**3. API Key لا يعمل:**
- تحقق من صلاحية المفتاح
- تأكد من وجود رصيد في حساب Anthropic

---

## 📞 الدعم

لأي استفسارات، راسل: [your-email@example.com]

---

**تم إنشاء هذا المشروع بواسطة GCEM Team 🎓**
