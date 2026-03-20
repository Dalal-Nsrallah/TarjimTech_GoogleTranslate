"""
وكيل 3: معالج الاتجاهات (BiDi Fixer Agent)
=============================================
يُصلح مشاكل اتجاه النص العربي (RTL) مع النصوص اللاتينية (LTR).
يعمل أوفلاين بالكامل.

المهام:
  - إدراج علامات Unicode BiDi الصحيحة
  - إصلاح ترتيب الأقواس والعلامات
  - معالجة النصوص المختلطة (عربي + إنجليزي + أرقام)
  - إصلاح اتجاه علامات الترقيم
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# علامات Unicode للاتجاه
RLM = "\u200F"   # Right-to-Left Mark
LRM = "\u200E"   # Left-to-Right Mark
RLE = "\u202B"   # Right-to-Left Embedding
LRE = "\u202A"   # Left-to-Right Embedding
PDF = "\u202C"   # Pop Directional Formatting
RLI = "\u2067"   # Right-to-Left Isolate
LRI = "\u2066"   # Left-to-Right Isolate
PDI = "\u2069"   # Pop Directional Isolate


@dataclass
class BidiIssue:
    """مشكلة اتجاه واحدة."""
    position: int
    issue_type: str
    description: str
    fix_applied: str


@dataclass
class BidiResult:
    """نتيجة إصلاح الاتجاهات."""
    original: str
    fixed: str
    issues: list = field(default_factory=list)

    @property
    def was_modified(self) -> bool:
        return self.original != self.fixed


class BidiFixerAgent:
    """
    الوكيل الثالث — معالج الاتجاهات.
    يُصلح مشاكل RTL/LTR في النصوص المختلطة.
    """

    # أنماط النص اللاتيني (إنجليزي، أرقام، رموز)
    LATIN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9._\-]*(?:\s+[a-zA-Z][a-zA-Z0-9._\-]*)*")

    # أنماط الأرقام مع وحدات
    NUMBER_UNIT_PATTERN = re.compile(r"\d+(?:\.\d+)?\s*(?:%|[a-zA-Z]+)")

    # أقواس ورموز تحتاج عكس في RTL
    BRACKET_PAIRS = {
        "(": ")",
        ")": "(",
        "[": "]",
        "]": "[",
        "{": "}",
        "}": "{",
        "<": ">",
        ">": "<",
    }

    # نمط عربي
    ARABIC_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]")

    def __init__(self):
        self.stats = {
            "texts_processed": 0,
            "latin_isolations": 0,
            "number_fixes": 0,
            "bracket_fixes": 0,
            "punctuation_fixes": 0,
            "rlm_insertions": 0,
        }

    def _is_arabic(self, char: str) -> bool:
        """هل الحرف عربي؟"""
        return bool(self.ARABIC_PATTERN.match(char))

    def _is_latin(self, char: str) -> bool:
        """هل الحرف لاتيني؟"""
        return char.isascii() and char.isalpha()

    def isolate_latin_segments(self, text: str) -> tuple[str, list[BidiIssue]]:
        """عزل المقاطع اللاتينية بعلامات LRI/PDI."""
        issues = []

        def replacer(match):
            segment = match.group()
            start = match.start()
            # تحقق أن المقطع محاط بنص عربي (تخطي المسافات)
            before = ""
            for j in range(start - 1, -1, -1):
                if not text[j].isspace():
                    before = text[j]
                    break
            after = ""
            for j in range(match.end(), len(text)):
                if not text[j].isspace():
                    after = text[j]
                    break

            if (before and self._is_arabic(before)) or (after and self._is_arabic(after)):
                issues.append(BidiIssue(
                    position=start,
                    issue_type="latin_isolation",
                    description=f"عزل نص لاتيني: '{segment}'",
                    fix_applied="LRI...PDI",
                ))
                self.stats["latin_isolations"] += 1
                return f"{LRI}{segment}{PDI}"
            return segment

        fixed = self.LATIN_PATTERN.sub(replacer, text)
        return fixed, issues

    def fix_numbers_in_context(self, text: str) -> tuple[str, list[BidiIssue]]:
        """إصلاح اتجاه الأرقام في السياق العربي."""
        issues = []

        def replacer(match):
            segment = match.group()
            issues.append(BidiIssue(
                position=match.start(),
                issue_type="number_fix",
                description=f"إصلاح اتجاه رقم: '{segment}'",
                fix_applied="LRI...PDI",
            ))
            self.stats["number_fixes"] += 1
            return f"{LRI}{segment}{PDI}"

        fixed = self.NUMBER_UNIT_PATTERN.sub(replacer, text)
        return fixed, issues

    def fix_punctuation_direction(self, text: str) -> tuple[str, list[BidiIssue]]:
        """إصلاح اتجاه علامات الترقيم بين النص العربي واللاتيني."""
        issues = []
        result = list(text)
        i = 0

        while i < len(result):
            char = result[i]
            # إذا كانت نقطة أو فاصلة بعد نص عربي
            if char in ".,:;" and i > 0:
                prev_char = result[i - 1] if i > 0 else ""
                if prev_char and self._is_arabic(prev_char):
                    # أضف RLM بعد علامة الترقيم لضمان الاتجاه الصحيح
                    if i + 1 < len(result) and self._is_latin(result[i + 1]):
                        result.insert(i + 1, RLM)
                        issues.append(BidiIssue(
                            position=i,
                            issue_type="punctuation_direction",
                            description=f"إصلاح اتجاه ترقيم: '{char}'",
                            fix_applied="RLM بعد علامة الترقيم",
                        ))
                        self.stats["punctuation_fixes"] += 1
            i += 1

        return "".join(result), issues

    def ensure_rtl_paragraph(self, text: str) -> tuple[str, list[BidiIssue]]:
        """ضمان اتجاه RTL للفقرة العربية."""
        issues = []
        # إذا النص يبدأ بحرف عربي، أضف RLM في البداية
        if text and self._is_arabic(text[0]):
            if not text.startswith(RLM) and not text.startswith(RLI):
                text = RLM + text
                issues.append(BidiIssue(
                    position=0,
                    issue_type="rtl_paragraph",
                    description="إضافة RLM لبداية الفقرة",
                    fix_applied="RLM في البداية",
                ))
                self.stats["rlm_insertions"] += 1
        return text, issues

    def clean_existing_bidi_marks(self, text: str) -> str:
        """إزالة علامات BiDi القديمة قبل إعادة المعالجة."""
        marks = [RLM, LRM, RLE, LRE, PDF, RLI, LRI, PDI]
        for mark in marks:
            text = text.replace(mark, "")
        return text

    def fix(self, text: str, clean_first: bool = True) -> BidiResult:
        """
        إصلاح اتجاهات النص الكامل.

        Args:
            text: النص المراد إصلاحه
            clean_first: إزالة علامات BiDi القديمة أولاً

        Returns:
            BidiResult مع النص المُصلح وتفاصيل التغييرات
        """
        original = text
        all_issues = []

        # تنظيف العلامات القديمة
        if clean_first:
            text = self.clean_existing_bidi_marks(text)

        # 1. عزل المقاطع اللاتينية
        text, issues = self.isolate_latin_segments(text)
        all_issues.extend(issues)

        # 2. إصلاح الأرقام
        text, issues = self.fix_numbers_in_context(text)
        all_issues.extend(issues)

        # 3. إصلاح علامات الترقيم
        text, issues = self.fix_punctuation_direction(text)
        all_issues.extend(issues)

        # 4. ضمان اتجاه الفقرة
        text, issues = self.ensure_rtl_paragraph(text)
        all_issues.extend(issues)

        self.stats["texts_processed"] += 1

        return BidiResult(
            original=original,
            fixed=text,
            issues=all_issues,
        )

    def get_stats(self) -> dict:
        return self.stats.copy()
