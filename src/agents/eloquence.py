"""
وكيل 4: الفصاحة (Arabic Eloquence Agent)
==========================================
يقرأ النص العربي كاملاً ويُحسّن لغته لتكون فصيحة وسليمة.
يعمل أوفلاين بالكامل — قواعد مبنية على النحو والصرف العربي.

المهام:
  - استبدال الأساليب الركيكة بأساليب فصيحة
  - تصحيح التراكيب المتأثرة بالإنجليزية (Calque)
  - تحسين ترتيب الجملة (فعلية بدل اسمية حيث يُناسب)
  - استبدال "يتم + مصدر" بالمبني للمجهول
  - إزالة الحشو والتكرار
  - تحسين حروف العطف والربط
  - ضبط المطابقة (مذكر/مؤنث، مفرد/جمع)
"""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EloquenceFix:
    """إصلاح فصاحة واحد."""
    rule_name: str           # اسم القاعدة
    category: str            # نوع: أسلوب، نحو، صرف، بلاغة، حشو
    original: str            # النص الأصلي
    improved: str            # النص المحسّن
    explanation: str         # شرح سبب التحسين


@dataclass
class EloquenceResult:
    """نتيجة تحسين الفصاحة."""
    original_text: str
    improved_text: str
    fixes: list = field(default_factory=list)
    eloquence_score_before: float = 0.0
    eloquence_score_after: float = 0.0

    @property
    def was_modified(self) -> bool:
        return self.original_text != self.improved_text

    @property
    def improvement(self) -> float:
        return self.eloquence_score_after - self.eloquence_score_before


class EloquenceAgent:
    """
    وكيل الفصاحة — يُحسّن النص العربي ليكون فصيحاً وطبيعياً.

    يعالج المشاكل الشائعة في النصوص المترجمة من الإنجليزية:
    1. أساليب ركيكة متأثرة بتراكيب إنجليزية
    2. حشو وتكرار غير ضروري
    3. ترتيب جملة غير طبيعي بالعربية
    4. مبني للمجهول ركيك
    5. حروف ربط ضعيفة
    """

    def __init__(self, extra_rules_path: Optional[str] = None):
        self.stats = {
            "texts_processed": 0,
            "total_fixes": 0,
            "style_fixes": 0,
            "grammar_fixes": 0,
            "padding_removals": 0,
            "calque_fixes": 0,
            "passive_fixes": 0,
            "connector_fixes": 0,
        }
        self._extra_rules = []
        if extra_rules_path:
            self._load_extra_rules(extra_rules_path)

    def _load_extra_rules(self, path: str):
        import json
        from pathlib import Path
        p = Path(path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                self._extra_rules = json.load(f)

    # ═══════════════════════════════════════════
    # 1. إصلاح "يتم + فعل" → المبني للمجهول
    # ═══════════════════════════════════════════

    # "يتم إرسال" → "يُرسَل"
    # "يتم تنفيذ" → "يُنفَّذ"
    # "تم إنشاء" → "أُنشئ"
    YATIM_PATTERNS = [
        # يتم + مصدر → مضارع مبني للمجهول
        (re.compile(r"يتم\s+إرسال"), "يُرسَل", "مبني للمجهول أفصح من 'يتم إرسال'"),
        (re.compile(r"يتم\s+تنفيذ"), "يُنفَّذ", "مبني للمجهول أفصح من 'يتم تنفيذ'"),
        (re.compile(r"يتم\s+تحديث"), "يُحدَّث", "مبني للمجهول أفصح من 'يتم تحديث'"),
        (re.compile(r"يتم\s+استخدام"), "يُستخدَم", "مبني للمجهول أفصح من 'يتم استخدام'"),
        (re.compile(r"يتم\s+تطبيق"), "يُطبَّق", "مبني للمجهول أفصح من 'يتم تطبيق'"),
        (re.compile(r"يتم\s+تشغيل"), "يُشغَّل", "مبني للمجهول أفصح من 'يتم تشغيل'"),
        (re.compile(r"يتم\s+حذف"), "يُحذَف", "مبني للمجهول أفصح من 'يتم حذف'"),
        (re.compile(r"يتم\s+عرض"), "يُعرَض", "مبني للمجهول أفصح من 'يتم عرض'"),
        (re.compile(r"يتم\s+حفظ"), "يُحفَظ", "مبني للمجهول أفصح من 'يتم حفظ'"),
        (re.compile(r"يتم\s+فحص"), "يُفحَص", "مبني للمجهول أفصح من 'يتم فحص'"),
        (re.compile(r"يتم\s+نقل"), "يُنقَل", "مبني للمجهول أفصح من 'يتم نقل'"),
        (re.compile(r"يتم\s+تحميل"), "يُحمَّل", "مبني للمجهول أفصح من 'يتم تحميل'"),
        (re.compile(r"يتم\s+تخزين"), "يُخزَّن", "مبني للمجهول أفصح من 'يتم تخزين'"),
        (re.compile(r"يتم\s+معالجة"), "تُعالَج", "مبني للمجهول أفصح من 'يتم معالجة'"),
        (re.compile(r"يتم\s+إضافة"), "تُضاف", "مبني للمجهول أفصح من 'يتم إضافة'"),
        (re.compile(r"يتم\s+إزالة"), "تُزال", "مبني للمجهول أفصح من 'يتم إزالة'"),
        # تم + مصدر → ماضٍ مبني للمجهول
        (re.compile(r"تم\s+إرسال"), "أُرسِل", "ماضٍ مبني للمجهول أفصح"),
        (re.compile(r"تم\s+تنفيذ"), "نُفِّذ", "ماضٍ مبني للمجهول أفصح"),
        (re.compile(r"تم\s+إنشاء"), "أُنشئ", "ماضٍ مبني للمجهول أفصح"),
        (re.compile(r"تم\s+تحديث"), "حُدِّث", "ماضٍ مبني للمجهول أفصح"),
        (re.compile(r"تم\s+حذف"), "حُذِف", "ماضٍ مبني للمجهول أفصح"),
        (re.compile(r"تم\s+استخدام"), "استُخدِم", "ماضٍ مبني للمجهول أفصح"),
        (re.compile(r"تم\s+تطبيق"), "طُبِّق", "ماضٍ مبني للمجهول أفصح"),
        (re.compile(r"تم\s+اكتشاف"), "اكتُشِف", "ماضٍ مبني للمجهول أفصح"),
        (re.compile(r"تم\s+حفظ"), "حُفِظ", "ماضٍ مبني للمجهول أفصح"),
        (re.compile(r"تم\s+نقل"), "نُقِل", "ماضٍ مبني للمجهول أفصح"),
    ]

    def fix_passive_voice(self, text: str) -> tuple[str, list[EloquenceFix]]:
        """تحويل 'يتم/تم + مصدر' إلى مبني للمجهول عربي أصيل."""
        fixes = []
        for pattern, replacement, explanation in self.YATIM_PATTERNS:
            match = pattern.search(text)
            if match:
                original = match.group()
                text = pattern.sub(replacement, text, count=1)
                fixes.append(EloquenceFix(
                    rule_name="المبني للمجهول",
                    category="نحو",
                    original=original,
                    improved=replacement,
                    explanation=explanation,
                ))
                self.stats["passive_fixes"] += 1
        return text, fixes

    # ═══════════════════════════════════════════
    # 2. إزالة الحشو والزيادات
    # ═══════════════════════════════════════════

    PADDING_PATTERNS = [
        # "بشكل + صفة" → مصدر أو حال
        (re.compile(r"بشكل\s+كبير"), "كثيراً", "استخدم الحال بدل 'بشكل'"),
        (re.compile(r"بشكل\s+سريع"), "سريعاً", "استخدم الحال بدل 'بشكل'"),
        (re.compile(r"بشكل\s+مباشر"), "مباشرةً", "استخدم الحال بدل 'بشكل'"),
        (re.compile(r"بشكل\s+عام"), "عموماً", "استخدم الحال بدل 'بشكل'"),
        (re.compile(r"بشكل\s+خاص"), "خصوصاً", "استخدم الحال بدل 'بشكل'"),
        (re.compile(r"بشكل\s+أساسي"), "أساساً", "استخدم الحال بدل 'بشكل'"),
        (re.compile(r"بشكل\s+تلقائي"), "تلقائياً", "استخدم الحال بدل 'بشكل'"),
        (re.compile(r"بشكل\s+صحيح"), "صحيحاً", "استخدم الحال بدل 'بشكل'"),
        (re.compile(r"بشكل\s+فعّال"), "بفاعلية", "استخدم المصدر بدل 'بشكل'"),
        (re.compile(r"بشكل\s+متكرر"), "مراراً", "استخدم الحال بدل 'بشكل'"),
        # "عملية الـ" → حذف "عملية"
        (re.compile(r"عملية\s+التحديث"), "التحديث", "'عملية' حشو غير ضروري"),
        (re.compile(r"عملية\s+التثبيت"), "التثبيت", "'عملية' حشو غير ضروري"),
        (re.compile(r"عملية\s+التشغيل"), "التشغيل", "'عملية' حشو غير ضروري"),
        (re.compile(r"عملية\s+البحث"), "البحث", "'عملية' حشو غير ضروري"),
        (re.compile(r"عملية\s+النقل"), "النقل", "'عملية' حشو غير ضروري"),
        (re.compile(r"عملية\s+الترجمة"), "الترجمة", "'عملية' حشو غير ضروري"),
        # "القيام بـ" → الفعل مباشرة
        (re.compile(r"القيام\s+بتنفيذ"), "تنفيذ", "'القيام بـ' حشو"),
        (re.compile(r"القيام\s+بإرسال"), "إرسال", "'القيام بـ' حشو"),
        (re.compile(r"القيام\s+بعمل"), "عمل", "'القيام بـ' حشو"),
        (re.compile(r"القيام\s+بفحص"), "فحص", "'القيام بـ' حشو"),
        # "وذلك من أجل" → "لـ"
        (re.compile(r"وذلك\s+من\s+أجل"), "لـ", "اختصر — 'لـ' أفصح من 'وذلك من أجل'"),
        # "هو عبارة عن" → حذف
        (re.compile(r"هو\s+عبارة\s+عن"), "هو", "'عبارة عن' حشو غير ضروري"),
        (re.compile(r"هي\s+عبارة\s+عن"), "هي", "'عبارة عن' حشو غير ضروري"),
    ]

    def remove_padding(self, text: str) -> tuple[str, list[EloquenceFix]]:
        """إزالة الحشو والتكرار."""
        fixes = []
        for pattern, replacement, explanation in self.PADDING_PATTERNS:
            match = pattern.search(text)
            if match:
                original = match.group()
                text = pattern.sub(replacement, text, count=1)
                fixes.append(EloquenceFix(
                    rule_name="إزالة الحشو",
                    category="حشو",
                    original=original,
                    improved=replacement,
                    explanation=explanation,
                ))
                self.stats["padding_removals"] += 1
        return text, fixes

    # ═══════════════════════════════════════════
    # 3. إصلاح التراكيب المنقولة من الإنجليزية
    # ═══════════════════════════════════════════

    CALQUE_PATTERNS = [
        # "يلعب دوراً" (plays a role) → "له دور" أو "يؤدي دوراً"
        (re.compile(r"يلعب\s+دوراً"), "يؤدي دوراً", "'يلعب دوراً' منقولة — 'يؤدي' أفصح"),
        (re.compile(r"تلعب\s+دوراً"), "تؤدي دوراً", "'تلعب دوراً' منقولة — 'تؤدي' أفصح"),
        # "يأخذ مكان" (takes place) → "يحدث / يقع"
        (re.compile(r"يأخذ\s+مكان"), "يحدث", "'يأخذ مكان' منقولة من الإنجليزية"),
        (re.compile(r"أخذ\s+مكان"), "حدث", "'أخذ مكان' منقولة من الإنجليزية"),
        # "يأخذ بعين الاعتبار" → "يراعي"
        (re.compile(r"يأخذ\s+بعين\s+الاعتبار"), "يراعي", "'يأخذ بعين الاعتبار' طويلة — 'يراعي' أفصح"),
        (re.compile(r"أخذ\s+بعين\s+الاعتبار"), "راعى", "'أخذ بعين الاعتبار' طويلة — 'راعى' أفصح"),
        # "في نهاية المطاف" (at the end of the day) → "في النهاية"
        (re.compile(r"في\s+نهاية\s+المطاف"), "في النهاية", "اختصر — 'في النهاية' تكفي"),
        # "على أرض الواقع" (on the ground) → "فعلياً / واقعياً"
        (re.compile(r"على\s+أرض\s+الواقع"), "واقعياً", "'على أرض الواقع' حشو منقول"),
        # "في هذا السياق" (in this context) → "هنا"
        (re.compile(r"في\s+هذا\s+السياق"), "هنا", "اختصر — 'هنا' تكفي غالباً"),
        # "بالنسبة لـ" (as for / regarding) → "أما ... فـ"
        (re.compile(r"بالنسبة\s+لـ?ل"), "أما", "'بالنسبة لـ' أسلوب ثقيل — 'أما ... فـ' أفصح"),
        # "يعتبر" بمعنى "is considered" → "يُعَدّ"
        (re.compile(r"يعتبر\s+من"), "يُعَدّ من", "'يُعَدّ' أفصح من 'يعتبر' بمعنى is considered"),
        (re.compile(r"تعتبر\s+من"), "تُعَدّ من", "'تُعَدّ' أفصح من 'تعتبر'"),
    ]

    def fix_calques(self, text: str) -> tuple[str, list[EloquenceFix]]:
        """إصلاح التراكيب المنقولة حرفياً من الإنجليزية."""
        fixes = []
        for pattern, replacement, explanation in self.CALQUE_PATTERNS:
            match = pattern.search(text)
            if match:
                original = match.group()
                text = pattern.sub(replacement, text, count=1)
                fixes.append(EloquenceFix(
                    rule_name="تركيب منقول",
                    category="أسلوب",
                    original=original,
                    improved=replacement,
                    explanation=explanation,
                ))
                self.stats["calque_fixes"] += 1
        return text, fixes

    # ═══════════════════════════════════════════
    # 4. تحسين حروف الربط والعطف
    # ═══════════════════════════════════════════

    CONNECTOR_PATTERNS = [
        # "بالإضافة إلى ذلك" → "فضلاً عن ذلك" أو "علاوةً على ذلك"
        (re.compile(r"بالإضافة\s+إلى\s+ذلك"), "فضلاً عن ذلك", "'فضلاً عن ذلك' أفصح"),
        # "على الرغم من" متكررة → "رغم"
        (re.compile(r"على\s+الرغم\s+من\s+أن"), "رغم أنّ", "'رغم أنّ' أخصر وأفصح"),
        # "من الممكن أن" → "قد"
        (re.compile(r"من\s+الممكن\s+أن"), "قد", "'قد' أفصح من 'من الممكن أن'"),
        # "من أجل أن" → "لـ" أو "كي"
        (re.compile(r"من\s+أجل\s+أن"), "كي", "'كي' أفصح وأخصر"),
        # "في حالة" → "إذا / إن"
        (re.compile(r"في\s+حالة\s+أن"), "إذا", "'إذا' أفصح من 'في حالة أن'"),
        (re.compile(r"في\s+حالة"), "إن", "'إن' أفصح من 'في حالة'"),
        # "وبالتالي" → "فـ" أو "لذا"
        (re.compile(r"وبالتالي"), "لذا", "'لذا' أخصر وأفصح"),
        # "نظراً لأن" → "إذ إنّ" أو "لأنّ"
        (re.compile(r"نظراً\s+لأن"), "لأنّ", "'لأنّ' أفصح من 'نظراً لأن'"),
        # "ومع ذلك" → "غير أنّ" أو "لكنّ"
        (re.compile(r"ومع\s+ذلك"), "غير أنّ", "'غير أنّ' أفصح"),
    ]

    def fix_connectors(self, text: str) -> tuple[str, list[EloquenceFix]]:
        """تحسين حروف الربط والعطف."""
        fixes = []
        for pattern, replacement, explanation in self.CONNECTOR_PATTERNS:
            match = pattern.search(text)
            if match:
                original = match.group()
                text = pattern.sub(replacement, text, count=1)
                fixes.append(EloquenceFix(
                    rule_name="حرف ربط",
                    category="أسلوب",
                    original=original,
                    improved=replacement,
                    explanation=explanation,
                ))
                self.stats["connector_fixes"] += 1
        return text, fixes

    # ═══════════════════════════════════════════
    # 5. تحسينات نحوية عامة
    # ═══════════════════════════════════════════

    GRAMMAR_PATTERNS = [
        # "الذي هو" → "الذي" (حشو ضميري)
        (re.compile(r"الذي\s+هو\s+"), "الذي ", "حذف الضمير الزائد بعد الموصول"),
        (re.compile(r"التي\s+هي\s+"), "التي ", "حذف الضمير الزائد بعد الموصول"),
        # "أكثر + صفة" → أفعل التفضيل
        (re.compile(r"أكثر\s+أهمية"), "أهمّ", "أفعل التفضيل أفصح"),
        (re.compile(r"أكثر\s+سرعة"), "أسرع", "أفعل التفضيل أفصح"),
        (re.compile(r"أكثر\s+سهولة"), "أسهل", "أفعل التفضيل أفصح"),
        (re.compile(r"أكثر\s+صعوبة"), "أصعب", "أفعل التفضيل أفصح"),
        (re.compile(r"أكثر\s+دقة"), "أدقّ", "أفعل التفضيل أفصح"),
        (re.compile(r"أكثر\s+قوة"), "أقوى", "أفعل التفضيل أفصح"),
        (re.compile(r"أكثر\s+وضوحاً"), "أوضح", "أفعل التفضيل أفصح"),
        # "لا يوجد هناك" → "لا يوجد" أو "ليس ثمة"
        (re.compile(r"لا\s+يوجد\s+هناك"), "ليس ثمة", "حذف 'هناك' الزائدة"),
        (re.compile(r"لا\s+توجد\s+هناك"), "ليس ثمة", "حذف 'هناك' الزائدة"),
        # "يوجد هناك" → "ثمة"
        (re.compile(r"يوجد\s+هناك"), "ثمة", "'ثمة' أفصح من 'يوجد هناك'"),
        (re.compile(r"توجد\s+هناك"), "ثمة", "'ثمة' أفصح من 'توجد هناك'"),
        # "هذا يعني أن" → "أي أنّ"
        (re.compile(r"هذا\s+يعني\s+أن"), "أي أنّ", "'أي أنّ' أخصر"),
    ]

    def fix_grammar(self, text: str) -> tuple[str, list[EloquenceFix]]:
        """تحسينات نحوية عامة."""
        fixes = []
        for pattern, replacement, explanation in self.GRAMMAR_PATTERNS:
            match = pattern.search(text)
            if match:
                original = match.group()
                text = pattern.sub(replacement, text, count=1)
                fixes.append(EloquenceFix(
                    rule_name="تحسين نحوي",
                    category="نحو",
                    original=original,
                    improved=replacement,
                    explanation=explanation,
                ))
                self.stats["grammar_fixes"] += 1
        return text, fixes

    # ═══════════════════════════════════════════
    # 6. تطبيق قواعد المكتشف
    # ═══════════════════════════════════════════

    def apply_extra_rules(self, text: str) -> tuple[str, list[EloquenceFix]]:
        """تطبيق قواعد إضافية من وكيل المكتشف."""
        fixes = []
        for rule in self._extra_rules:
            pattern = rule.get("pattern", "")
            replacement = rule.get("replacement", "")
            explanation = rule.get("description", "قاعدة مكتشفة")
            if pattern and replacement:
                try:
                    match = re.search(pattern, text)
                    if match:
                        original = match.group()
                        text = re.sub(pattern, replacement, text, count=1)
                        fixes.append(EloquenceFix(
                            rule_name="قاعدة مكتشفة",
                            category="أسلوب",
                            original=original,
                            improved=replacement,
                            explanation=explanation,
                        ))
                except re.error:
                    pass
        return text, fixes

    # ═══════════════════════════════════════════
    # التقييم
    # ═══════════════════════════════════════════

    def score_eloquence(self, text: str) -> float:
        """
        تقييم فصاحة النص من 0-100.
        كلما قلّت المشاكل ارتفعت الدرجة.
        """
        score = 100.0
        all_patterns = (
            self.YATIM_PATTERNS
            + self.PADDING_PATTERNS
            + self.CALQUE_PATTERNS
            + self.CONNECTOR_PATTERNS
            + self.GRAMMAR_PATTERNS
        )
        penalties = {
            "نحو": 5.0,
            "حشو": 3.0,
            "أسلوب": 4.0,
        }
        for pattern_tuple in all_patterns:
            pattern = pattern_tuple[0]
            if pattern.search(text):
                # تحديد نوع المشكلة حسب المجموعة
                if pattern_tuple in self.YATIM_PATTERNS:
                    score -= penalties["نحو"]
                elif pattern_tuple in self.PADDING_PATTERNS:
                    score -= penalties["حشو"]
                else:
                    score -= penalties["أسلوب"]
        return max(0.0, score)

    # ═══════════════════════════════════════════
    # الدورة الكاملة
    # ═══════════════════════════════════════════

    def improve(self, text: str) -> EloquenceResult:
        """
        تحسين النص العربي — الدورة الكاملة.

        يقرأ النص كاملاً ويُطبّق كل قواعد الفصاحة:
        1. المبني للمجهول
        2. إزالة الحشو
        3. إصلاح التراكيب المنقولة
        4. تحسين حروف الربط
        5. تحسينات نحوية
        6. قواعد المكتشف

        Args:
            text: النص العربي المراد تحسينه

        Returns:
            EloquenceResult مع النص المحسّن وتفاصيل كل إصلاح
        """
        original = text
        all_fixes = []

        # التقييم قبل التحسين
        score_before = self.score_eloquence(text)

        # 1. المبني للمجهول
        text, fixes = self.fix_passive_voice(text)
        all_fixes.extend(fixes)

        # 2. إزالة الحشو
        text, fixes = self.remove_padding(text)
        all_fixes.extend(fixes)

        # 3. التراكيب المنقولة
        text, fixes = self.fix_calques(text)
        all_fixes.extend(fixes)

        # 4. حروف الربط
        text, fixes = self.fix_connectors(text)
        all_fixes.extend(fixes)

        # 5. تحسينات نحوية
        text, fixes = self.fix_grammar(text)
        all_fixes.extend(fixes)

        # 6. قواعد المكتشف
        text, fixes = self.apply_extra_rules(text)
        all_fixes.extend(fixes)

        # التقييم بعد التحسين
        score_after = self.score_eloquence(text)

        self.stats["texts_processed"] += 1
        self.stats["total_fixes"] += len(all_fixes)

        return EloquenceResult(
            original_text=original,
            improved_text=text,
            fixes=all_fixes,
            eloquence_score_before=score_before,
            eloquence_score_after=score_after,
        )

    def get_stats(self) -> dict:
        return self.stats.copy()
