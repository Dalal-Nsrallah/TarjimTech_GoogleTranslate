"""
وكيل 2: مقيّم الجودة (QA Evaluator Agent)
============================================
يُقيّم جودة الترجمة من الإنجليزية للعربية.
يعمل هجين — القواعد الأساسية أوفلاين، والتقييم المتقدم أونلاين.

المهام:
  - كشف الترجمة الحرفية (literal translation)
  - فحص تناسق المصطلحات مع المعجم
  - تقييم سلاسة الجملة العربية
  - كشف الكلمات المتروكة بدون ترجمة
  - تقييم شامل بدرجة من 0-100
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QAIssue:
    """مشكلة جودة واحدة."""
    category: str          # نوع المشكلة
    severity: str          # خطورة: low, medium, high, critical
    description: str       # وصف المشكلة
    source_segment: str    # الجزء من النص المصدر
    target_segment: str    # الجزء من النص المترجم
    suggestion: str = ""   # اقتراح التصحيح


@dataclass
class QAResult:
    """نتيجة تقييم الجودة الكاملة."""
    source: str
    target: str
    score: float              # 0-100
    issues: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)

    @property
    def grade(self) -> str:
        if self.score >= 90:
            return "ممتاز"
        elif self.score >= 75:
            return "جيد"
        elif self.score >= 60:
            return "مقبول"
        elif self.score >= 40:
            return "ضعيف"
        return "مرفوض"

    @property
    def passed(self) -> bool:
        return self.score >= 60


class QAEvaluatorAgent:
    """
    الوكيل الثاني — مقيّم الجودة.
    يفحص الترجمة ويُعطي تقييماً شاملاً.
    """

    # ترجمات حرفية شائعة خاطئة
    LITERAL_TRANSLATIONS = {
        "look up": {"wrong": "انظر فوق", "correct": "ابحث عن"},
        "break down": {"wrong": "اكسر تحت", "correct": "حلّل / تعطّل"},
        "give up": {"wrong": "أعطِ فوق", "correct": "استسلم / تخلّى عن"},
        "carry out": {"wrong": "احمل خارج", "correct": "نفّذ"},
        "bring up": {"wrong": "أحضر فوق", "correct": "أثار / ربّى"},
        "turn out": {"wrong": "أدر خارج", "correct": "تبيّن / اتضح"},
        "set up": {"wrong": "ضع فوق", "correct": "أنشأ / أعدّ"},
        "point out": {"wrong": "أشر خارج", "correct": "أشار إلى / نبّه"},
        "find out": {"wrong": "اعثر خارج", "correct": "اكتشف"},
        "make up": {"wrong": "اصنع فوق", "correct": "اختلق / شكّل"},
        "take over": {"wrong": "خذ فوق", "correct": "تولّى / استحوذ"},
        "come up with": {"wrong": "تعال فوق مع", "correct": "ابتكر / توصّل إلى"},
    }

    # كلمات إنجليزية يجب ألا تبقى في النص العربي
    ENGLISH_WORD_PATTERN = re.compile(r"\b[a-zA-Z]{3,}\b")

    # أنماط المبني للمجهول الخاطئ
    PASSIVE_WRONG_PATTERNS = [
        (re.compile(r"كان\s+\S+اً"), "استخدام مبني للمجهول عربي أصيل"),
        (re.compile(r"تم\s+\S+\s+بواسطة"), "تجنب 'تم ... بواسطة' — استخدم المبني للمجهول"),
    ]

    # أنماط ضعف الجملة العربية
    WEAK_PATTERNS = [
        (re.compile(r"هو\s+يكون"), "تكرار ضمير مع فعل الكون"),
        (re.compile(r"إن\s+ال\S+\s+هو"), "'إنّ ... هو' — حشو غير ضروري"),
        (re.compile(r"بشكل\s+\S+"), "'بشكل' — أسلوب ركيك، استخدم المصدر"),
        (re.compile(r"يتم\s+\S+"), "'يتم' — استخدم الفعل المبني للمجهول مباشرة"),
        (re.compile(r"عملية\s+ال"), "'عملية الـ' — حشو غير ضروري غالباً"),
    ]

    def __init__(self, glossary_path: Optional[str] = None,
                 discovered_rules_path: Optional[str] = None):
        self.glossary = {}
        self.discovered_rules = []
        self.stats = {
            "evaluations": 0,
            "avg_score": 0.0,
            "total_issues": 0,
            "literal_detections": 0,
            "untranslated_detections": 0,
            "passive_issues": 0,
            "weak_style_issues": 0,
        }
        if glossary_path:
            self._load_glossary(glossary_path)
        if discovered_rules_path:
            self._load_discovered_rules(discovered_rules_path)

    def _load_glossary(self, path: str):
        """تحميل المعجم."""
        gpath = Path(path)
        if gpath.exists():
            with open(gpath, "r", encoding="utf-8") as f:
                self.glossary = json.load(f)

    def _load_discovered_rules(self, path: str):
        """تحميل قواعد مكتشفة من وكيل المكتشف."""
        rpath = Path(path)
        if rpath.exists():
            with open(rpath, "r", encoding="utf-8") as f:
                self.discovered_rules = json.load(f)

    def check_literal_translation(self, source: str, target: str) -> list[QAIssue]:
        """كشف الترجمات الحرفية."""
        issues = []
        source_lower = source.lower()
        for phrase, translations in self.LITERAL_TRANSLATIONS.items():
            if phrase in source_lower and translations["wrong"] in target:
                issues.append(QAIssue(
                    category="ترجمة_حرفية",
                    severity="high",
                    description=f"ترجمة حرفية لـ '{phrase}'",
                    source_segment=phrase,
                    target_segment=translations["wrong"],
                    suggestion=f"الأصح: {translations['correct']}",
                ))
                self.stats["literal_detections"] += 1
        return issues

    def check_untranslated_words(self, target: str) -> list[QAIssue]:
        """كشف الكلمات المتروكة بالإنجليزية."""
        issues = []
        # استثناء الأسماء العلم والاختصارات المعروفة
        allowed = {"API", "URL", "HTTP", "HTTPS", "JSON", "XML", "HTML",
                   "CSS", "SQL", "PDF", "USB", "GPS", "WiFi", "AI", "ML",
                   "NLP", "FBI", "CIA", "NSA", "Google", "Microsoft",
                   "Apple", "Amazon", "Python", "JavaScript", "Linux"}
        matches = self.ENGLISH_WORD_PATTERN.findall(target)
        for word in matches:
            if word not in allowed and word.upper() not in allowed:
                issues.append(QAIssue(
                    category="كلمة_غير_مترجمة",
                    severity="medium",
                    description=f"كلمة إنجليزية متروكة: '{word}'",
                    source_segment=word,
                    target_segment=word,
                    suggestion="يجب ترجمة هذه الكلمة أو تعريبها",
                ))
                self.stats["untranslated_detections"] += 1
        return issues

    def check_passive_voice(self, target: str) -> list[QAIssue]:
        """كشف المبني للمجهول الركيك."""
        issues = []
        for pattern, suggestion in self.PASSIVE_WRONG_PATTERNS:
            match = pattern.search(target)
            if match:
                issues.append(QAIssue(
                    category="مبني_للمجهول",
                    severity="medium",
                    description="أسلوب مبني للمجهول ركيك",
                    source_segment="",
                    target_segment=match.group(),
                    suggestion=suggestion,
                ))
                self.stats["passive_issues"] += 1
        return issues

    def check_weak_style(self, target: str) -> list[QAIssue]:
        """كشف الأساليب الركيكة."""
        issues = []
        for pattern, suggestion in self.WEAK_PATTERNS:
            match = pattern.search(target)
            if match:
                issues.append(QAIssue(
                    category="أسلوب_ضعيف",
                    severity="low",
                    description="أسلوب ركيك يمكن تحسينه",
                    source_segment="",
                    target_segment=match.group(),
                    suggestion=suggestion,
                ))
                self.stats["weak_style_issues"] += 1
        return issues

    def check_glossary_consistency(self, source: str, target: str) -> list[QAIssue]:
        """فحص تناسق المصطلحات مع المعجم."""
        issues = []
        source_lower = source.lower()
        for term, expected_translation in self.glossary.items():
            if term.lower() in source_lower:
                if expected_translation not in target:
                    issues.append(QAIssue(
                        category="تناسق_معجم",
                        severity="medium",
                        description=f"مصطلح '{term}' لم يُترجم حسب المعجم",
                        source_segment=term,
                        target_segment="",
                        suggestion=f"الترجمة المعتمدة: {expected_translation}",
                    ))
        return issues

    def check_discovered_rules(self, source: str, target: str) -> list[QAIssue]:
        """تطبيق القواعد المكتشفة من وكيل المكتشف."""
        issues = []
        for rule in self.discovered_rules:
            pattern = rule.get("pattern", "")
            desc = rule.get("description", "قاعدة مكتشفة")
            suggestion = rule.get("suggestion", "")
            if pattern and re.search(pattern, target):
                issues.append(QAIssue(
                    category="قاعدة_مكتشفة",
                    severity=rule.get("severity", "medium"),
                    description=desc,
                    source_segment="",
                    target_segment=re.search(pattern, target).group(),
                    suggestion=suggestion,
                ))
        return issues

    def calculate_score(self, issues: list[QAIssue]) -> float:
        """حساب الدرجة بناءً على المشاكل."""
        score = 100.0
        penalties = {
            "critical": 25.0,
            "high": 15.0,
            "medium": 8.0,
            "low": 3.0,
        }
        for issue in issues:
            score -= penalties.get(issue.severity, 5.0)
        return max(0.0, score)

    def evaluate(self, source: str, target: str) -> QAResult:
        """
        تقييم شامل للترجمة.

        Args:
            source: النص المصدر (الإنجليزي)
            target: النص المترجم (العربي)

        Returns:
            QAResult مع الدرجة والمشاكل والاقتراحات
        """
        all_issues = []

        # تشغيل كل الفحوصات
        all_issues.extend(self.check_literal_translation(source, target))
        all_issues.extend(self.check_untranslated_words(target))
        all_issues.extend(self.check_passive_voice(target))
        all_issues.extend(self.check_weak_style(target))
        all_issues.extend(self.check_glossary_consistency(source, target))
        all_issues.extend(self.check_discovered_rules(source, target))

        score = self.calculate_score(all_issues)

        # تحديث الإحصائيات
        self.stats["evaluations"] += 1
        self.stats["total_issues"] += len(all_issues)
        total = self.stats["evaluations"]
        self.stats["avg_score"] = (
            (self.stats["avg_score"] * (total - 1) + score) / total
        )

        metrics = {
            "issue_count": len(all_issues),
            "critical_count": sum(1 for i in all_issues if i.severity == "critical"),
            "high_count": sum(1 for i in all_issues if i.severity == "high"),
            "medium_count": sum(1 for i in all_issues if i.severity == "medium"),
            "low_count": sum(1 for i in all_issues if i.severity == "low"),
        }

        return QAResult(
            source=source,
            target=target,
            score=score,
            issues=all_issues,
            metrics=metrics,
        )

    def get_stats(self) -> dict:
        return self.stats.copy()
