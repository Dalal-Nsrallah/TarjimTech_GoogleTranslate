#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
#  TARJIMTECH INTEL TERMINAL
#  كيف كشف غوغل ترانسليت عميلاً روسياً
#  دلال نصرالله — ترجمتك للتقنية — 2026
# ─────────────────────────────────────────────────────────────

import time, sys, random, unicodedata
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn
from rich.prompt import Prompt
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from rich import box
from rich.markup import escape

console = Console()

def normalize_arabic(text):
    """Normalize all Arabic character variants from Mac keyboard."""
    import unicodedata
    text = unicodedata.normalize('NFC', text)
    # Hamza variants → standard
    text = text.replace('أ', 'ا')  # أ → ا
    text = text.replace('إ', 'ا')  # إ → ا
    text = text.replace('آ', 'ا')  # آ → ا
    text = text.replace('ؤ', 'و')  # ؤ → و
    text = text.replace('ئ', 'ي')  # ئ → ي
    # Taa marbuta → haa
    text = text.replace('ة', 'ه')  # ة → ه
    # Alef maqsura → yaa
    text = text.replace('ى', 'ي')  # ى → ي
    return text.strip()


G  = "bright_green"
G2 = "green"
R  = "bright_red"
A  = "yellow"
W  = "white"
D  = "grey50"

ALL_CMDS = [
    "مساعده","تشغيل","الحادثه","المشتبه",
    "نظام","الزاحف","بياناتك","الثغره",
    "FBI","الدروس","ادوات",
    "عن","مسح","خروج"
]

def stagger(lines, gap=0.07):
    for ln in lines:
        if isinstance(ln, tuple):
            console.print(ln[0], highlight=False)
        else:
            console.print(ln, highlight=False)
        time.sleep(gap)

def hr(color=G2):
    console.print(Rule(style=color))

def blank():
    console.print()

def prog_bar(label, duration=1.2, steps=40):
    with Progress(
        TextColumn(f"  [green]{label}[/green]"),
        BarColumn(bar_width=30, style="green", complete_style="bright_green"),
        TextColumn("[bright_green]{task.percentage:>3.0f}%[/bright_green]"),
        console=console,
        transient=False,
    ) as p:
        t = p.add_task("", total=steps)
        for _ in range(steps):
            time.sleep(duration / steps)
            p.advance(t)

def glitch(text, times=3):
    chars = "!@#$%^&*<>?/|\\[]{}~"
    for _ in range(times):
        scrambled = "".join(
            random.choice(chars) if random.random() < 0.4 else c
            for c in text
        )
        console.print(f"\r  [bright_red]{scrambled}[/bright_red]", end="")
        time.sleep(0.06)
    console.print(f"\r  [bright_red]{text}[/bright_red]")

def panel(content, title="", style=G2, padding=(1,2)):
    console.print(Panel(content, title=title, border_style=style, padding=padding))

# ── COMMANDS ──────────────────────────────────────────────

def cmd_help():
    t = Table(show_header=False, box=box.SIMPLE, padding=(0,1))
    t.add_column(style=G, no_wrap=True)
    t.add_column(style=D)
    rows = [
        ("تشغيل",    "ابدأ من هنا — يفتح ملف القضية مع شرائط التحميل"),
        ("الحادثة",  "القصة كاملةً من البداية حتى الاعتقال"),
        ("المشتبه",  "ملف تعريفي بالضابط الروسي دينيس أليموف"),
        ("نظام",      "كيف يعمل Google Translate من الداخل — نظامان"),
        ("الزاحف",   "شاهد الزاحف وهو يجمع البيانات من الإنترنت"),
        ("بياناتك",  "اكتشف ما يحتفظ به غوغل عنك في كل مرة تترجم"),
        ("الثغرة",   "لماذا لم ينجح التشفير في حماية الجاسوس"),
        ("FBI",       "كيف تتبّع الـ FBI خطواته خطوةً بخطوة"),
        ("الدروس",   "خمسة دروس يجب أن يعرفها كل مترجم"),
        ("أدوات",   "بدائل آمنة لغوغل ترانسليت — مقارنة شاملة"),
        ("عن",       "من وراء هذا المحتوى التعليمي"),
        ("مسح",      "مسح الشاشة"),
        ("خروج",     "الخروج من البرنامج"),
    ]
    for cmd, desc in rows:
        t.add_row(cmd, desc)
    panel(t, title="[bright_green] الأوامر المتاحة [/bright_green]")
    blank()

def cmd_boot():
    console.print(f"\n  [grey50]جارٍ فتح ملف القضية...[/grey50]")
    blank()
    prog_bar("تحميل وثائق القضية  CENTER-795-2026 ", 1.0)
    prog_bar("فك تشفير سجلات الترجمة             ", 0.8)
    prog_bar("رسم مسار المراقبة                  ", 0.7)
    prog_bar("تحليل الشبكة                       ", 0.6)
    blank()
    time.sleep(0.3)
    glitch("النظام مخترَق...")
    time.sleep(0.2)
    console.print(f"\r  [bright_green]✓ الملف جاهز للاطلاع[/bright_green]")
    blank()

    t = Table(show_header=False, box=box.SIMPLE_HEAD, padding=(0,2), border_style="grey23")
    t.add_column(style=D, no_wrap=True)
    t.add_column(style=W)
    t.add_row("رقم القضية",  "[yellow]CENTER-795-2026[/yellow]")
    t.add_row("المتهم",      "[bright_red]دينيس أليموف — ضابط استخبارات روسي[/bright_red]")
    t.add_row("الوحدة",      "[bright_red]المركز 795 — هيئة الأركان العامة الروسية[/bright_red]")
    t.add_row("الغطاء",      "شركة كلاشنيكوف — مجمع باتريوت خارج موسكو")
    t.add_row("نقطة الضعف",  "[yellow]غوغل ترانسليت — نصوص مكشوفة على خوادم أمريكية[/yellow]")
    t.add_row("مكان الاعتقال","مطار بوغوتا الدولي، كولومبيا")
    t.add_row("تاريخ الاعتقال","[bright_red]24 فبراير 2026[/bright_red]")
    t.add_row("الوضع الحالي", "[bright_red]موقوف — بانتظار التسليم للولايات المتحدة[/bright_red]")
    panel(t, title="[yellow] ملف القضية [/yellow]", style="yellow")
    blank()

def cmd_incident():
    panel(
        "[bold bright_green]القصة الكاملة — كيف انكشف الجاسوس[/bold bright_green]\n"
        "[grey50]محتوى تعليمي · قضية CENTER-795-2026[/grey50]",
        style=G2
    )
    blank()
    events = [
        ("ديسمبر 2022", G, "روسيا تؤسس وحدة سرية من النخبة", [
            "بأمر مباشر من هيئة الأركان العامة، أُنشئت وحدة استخباراتية سرية للغاية.",
            "وُضعت تحت غطاء شركة كلاشنيكوف للأسلحة في مجمع باتريوت.",
            "ضمّت نحو 500 ضابط من خيرة عناصر الـ FSB والـ GRU والحرس الوطني.",
            "مهمتها: تنفيذ اغتيالات واختطاف ومهام تخريبية خارج روسيا.",
            "رئيسها يتقاضى ما يزيد على نصف مليون دولار سنوياً.",
        ]),
        ("2025 — 2026", A, "مهمة: اغتيال معارضَين شيشانيَّين في أوروبا", [
            "كُلِّف الضابط دينيس أليموف بتنفيذ عملية اغتيال داخل أوروبا.",
            "جنّد منفّذاً من خارج روسيا: داركو دوروفيتش، صربي-كرواتي مقيم في أمريكا.",
            "عرض عليه مليوناً ونصف المليون دولار مقابل كل هدف.",
            'المطلوب: "ترحيل المعارض إلى روسيا" — حياً كان أم ميتاً.',
        ]),
        ("نقطة التحول", R, "حاجز لغوي يقلب المعادلة", [
            "أليموف ودوروفيتش لا يتكلمان أي لغة مشتركة.",
            "اختارا تطبيقاً مشفَّراً للتواصل — وهذا صواب.",
            "لكنهما كانا ينسخان كل رسالة ويلصقانها في غوغل ترانسليت للترجمة.",
            "هذه الخطوة البسيطة وحدها كانت كافيةً لتدمير العملية بالكامل.",
        ]),
        ("فبراير 2026", G, "الـ FBI يحصل على إذن المراقبة", [
            "رصد الـ FBI استخدام غوغل ترانسليت في تلك المراسلات.",
            "استصدر أمر مراقبة قضائياً وفق قانون ECPA الأمريكي.",
            "غوغل ملزَم قانوناً بتسليم سجلات الترجمة عند الطلب.",
            "بات الـ FBI يطّلع على كل رسالة بينهما في الوقت الفعلي.",
        ]),
        ("24 فبراير 2026", R, "الاعتقال في مطار بوغوتا", [
            "أُوقف أليموف في مطار إيل دورادو الدولي بكولومبيا.",
            "وُجِّهت إليه تهم التآمر على الاختطاف والقتل وتمويل الإرهاب.",
            "يواجه السجن المؤبد إن صدر بحقه حكم إدانة.",
        ]),
    ]
    for date, col, title, details in events:
        console.print(f"  [{col}]● {date}[/{col}]  [{W}]{title}[/{W}]", highlight=False)
        for d in details:
            console.print(f"           [grey50]{d}[/grey50]", highlight=False)
            time.sleep(0.06)
        blank()
        time.sleep(0.1)

    panel(
        '[yellow]"الوحدة الأكثر سرية في الاستخبارات العسكرية الروسية\nلم تنكشف بسبب مخبر أو عميل مزروع —\nبل بسبب حاجز لغوي وأمر مراقبة"[/yellow]\n[grey50]— The Insider، مارس 2026[/grey50]',
        style="yellow"
    )

def cmd_suspect():
    t = Table(show_header=False, box=box.SIMPLE, padding=(0,2))
    t.add_column(style=D, no_wrap=True)
    t.add_column()
    t.add_row("الاسم",        "[bold white]دينيس أليموف / Denis Alimov[/bold white]")
    t.add_row("الوحدة",       "[bright_red]المركز 795 — مديرية الاستخبارات[/bright_red]")
    t.add_row("الغطاء",       "موظف في شركة كلاشنيكوف للأسلحة")
    t.add_row("قائده",        "دينيس فيسنكو — ضابط سابق في مجموعة ألفا")
    t.add_row("","")
    t.add_row("المهمة",       "[yellow]اغتيال معارضَين شيشانيَّين مقيمَين في أوروبا[/yellow]")
    t.add_row("المنفّذ",      "داركو دوروفيتش — صربي-كرواتي مقيم في أمريكا")
    t.add_row("المكافأة",     "[bright_red]مليون ونصف دولار لكل هدف — حياً أو ميتاً[/bright_red]")
    t.add_row("","")
    t.add_row("الخطأ",        "[bright_red]لا لغة مشتركة بينه وبين منفّذ العملية[/bright_red]")
    t.add_row("",             "[bright_red]لجأ إلى غوغل ترانسليت فخلّف أثراً نصياً كاملاً[/bright_red]")
    t.add_row("","")
    t.add_row("وضعه الآن",    "[bold bright_red]موقوف — مطار بوغوتا — 24 فبراير 2026[/bold bright_red]")
    t.add_row("يواجه",        "[bright_red]عقوبة السجن المؤبد[/bright_red]")
    panel(t, title="[bright_red] ملف المتهم [/bright_red]", style=R)

def cmd_how_translate():
    panel(
        "[bold bright_green]غوغل ترانسليت — نظامان لا نظام واحد[/bold bright_green]\n"
        "[grey50]كثيرون يظنّونه مجرد برنامج ترجمة، والحقيقة أعمق من ذلك[/grey50]",
        style=G2
    )
    blank()
    c1 = Panel(
        "[bold green]النظام الأول — الزاحف[/bold green]\n\n"
        "[grey50]طبيعته: [/grey50][white]برنامج كلاسيكي لا علاقة له بالذكاء الاصطناعي[/white]\n"
        "[grey50]عمله:   [/grey50][white]يجول في الإنترنت ويجمع النصوص[/white]\n"
        "[grey50]هدفه:   [/grey50][white]إيجاد نفس النص بلغتين مختلفتين[/white]\n"
        "[grey50]وأنت:   [/grey50][green]لا يعرف شيئاً عنك — بياناته مجهولة الهوية ✓[/green]\n"
        "[grey50]فكّر فيه:[/grey50][white] كعامل مكتبة يجمع الكتب دون أن يقرأها[/white]",
        border_style=G2, padding=(1,2)
    )
    c2 = Panel(
        "[bold yellow]النظام الثاني — نموذج الذكاء الاصطناعي[/bold yellow]\n\n"
        "[grey50]طبيعته: [/grey50][white]نموذج Transformer متطور[/white]\n"
        "[grey50]تدريبه: [/grey50][white]على مليارات الأمثلة التي جمعها الزاحف[/white]\n"
        "[grey50]عمله:   [/grey50][white]يترجم النص الذي تكتبه أنت الآن[/white]\n"
        "[grey50]وأنت:   [/grey50][bright_red]يرى نصّك — يحفظه — مرتبط بهويتك ✗[/bright_red]\n"
        "[grey50]فكّر فيه:[/grey50][white]كمترجم بشري يفهم كل كلمة ويحتفظ بها[/white]",
        border_style="yellow", padding=(1,2)
    )
    console.print(Columns([c1, c2], equal=True))
    blank()
    hr()
    console.print(f"  [yellow bold]الذكاء الاصطناعي لا يدخل الصورة إلا في مرحلة التدريب.[/yellow bold]")
    console.print(f"  [grey50]قبل ذلك، الزاحف يجمع البيانات بصمت — ثم يُسلّمها للنموذج ليتعلم منها.[/grey50]")
    blank()
    blank()

def cmd_crawler():
    panel(
        "[bold bright_green]الزاحف — كيف يجمع غوغل بياناته من الإنترنت[/bold bright_green]",
        style=G2
    )
    blank()
    prog_bar("تشغيل محرك الزاحف   ", 0.7)
    prog_bar("تحميل قائمة المواقع ", 0.5)
    blank()
    console.print(f"  [green]$[/green] [white]crawler --وضع=نصوص-متوازية --هدف=الإنترنت[/white]")
    blank()
    targets = [
        ("wikipedia.org/en/Translation",  "إنجليزي","عربي",  98),
        ("wikipedia.org/ar/ترجمة",         "عربي",   "إنجليزي", 98),
        ("un.org/en/documents/security",  "إنجليزي","عربي",  96),
        ("un.org/ar/documents/security",  "عربي",   "إنجليزي", 96),
        ("bbc.com/news/world-65432",      "إنجليزي","عربي",  91),
        ("bbc.com/arabic/world-65432",    "عربي",   "إنجليزي", 91),
        ("reuters.com/article/kr8mx",     "إنجليزي","عربي",  89),
        ("aljazeera.net/أخبار/مقال",       "عربي",   "إنجليزي", 89),
        ("consilium.europa.eu/en/press",  "إنجليزي","إيطالي", 94),
        ("theguardian.com/world/xyz",     "إنجليزي","عربي",  82),
    ]
    for url, fr, to, score in targets:
        col = G if score >= 90 else A if score >= 85 else D
        console.print(f"  [grey50]GET[/grey50] https://{url}", highlight=False)
        console.print(f"       [{col}]✓ تطابق [{fr} ↔ {to}] — دقة التوافق: {score}%[/{col}]", highlight=False)
        time.sleep(0.09)
    blank()
    hr()
    stagger([
        (f"  أزواج نصية جُمعت   [bright_green bold]2,300,000,000[/bright_green bold]  (عربي ↔ إنجليزي)"),
        (f"  متوسط دقة التوافق  [bright_green]92.4%[/bright_green]"),
        (f"  أبرز المصادر        [yellow]ويكيبيديا · الأمم المتحدة · BBC · الجزيرة · الاتحاد الأوروبي[/yellow]"),
    ], gap=0.1)
    blank()
    panel(
        "[bright_red bold]⚠ تنبيه مهم[/bright_red bold]\n"
        "[grey50]  ما تكتبه أنت في مربع الترجمة لا يمر عبر الزاحف.[/grey50]\n"
        "[grey50]  نصّك يصل مباشرةً إلى النموذج، ويُحفظ على خوادم أمريكية.[/grey50]",
        style=R
    )

def cmd_user_data():
    panel(
        "[bold bright_red]ما الذي يحتفظ به غوغل عنك في كل مرة تترجم؟[/bold bright_red]",
        style=R
    )
    blank()
    prog_bar("تحليل طلب الترجمة", 0.7)
    blank()
    console.print(f"  [green]$[/green] [white]تحليل-الطلب --مصدر=غوغل-ترانسليت[/white]")
    blank()
    console.print(f"  [yellow]ما يحدث عند إرسال طلب الترجمة[/yellow]")
    stagger([
        (f"  [grey50]  البروتوكول:  [/grey50][white]POST إلى https://translate.googleapis.com/v2[/white]"),
        (f"  [grey50]  التشفير:     [/grey50][green]HTTPS — النص مشفَّر أثناء الإرسال فقط ✓[/green]"),
        (f"  [grey50]  على الخادم:  [/grey50][bright_red]النص يصل صريحاً غير مشفَّر — مقروء تماماً[/bright_red]"),
    ], gap=0.07)
    blank()
    console.print(f"  [bright_red]ما يُحفظ على خوادم غوغل في الولايات المتحدة[/bright_red]")
    stored = [
        "النص الأصلي الذي كتبته",
        "نتيجة الترجمة",
        "عنوان IP جهازك",
        "معرّف حسابك في Google",
        "بصمة جهازك",
        "التوقيت الدقيق للطلب",
        "اسم التطبيق أو المتصفح المستخدم",
    ]
    for item in stored:
        console.print(f"  [bright_red]  [محفوظ][/bright_red]  [white]{item}[/white]", highlight=False)
        time.sleep(0.07)
    blank()
    hr()
    t = Table(show_header=False, box=box.SIMPLE, padding=(0,2))
    t.add_column(style=D, no_wrap=True)
    t.add_column()
    t.add_row("مدة الاحتفاظ",   "[yellow]حتى 18 شهراً بصورة افتراضية[/yellow]")
    t.add_row("موقع الخوادم",   "[yellow]الولايات المتحدة الأمريكية[/yellow]")
    t.add_row("القانون السائد", "[yellow]ECPA — قانون خصوصية الاتصالات الإلكترونية[/yellow]")
    t.add_row("أمر المراقبة",   "[bright_red]يمكن استصداره — وهذا ما حدث مع أليموف[/bright_red]")
    t.add_row("سلسلة الوصول",   "[bright_red]أنت ← غوغل ← أي جهة قضائية أمريكية[/bright_red]")
    console.print(t)

def cmd_flaw():
    panel(
        "[bold bright_red]لماذا فشل التشفير في حماية الجاسوس؟[/bold bright_red]\n"
        "[grey50]درس في الفرق بين تشفير القناة وخصوصية المحتوى[/grey50]",
        style=R
    )
    blank()
    safe = Panel(
        "[bold green]التطبيق المشفَّر — Signal[/bold green]\n\n"
        "[grey50]الرسالة تنتقل [/grey50][green]مشفَّرةً من طرف إلى طرف[/green]\n"
        "[grey50]لا أحد يطّلع على محتواها — لا Signal ولا أي جهة أخرى[/grey50]\n"
        "[green]الـ FBI والـ NSA وغوغل: لا يستطيعون القراءة ✓[/green]",
        border_style=G2, padding=(1,2)
    )
    danger = Panel(
        "[bold bright_red]غوغل ترانسليت — النص مكشوف[/bold bright_red]\n\n"
        "[grey50]الرسالة تُنسخ وتُلصق في غوغل ←[/grey50][bright_red] تصل إلى خادم غوغل[/bright_red]\n"
        "[grey50]النص يصل [/grey50][bright_red]صريحاً وغير مشفَّر — قابل للقراءة الكاملة[/bright_red]\n"
        "[bright_red]الـ FBI + أمر قضائي = الاطلاع على كل شيء ✗[/bright_red]",
        border_style=R, padding=(1,2)
    )
    console.print(safe)
    blank()
    console.print(f"  [yellow bold]        ↓  نسخ ولصق  ←  هنا انتهت الحماية تماماً[/yellow bold]")
    blank()
    console.print(danger)
    blank()
    hr()
    stagger([
        (f"  [yellow bold]الدرس الأساسي:[/yellow bold]"),
        (f"  [grey50]  التشفير يحمي مسار الرسالة فقط — لا المحتوى بعد إخراجه من التطبيق.[/grey50]"),
        (f"  [grey50]  بمجرد أن تنسخ النص إلى مكان آخر، تنتهي الحماية كلياً.[/grey50]"),
    ], gap=0.1)
    blank()
    panel(
        "[bright_red bold]⚠ ميزة ترجمة النقر — خطر لا يُرى[/bright_red bold]\n"
        "[grey50]  أي نص تنسخه من أي تطبيق — حتى Signal وWhatsApp —[/grey50]\n"
        "[grey50]  يُرسَل إلى غوغل تلقائياً إن كانت هذه الميزة مفعَّلة.[/grey50]\n"
        "[yellow]  لإيقافها: الإعدادات ← التطبيقات ← غوغل ترانسليت ← الأذونات[/yellow]",
        style=R
    )

def cmd_warrant():
    panel(
        "[bold bright_green]كيف وصل الـ FBI إلى رسائل الجاسوس؟[/bold bright_green]\n"
        "[grey50]مسار المراقبة خطوةً بخطوة[/grey50]",
        style=G2
    )
    blank()
    prog_bar("إعادة بناء مسار المراقبة", 0.9)
    blank()
    steps = [
        ("الخطوة 1", G,  "رصد النمط المشبوه", [
            "لاحظ الـ FBI نمطاً غير عادي في تواصل أليموف مع دوروفيتش.",
            "محتوى التطبيق المشفَّر لم يكن متاحاً — طريق مسدود.",
            "توصّل المحققون إلى أن غوغل ترانسليت كان يُستخدم كجسر لغوي.",
        ]),
        ("الخطوة 2", A,  "غوغل ترانسليت = أرض أمريكية = قانون أمريكي", [
            "خوادم غوغل تقع على الأراضي الأمريكية.",
            "هذا يعني خضوعها للقانون الأمريكي بالكامل.",
            "سجلات الترجمة تُعدّ اتصالات إلكترونية محفوظة وفق قانون ECPA.",
        ]),
        ("الخطوة 3", A,  "استصدار أمر المراقبة القضائي", [
            "تقدّم الـ FBI بطلب رسمي إلى محكمة فيدرالية أمريكية.",
            "شمل الأمر سجلات الترجمة للحسابات المستهدَفة.",
            "وافقت المحكمة — وبات غوغل ملزَماً قانونياً بالامتثال.",
        ]),
        ("الخطوة 4", G,  "غوغل يُسلّم السجلات", [
            "سلّم غوغل السجلات الكاملة لكل رسائل الترجمة.",
            "أصبحت جميع الرسائل بين العربية والصربية-الكرواتية مقروءةً بالكامل.",
            "صار الـ FBI يتابع المراسلات في الوقت الفعلي.",
        ]),
        ("الخطوة 5", R,  "الاعتقال في بوغوتا", [
            "انكشفت خطط الاغتيال بتفاصيلها كاملةً.",
            "في 24 فبراير 2026، أُوقف أليموف في مطار بوغوتا الدولي.",
            "وُجِّهت إليه تهم التآمر على الاختطاف والقتل وتمويل الإرهاب.",
            "يواجه اليوم خطر السجن المؤبد.",
        ]),
    ]
    for label, col, title, details in steps:
        console.print(f"  [{col}][{label}][/{col}]  [{W}]{title}[/{W}]", highlight=False)
        for d in details:
            console.print(f"           [grey50]{d}[/grey50]", highlight=False)
            time.sleep(0.05)
        blank()
        time.sleep(0.1)
    panel(
        '[yellow bold]الخلاصة:[/yellow bold] [white]أكثر وحدة استخباراتية سرية في الجيش الروسي[/white]\n'
        '[white]لم تنكشف بسبب مخبر أو عميل مزروع في صفوفها —[/white]\n'
        '[bright_red bold]بل بسبب حاجز لغوي وأمر مراقبة قضائي[/bright_red bold]\n'
        '[grey50]— The Insider، مارس 2026[/grey50]',
        style="yellow"
    )

def cmd_lessons():
    panel(
        "[bold bright_green]خمسة دروس يجب أن يعرفها كل مترجم[/bold bright_green]\n"
        "[grey50]الأمان الرقمي ليس ترفاً — إنه جزء من الاحتراف[/grey50]",
        style=G2
    )
    blank()
    lessons = [
        ("01", G, "كل أداة سحابية تعني خروج بياناتك", [
            "غوغل ترانسليت وDeepL وChatGPT وغيرها كلها تستقبل نصوصك على خوادم خارجية.",
            "النصوص السرية أو المحمية قانونياً لا ينبغي أن تقترب من هذه الأدوات.",
        ]),
        ("02", A, "الزاحف والنموذج شيئان مختلفان تماماً", [
            "الزاحف يجمع من الإنترنت العام — بيانات مجهولة لا تمسّك.",
            "النموذج هو من يترجم نصّك — وهو من يحفظه مرتبطاً بهويتك.",
            "ما تترجمه لا يذهب للزاحف — بل للنموذج مباشرةً.",
        ]),
        ("03", R, "التشفير يحمي مسار الرسالة، لا محتواها", [
            "استخدام تطبيق مشفَّر ثم نسخ النص إلى أداة سحابية يلغي الحماية كلياً.",
            "حين تخرج النص من التطبيق المشفَّر، تنتهي حمايته في تلك اللحظة.",
        ]),
        ("04", R, "أوقف ميزة ترجمة النقر الآن", [
            "هذه الميزة ترسل أي نص تنسخه تلقائياً إلى غوغل، من أي تطبيق.",
            "حتى رسائل Signal وWhatsApp وTelegram ليست بمأمن منها.",
        ]),
        ("05", G, "اختر أداة الترجمة بحسب حساسية النص", [
            "نص عام       ← أي أداة مقبولة.",
            "نص مهني      ← DeepL Pro بخوادمه الأوروبية كحدٍّ أدنى.",
            "نص سري       ← نموذج محلي على جهازك فقط، لا شيء يغادر.",
        ]),
    ]
    for num, col, title, details in lessons:
        console.print(f"  [{col}][{num}][/{col}]  [{W}]{title}[/{W}]", highlight=False)
        for d in details:
            console.print(f"        [grey50]{d}[/grey50]", highlight=False)
            time.sleep(0.05)
        blank()
        time.sleep(0.08)

def cmd_tools():
    panel(
        "[bold bright_green]بدائل آمنة لغوغل ترانسليت[/bold bright_green]\n"
        "[grey50]مرتَّبة من الأعلى خصوصيةً إلى الأقل[/grey50]",
        style=G2
    )
    blank()
    t = Table(box=box.SIMPLE_HEAD, border_style="grey23", padding=(0,1))
    t.add_column("الأداة",     style=W, no_wrap=True)
    t.add_column("طريقة العمل", style=D)
    t.add_column("الخصوصية",  no_wrap=True)
    t.add_column("التكلفة",    no_wrap=True)

    t.add_row("[bright_green]── المستوى الأول — كل شيء على جهازك[/bright_green]","","","")
    t.add_row("LibreTranslate", "مستضاف محلياً أو ذاتياً",
              "[bright_green]حماية كاملة ✓[/bright_green]", "[bright_green]مجاني[/bright_green]")
    t.add_row("Argos Translate", "يعمل بلا اتصال بالإنترنت",
              "[bright_green]حماية كاملة ✓[/bright_green]", "[bright_green]مجاني[/bright_green]")
    t.add_row("OPUS-MT",        "نماذج مفتوحة المصدر",
              "[bright_green]حماية كاملة ✓[/bright_green]", "[bright_green]مجاني[/bright_green]")
    t.add_row("[yellow]── المستوى الثاني — خوادم أوروبية خاضعة لـ GDPR[/yellow]","","","")
    t.add_row("DeepL Pro",  "خوادم أوروبية",
              "[yellow]جيدة[/yellow]", "[yellow]مدفوع[/yellow]")
    t.add_row("ModernMT",   "يراعي الخصوصية",
              "[yellow]جيدة[/yellow]", "[yellow]مدفوع[/yellow]")
    t.add_row("[bright_red]── المستوى الثالث — تجنّبها للمحتوى الحساس[/bright_red]","","","")
    t.add_row("غوغل ترانسليت", "سحابي أمريكي — كل شيء مسجَّل",
              "[bright_red]غير آمن للمحتوى الحساس ✗[/bright_red]", "[bright_green]مجاني[/bright_green]")
    t.add_row("Bing Translator","سحابي تابع لـ Microsoft",
              "[bright_red]غير آمن للمحتوى الحساس ✗[/bright_red]", "[bright_green]مجاني[/bright_green]")
    console.print(t)
    blank()
    console.print(f"  [yellow bold]القاعدة الذهبية:[/yellow bold]")
    console.print(f"  [grey50]  حساسية النص هي التي تحدد الأداة المناسبة — وليس العكس.[/grey50]")
    blank()

def cmd_about():
    a = Table(show_header=False, box=box.SIMPLE, padding=(0,2))
    a.add_column(style=D, no_wrap=True)
    a.add_column()
    a.add_row("الاسم",    "[bold bright_green]دلال نصرالله  /  Dalal Nasrallah[/bold bright_green]")
    a.add_row("التخصص",  "[yellow]مترجمة إيطالية · مترجمة إنجليزية · مبرمجة[/yellow]")
    a.add_row("العلامة",  "[bright_green]ترجمتك للتقنية — Tarjimtech[/bright_green]")
    a.add_row("البحث",    "[green]Translation Quality Assessment & Arabic Localization[/green]")
    a.add_row("البريد",   "[grey50]d@dalalnsrallah.com[/grey50]")
    a.add_row("X",        "[grey50]@dalalnsrAllah[/grey50]")
    panel(a, title="[bright_green] عن المبرمجة [/bright_green]", style=G2)
    blank()
    t = Table(show_header=False, box=box.SIMPLE, padding=(0,2))
    t.add_column(style=D, no_wrap=True)
    t.add_column()
    t.add_row("الموضوع", "[white]ترجمة غوغل والخصوصية[/white]")
    t.add_row("الفئة",   "[white]المترجمون والمهتمون بالذكاء الاصطناعي[/white]")
    t.add_row("المصدر",  "[white]The Insider / Meduza — مارس 2026[/white]")
    t.add_row("التمويل", "[yellow]ترجمتك للتقنية — Tarjimtech[/yellow]")
    t.add_row("التاريخ", "[grey50]14 مارس 2026[/grey50]")
    panel(t, title="[bright_green] عن هذا المحتوى [/bright_green]", style=G2)

# ── MAIN ──────────────────────────────────────────────────
def run():
    console.clear()

    # ── PORTRAIT ─────────────────────────────────────────
    portrait = [
        "                                                  ",
        "                  [green].:;;::::::.::.                  [/green]",
        "             [green]:+*#@@@@@@@@@@@@@@@#*+;:             [/green]",
        "          [green];*#@@@@@@@@@@@##@@@@@@@@@@@#*;          [/green]",
        "       [green].+#@@@@@@@@@@@@@@@@@@@@@@@@@@##@@@+        [/green]",
        "      [green]+#@##@@@@@@##@@@@@@@@##@@@@@@@@###@@#:      [/green]",
        "    [green].#@@##@@@@@@#**###@@@@@##@@###@@@@###@@@;     [/green]",
        "   [green].#@##@@@@@@@@@#******++;::;+*##@##@@###@@@:    [/green]",
        "   [green]#@@@@@@##@@@#*;:.           .:+#@#*#@###@@@.   [/green]",
        "  [green]*@@@@@###@@#*;:                .;*@#*#####@@*   [/green]",
        " [green]:@@@@@@#@@@@#+:                  .+#@@######@@;  [/green]",
        " [green]*@@@@@@@@@@#*:                    :+###@@@@@@@#  [/green]",
        "[green]:@@@@@@@@@@#*:                      :+###@@@@@@@; [/green]",
        "[green]#@@@@@@@@@@#+;::;::..       .:::::.:;*###@@@@@@@@.[/green]",
        "[green]@@@@@@@@@@*;:;;;;++++:.    :+++++;;;:;*@#@@@@@@@@#[/green]",
        "[green]@@@@@@@@@+;*@#+@#+:+*;:.  .:+*;+@#**@*;*##@@@@@@@[/green]",
        "[green]@@@@@@@@+...:;.;+::::::.  ..::..;;:::. .+#@@@@@@@@[/green]",
        "[green]@@@@@@@#:..          ::.  ..            .+@@@@@@@@[/green]",
        "[green]@@@@@@@#;:..        .:.    ..          ..;@@@@@@@@[/green]",
        "[green]@@@@@@@#;:...      ::;:   .:.         ...;#@@@@@@@[/green]",
        "[green]@@@@@@@@+::...    ..:;;:;:.:.         ...:#@@@@@@@[/green]",
        "[green]@@@@@@@@*::....      .....         .....:*@@@@@@@@[/green]",
        "[green]#@@@@@@@@;::.....:;+++*****++;:..  .....+@@@@@@@@@[/green]",
        "[green]#@@@@@@@@#;::....::+++;;+++++;....  ...+@@@@@@#@@@[/green]",
    ]
    for row in portrait:
        console.print(f"  {row}", highlight=False)
    blank()

    # ── AUTHOR CARD ──────────────────────────────────────
    author = Table(show_header=False, box=None, padding=(0, 2))
    author.add_column(style=D, no_wrap=True)
    author.add_column()
    author.add_row("",         "[bold bright_green]دلال نصرالله[/bold bright_green]  [grey50]/[/grey50]  [bold white]Dalal Nasrallah[/bold white]")
    author.add_row("",         "[yellow]مترجمة إيطالية · مترجمة إنجليزية · مبرمجة[/yellow]")
    author.add_row("",         "[grey50]Italian & English Translator · Developer[/grey50]")
    author.add_row("",         "")
    author.add_row("brand",    "[bright_green]محتوى إبداعي لإثراء العالم التقني الترجمي العربي[/bright_green]")
    author.add_row("research", "[green]Translation Quality Assessment & Arabic Localization[/green]")
    author.add_row("module",   "[yellow]AI & Translation Security[/yellow]  [grey50]— مارس 2026[/grey50]")
    author.add_row("email",    "[grey50]d@dalalnsrallah.com[/grey50]")
    author.add_row("X",        "[grey50]@dalalnsrAllah[/grey50]")
    console.print(Panel(author, title="[grey50] // TRANSLATOR [/grey50]", border_style=G2, padding=(1, 3)))
    blank()

    # ── WELCOME ──────────────────────────────────────────
    console.print(Panel(
        "[bold bright_green]TARJIMTECH INTEL TERMINAL[/bold bright_green]\n"
        "[grey50]محتوى إبداعي للمهتمين بالتوطين والتقنية[/grey50]\n"
        "[grey50]Creative Content for Localization & Technology Enthusiasts[/grey50]\n"
        "[grey50]─────────────────────────────────────────────[/grey50]\n"
        "[grey50]Educational Module — AI & Translation Security[/grey50]\n"
        "[grey50]─────────────────────────────────────────────[/grey50]\n"
        "القضية  [yellow]CENTER-795-2026[/yellow]\n"
        "الحالة  [bright_red]سرية ← رُفعت السرية لأغراض تعليمية[/bright_red]\n"
        "[grey50]─────────────────────────────────────────────[/grey50]\n"
        "[bright_green]مستعد.[/bright_green]",
        border_style=G2, padding=(1, 3)
    ))
    blank()

    cmd_history = []
    while True:
        try:
            raw = Prompt.ask(f"[bright_green]›[/bright_green]", default="", show_default=False)
            cmd = normalize_arabic(raw)
        except (KeyboardInterrupt, EOFError):
            blank()
            blank()
            continue

        if not cmd:
            continue

        cmd_history.append(cmd)
        blank()

        dispatch = {
            # Arabic commands — all normalized (no hamza, ة→ه)
            "مساعده":  cmd_help,
            "تشغيل":   cmd_boot,
            "الحادثه": cmd_incident,
            "المشتبه": cmd_suspect,
            "نظام":    cmd_how_translate,
            "الزاحف":  cmd_crawler,
            "بياناتك": cmd_user_data,
            "الثغره":  cmd_flaw,
            "مراقبه":  cmd_warrant,
            "fbi":     cmd_warrant,
            "FBI":     cmd_warrant,
            "الدروس":  cmd_lessons,
            "ادوات":   cmd_tools,
            "عن":      cmd_about,
            "مسح":     lambda: console.clear(),
            "خروج":    lambda: sys.exit(0),
            # English aliases
            "help":    cmd_help,
            "boot":    cmd_boot,
            "incident":cmd_incident,
            "suspect": cmd_suspect,
            "how":     cmd_how_translate,
            "crawler": cmd_crawler,
            "data":    cmd_user_data,
            "flaw":    cmd_flaw,
            "warrant": cmd_warrant,
            "lessons": cmd_lessons,
            "tools":   cmd_tools,
            "about":   cmd_about,
            "clear":   lambda: console.clear(),
            "exit":    lambda: sys.exit(0),
        }

        if cmd in dispatch:
            try:
                dispatch[cmd]()
            except KeyboardInterrupt:
                blank()
                console.print("[grey50]  تم الإيقاف.[/grey50]")
        else:
            matches = [c for c in ALL_CMDS if c.startswith(cmd)]
            if len(matches) == 1:
                try:
                    dispatch[matches[0]]()
                except KeyboardInterrupt:
                    blank()
            elif len(matches) > 1:
                console.print(f"  [grey50]هل تقصدين:[/grey50] " +
                               "  ".join(f"[bright_green]{m}[/bright_green]" for m in matches))
            else:
                console.print(f"  [bright_red]أمر غير معروف:[/bright_red] [yellow]{escape(cmd)}[/yellow]", highlight=False)

        blank()

if __name__ == "__main__":
    run()
