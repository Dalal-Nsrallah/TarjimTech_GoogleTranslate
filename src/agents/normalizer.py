"""
وكيل 1: المطبّع (Normalizer Agent)
===================================
يُصلح النص العربي قبل وبعد الترجمة.
يعمل أوفلاين بالكامل — لا يحتاج إنترنت.

المهام:
  - توحيد أشكال الهمزة (إ أ آ → ا)
  - إزالة التشكيل الزائد
  - تصحيح التاء المربوطة/المبسوطة
  - توحيد علامات الترقيم العربية
  - تطبيع المسافات والأرقام
"""

import re
import json
import unicodedata
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NormalizationResult:
    """نتيجة التطبيع مع تفاصيل التغييرات."""
    original: str
    normalized: str
    changes: list = field(default_factory=list)
    rules_applied: list = field(default_factory=list)

    @property
    def was_modified(self) -> bool:
        return self.original != self.normalized


class NormalizerAgent:
    """
    الوكيل الأول — المطبّع.
    يُطبّع النص العربي لتحسين جودة الترجمة.
    """

    # أشكال الهمزة → ألف بدون همزة
    HAMZA_MAP = {
        "إ": "ا",
        "أ": "ا",
        "آ": "ا",
        "ٱ": "ا",
    }

    # علامات التشكيل العربية
    TASHKEEL = re.compile(
        "[\u0617-\u061A\u064B-\u0652\u0656-\u065F\u0670]"
    )

    # علامات الترقيم: تحويل الإنجليزية للعربية
    PUNCTUATION_MAP = {
        ",": "،",
        ";": "؛",
        "?": "؟",
    }

    # أرقام هندية → عربية (غربية)
    HINDI_TO_ARABIC = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

    def __init__(self, extra_rules_path: Optional[str] = None):
        self.extra_rules = []
        self.stats = {
            "texts_processed": 0,
            "hamza_fixes": 0,
            "tashkeel_removals": 0,
            "punctuation_fixes": 0,
            "space_fixes": 0,
            "taa_marbuta_fixes": 0,
            "number_conversions": 0,
            "extra_rules_applied": 0,
        }
        if extra_rules_path:
            self._load_extra_rules(extra_rules_path)

    def _load_extra_rules(self, path: str):
        """يحمّل قواعد إضافية من ملف JSON (مثلاً من وكيل المكتشف)."""
        rules_file = Path(path)
        if rules_file.exists():
            with open(rules_file, "r", encoding="utf-8") as f:
                self.extra_rules = json.load(f)

    def normalize_hamza(self, text: str) -> tuple[str, int]:
        """توحيد أشكال الهمزة."""
        count = 0
        for old, new in self.HAMZA_MAP.items():
            occurrences = text.count(old)
            if occurrences:
                text = text.replace(old, new)
                count += occurrences
        return text, count

    def remove_tashkeel(self, text: str) -> tuple[str, int]:
        """إزالة التشكيل."""
        cleaned = self.TASHKEEL.sub("", text)
        count = len(text) - len(cleaned)
        return cleaned, count

    def normalize_punctuation(self, text: str) -> tuple[str, int]:
        """توحيد علامات الترقيم."""
        count = 0
        for eng, arb in self.PUNCTUATION_MAP.items():
            occurrences = text.count(eng)
            if occurrences:
                text = text.replace(eng, arb)
                count += occurrences
        return text, count

    def normalize_spaces(self, text: str) -> tuple[str, int]:
        """تطبيع المسافات — إزالة المسافات المتعددة والزائدة."""
        original = text
        # مسافات متعددة → مسافة واحدة
        text = re.sub(r" {2,}", " ", text)
        # مسافة قبل علامات الترقيم
        text = re.sub(r"\s+([،؛؟.!:])", r"\1", text)
        text = text.strip()
        count = 1 if original != text else 0
        return text, count

    def fix_taa_marbuta(self, text: str) -> tuple[str, int]:
        """تصحيح التاء المربوطة في نهاية الكلمات (ه → ة في سياقات معينة)."""
        count = 0
        # كلمات شائعة تنتهي بتاء مربوطة لكن تُكتب خطأً بهاء
        common_words = {
            "مدرسه": "مدرسة",
            "جامعه": "جامعة",
            "شركه": "شركة",
            "حكومه": "حكومة",
            "ترجمه": "ترجمة",
            "لغه": "لغة",
            "مشكله": "مشكلة",
            "خدمه": "خدمة",
            "تقنيه": "تقنية",
            "برمجه": "برمجة",
            "خوارزميه": "خوارزمية",
            "تطبيقيه": "تطبيقية",
            "عمليه": "عملية",
            "نتيجه": "نتيجة",
            "قاعده": "قاعدة",
            "بيانات": "بيانات",
            "معالجه": "معالجة",
            "جوده": "جودة",
        }
        for wrong, correct in common_words.items():
            if wrong in text:
                text = text.replace(wrong, correct)
                count += 1
        return text, count

    def convert_numbers(self, text: str) -> tuple[str, int]:
        """تحويل الأرقام الهندية للعربية (الغربية)."""
        new_text = text.translate(self.HINDI_TO_ARABIC)
        count = sum(1 for a, b in zip(text, new_text) if a != b)
        return new_text, count

    def apply_extra_rules(self, text: str) -> tuple[str, int]:
        """تطبيق القواعد الإضافية من وكيل المكتشف."""
        count = 0
        for rule in self.extra_rules:
            pattern = rule.get("pattern", "")
            replacement = rule.get("replacement", "")
            if pattern and replacement:
                new_text = re.sub(pattern, replacement, text)
                if new_text != text:
                    count += 1
                    text = new_text
        return text, count

    def normalize(self, text: str, keep_tashkeel: bool = False) -> NormalizationResult:
        """
        تطبيع النص العربي بالكامل.

        Args:
            text: النص المراد تطبيعه
            keep_tashkeel: إذا True يحافظ على التشكيل

        Returns:
            NormalizationResult مع تفاصيل كل التغييرات
        """
        original = text
        changes = []
        rules = []

        # 1. توحيد الهمزة
        text, c = self.normalize_hamza(text)
        if c:
            changes.append(f"توحيد همزة: {c} تغيير")
            rules.append("hamza_normalization")
            self.stats["hamza_fixes"] += c

        # 2. إزالة التشكيل (اختياري)
        if not keep_tashkeel:
            text, c = self.remove_tashkeel(text)
            if c:
                changes.append(f"إزالة تشكيل: {c} حرف")
                rules.append("tashkeel_removal")
                self.stats["tashkeel_removals"] += c

        # 3. تصحيح التاء المربوطة
        text, c = self.fix_taa_marbuta(text)
        if c:
            changes.append(f"تصحيح تاء مربوطة: {c} كلمة")
            rules.append("taa_marbuta_fix")
            self.stats["taa_marbuta_fixes"] += c

        # 4. توحيد علامات الترقيم
        text, c = self.normalize_punctuation(text)
        if c:
            changes.append(f"توحيد ترقيم: {c} علامة")
            rules.append("punctuation_normalization")
            self.stats["punctuation_fixes"] += c

        # 5. تحويل الأرقام
        text, c = self.convert_numbers(text)
        if c:
            changes.append(f"تحويل أرقام: {c} رقم")
            rules.append("number_conversion")
            self.stats["number_conversions"] += c

        # 6. تطبيع المسافات
        text, c = self.normalize_spaces(text)
        if c:
            changes.append("تطبيع المسافات")
            rules.append("space_normalization")
            self.stats["space_fixes"] += c

        # 7. قواعد إضافية من وكيل المكتشف
        text, c = self.apply_extra_rules(text)
        if c:
            changes.append(f"قواعد مكتشفة: {c} قاعدة")
            rules.append("discovered_rules")
            self.stats["extra_rules_applied"] += c

        self.stats["texts_processed"] += 1

        return NormalizationResult(
            original=original,
            normalized=text,
            changes=changes,
            rules_applied=rules,
        )

    def get_stats(self) -> dict:
        """إرجاع إحصائيات المعالجة."""
        return self.stats.copy()

    def reset_stats(self):
        """إعادة تعيين الإحصائيات."""
        for key in self.stats:
            self.stats[key] = 0
