"""
وكيل 2: مقيّم الجودة (QA Evaluator Agent)
============================================
يُقيّم جودة الترجمة من الإنجليزية للعربية.
يعمل بنظام تفاعلي — يعرض المشاكل، يأخذ موافقة المستخدم، يطبّق، ثم يتحقق.

الدورة التفاعلية:
  1. تقييم أولي → يكشف كل المشاكل
  2. عرض للمستخدم → كل مشكلة + اقتراح
  3. قرار المستخدم → اعتمد / ارفض / عدّل
  4. تطبيق التعديلات → ينفّذ المعتمد فقط
  5. تحقق شامل → يعيد فحص النص كله بعد التعديل
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable
from enum import Enum


class UserDecision(Enum):
    """قرار المستخدم بخصوص مشكلة."""
    APPROVE = "approve"       # اعتمد التصحيح المقترح
    REJECT = "reject"         # ارفض — لا تغيّر
    MODIFY = "modify"         # عدّل — المستخدم يكتب تصحيحه


@dataclass
class QAIssue:
    """مشكلة جودة واحدة."""
    issue_id: int = 0          # رقم تسلسلي
    category: str = ""         # نوع المشكلة
    severity: str = ""         # خطورة: low, medium, high, critical
    description: str = ""      # وصف المشكلة
    source_segment: str = ""   # الجزء من النص المصدر
    target_segment: str = ""   # الجزء من النص المترجم
    suggestion: str = ""       # اقتراح التصحيح
    # حقول التفاعل
    user_decision: Optional[str] = None   # قرار المستخدم
    user_correction: Optional[str] = None # تصحيح المستخدم (إذا عدّل)
    applied: bool = False                  # هل تم تطبيقه


@dataclass
class VerificationResult:
    """نتيجة التحقق بعد تطبيق التعديلات."""
    text_before: str
    text_after: str
    remaining_issues: list = field(default_factory=list)
    new_issues: list = field(default_factory=list)
    fixes_verified: int = 0
    all_clear: bool = False


@dataclass
class QAResult:
    """نتيجة تقييم الجودة الكاملة."""
    source: str
    target: str
    score: float              # 0-100
    issues: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    # حقول الدورة التفاعلية
    approved_text: str = ""            # النص بعد تطبيق التعديلات المعتمدة
    verification: Optional[VerificationResult] = None
    final_score: float = 0.0           # الدرجة بعد التحقق

    @property
    def grade(self) -> str:
        s = self.final_score if self.final_score > 0 else self.score
        if s >= 90:
            return "ممتاز"
        elif s >= 75:
            return "جيد"
        elif s >= 60:
            return "مقبول"
        elif s >= 40:
            return "ضعيف"
        return "مرفوض"

    @property
    def passed(self) -> bool:
        s = self.final_score if self.final_score > 0 else self.score
        return s >= 60


class QAEvaluatorAgent:
    """
    الوكيل الثاني — مقيّم الجودة التفاعلي.

    الدورة:
      evaluate()          → تقييم أولي
      propose_fixes()     → عرض المشاكل والاقتراحات
      submit_decisions()  → المستخدم يقرر لكل مشكلة
      apply_approved()    → تطبيق المعتمد على النص
      verify()            → تحقق شامل من النص النهائي

    أو بخطوة واحدة:
      interactive_review() → الدورة الكاملة مع callback
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
        self._issue_counter = 0
        self.stats = {
            "evaluations": 0,
            "avg_score": 0.0,
            "total_issues": 0,
            "literal_detections": 0,
            "untranslated_detections": 0,
            "passive_issues": 0,
            "weak_style_issues": 0,
            "user_approvals": 0,
            "user_rejections": 0,
            "user_modifications": 0,
            "fixes_applied": 0,
            "verifications_passed": 0,
            "verifications_failed": 0,
        }
        if glossary_path:
            self._load_glossary(glossary_path)
        if discovered_rules_path:
            self._load_discovered_rules(discovered_rules_path)

    def _load_glossary(self, path: str):
        gpath = Path(path)
        if gpath.exists():
            with open(gpath, "r", encoding="utf-8") as f:
                self.glossary = json.load(f)

    def _load_discovered_rules(self, path: str):
        rpath = Path(path)
        if rpath.exists():
            with open(rpath, "r", encoding="utf-8") as f:
                self.discovered_rules = json.load(f)

    def _next_id(self) -> int:
        self._issue_counter += 1
        return self._issue_counter

    # ═══════════════════════════════════════════
    # المرحلة 1: التقييم الأولي (كشف المشاكل)
    # ═══════════════════════════════════════════

    def check_literal_translation(self, source: str, target: str) -> list[QAIssue]:
        issues = []
        source_lower = source.lower()
        for phrase, translations in self.LITERAL_TRANSLATIONS.items():
            if phrase in source_lower and translations["wrong"] in target:
                issues.append(QAIssue(
                    issue_id=self._next_id(),
                    category="ترجمة_حرفية",
                    severity="high",
                    description=f"ترجمة حرفية لـ '{phrase}'",
                    source_segment=phrase,
                    target_segment=translations["wrong"],
                    suggestion=translations["correct"],
                ))
                self.stats["literal_detections"] += 1
        return issues

    def check_untranslated_words(self, target: str) -> list[QAIssue]:
        issues = []
        allowed = {"API", "URL", "HTTP", "HTTPS", "JSON", "XML", "HTML",
                   "CSS", "SQL", "PDF", "USB", "GPS", "WiFi", "AI", "ML",
                   "NLP", "FBI", "CIA", "NSA", "Google", "Microsoft",
                   "Apple", "Amazon", "Python", "JavaScript", "Linux"}
        matches = self.ENGLISH_WORD_PATTERN.findall(target)
        for word in matches:
            if word not in allowed and word.upper() not in allowed:
                issues.append(QAIssue(
                    issue_id=self._next_id(),
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
        issues = []
        for pattern, suggestion in self.PASSIVE_WRONG_PATTERNS:
            match = pattern.search(target)
            if match:
                issues.append(QAIssue(
                    issue_id=self._next_id(),
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
        issues = []
        for pattern, suggestion in self.WEAK_PATTERNS:
            match = pattern.search(target)
            if match:
                issues.append(QAIssue(
                    issue_id=self._next_id(),
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
        issues = []
        source_lower = source.lower()
        for term, expected_translation in self.glossary.items():
            if term.lower() in source_lower:
                if expected_translation not in target:
                    issues.append(QAIssue(
                        issue_id=self._next_id(),
                        category="تناسق_معجم",
                        severity="medium",
                        description=f"مصطلح '{term}' لم يُترجم حسب المعجم",
                        source_segment=term,
                        target_segment="",
                        suggestion=f"الترجمة المعتمدة: {expected_translation}",
                    ))
        return issues

    def check_discovered_rules(self, source: str, target: str) -> list[QAIssue]:
        issues = []
        for rule in self.discovered_rules:
            pattern = rule.get("pattern", "")
            desc = rule.get("description", "قاعدة مكتشفة")
            suggestion = rule.get("suggestion", "")
            if pattern and re.search(pattern, target):
                issues.append(QAIssue(
                    issue_id=self._next_id(),
                    category="قاعدة_مكتشفة",
                    severity=rule.get("severity", "medium"),
                    description=desc,
                    source_segment="",
                    target_segment=re.search(pattern, target).group(),
                    suggestion=suggestion,
                ))
        return issues

    def calculate_score(self, issues: list[QAIssue]) -> float:
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
        المرحلة 1: تقييم أولي — يكشف كل المشاكل.

        Args:
            source: النص المصدر (الإنجليزي)
            target: النص المترجم (العربي)

        Returns:
            QAResult مع المشاكل المكتشفة (بدون تطبيق أي تعديل)
        """
        all_issues = []
        all_issues.extend(self.check_literal_translation(source, target))
        all_issues.extend(self.check_untranslated_words(target))
        all_issues.extend(self.check_passive_voice(target))
        all_issues.extend(self.check_weak_style(target))
        all_issues.extend(self.check_glossary_consistency(source, target))
        all_issues.extend(self.check_discovered_rules(source, target))

        score = self.calculate_score(all_issues)

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

    # ═══════════════════════════════════════════
    # المرحلة 2: عرض المشاكل (Propose Fixes)
    # ═══════════════════════════════════════════

    def propose_fixes(self, qa_result: QAResult) -> list[dict]:
        """
        المرحلة 2: تحويل المشاكل لاقتراحات واضحة للمستخدم.

        Returns:
            قائمة اقتراحات بتنسيق سهل القراءة
        """
        proposals = []
        for issue in qa_result.issues:
            proposal = {
                "issue_id": issue.issue_id,
                "severity": issue.severity,
                "severity_ar": self._severity_label(issue.severity),
                "category": issue.category,
                "description": issue.description,
                "current_text": issue.target_segment,
                "suggested_fix": issue.suggestion,
                "source_ref": issue.source_segment,
                "awaiting_decision": True,
            }
            proposals.append(proposal)
        return proposals

    def _severity_label(self, severity: str) -> str:
        labels = {
            "critical": "حرج 🔴",
            "high": "عالي 🟠",
            "medium": "متوسط 🟡",
            "low": "منخفض 🟢",
        }
        return labels.get(severity, severity)

    # ═══════════════════════════════════════════
    # المرحلة 3: استلام قرارات المستخدم
    # ═══════════════════════════════════════════

    def submit_decisions(self, qa_result: QAResult,
                         decisions: list[dict]) -> QAResult:
        """
        المرحلة 3: المستخدم يقرر لكل مشكلة.

        Args:
            qa_result: نتيجة التقييم
            decisions: قائمة القرارات:
                [{"issue_id": 1, "decision": "approve"},
                 {"issue_id": 2, "decision": "reject"},
                 {"issue_id": 3, "decision": "modify", "correction": "النص البديل"}]

        Returns:
            QAResult محدّث بالقرارات
        """
        decision_map = {d["issue_id"]: d for d in decisions}

        for issue in qa_result.issues:
            d = decision_map.get(issue.issue_id)
            if d:
                issue.user_decision = d["decision"]
                if d["decision"] == UserDecision.APPROVE.value:
                    self.stats["user_approvals"] += 1
                elif d["decision"] == UserDecision.REJECT.value:
                    self.stats["user_rejections"] += 1
                elif d["decision"] == UserDecision.MODIFY.value:
                    issue.user_correction = d.get("correction", "")
                    self.stats["user_modifications"] += 1

        return qa_result

    # ═══════════════════════════════════════════
    # المرحلة 4: تطبيق التعديلات المعتمدة
    # ═══════════════════════════════════════════

    def apply_approved(self, qa_result: QAResult) -> QAResult:
        """
        المرحلة 4: تطبيق التعديلات المعتمدة فقط على النص.

        Returns:
            QAResult مع approved_text (النص بعد التعديل)
        """
        text = qa_result.target

        for issue in qa_result.issues:
            if issue.user_decision == UserDecision.APPROVE.value:
                # تطبيق الاقتراح
                if issue.target_segment and issue.suggestion:
                    new_text = text.replace(issue.target_segment, issue.suggestion, 1)
                    if new_text != text:
                        text = new_text
                        issue.applied = True
                        self.stats["fixes_applied"] += 1

            elif issue.user_decision == UserDecision.MODIFY.value:
                # تطبيق تصحيح المستخدم
                if issue.target_segment and issue.user_correction:
                    new_text = text.replace(
                        issue.target_segment, issue.user_correction, 1
                    )
                    if new_text != text:
                        text = new_text
                        issue.applied = True
                        self.stats["fixes_applied"] += 1

            # REJECT = لا نفعل شيئاً

        qa_result.approved_text = text
        return qa_result

    # ═══════════════════════════════════════════
    # المرحلة 5: التحقق الشامل
    # ═══════════════════════════════════════════

    def verify(self, qa_result: QAResult) -> QAResult:
        """
        المرحلة 5: إعادة فحص النص بعد تطبيق التعديلات.
        يتحقق أن:
          1. التعديلات المعتمدة طُبّقت فعلاً
          2. لم تظهر مشاكل جديدة
          3. النص النهائي سليم

        Returns:
            QAResult محدّث بنتيجة التحقق والدرجة النهائية
        """
        approved_text = qa_result.approved_text or qa_result.target
        source = qa_result.source

        # 1. تحقق أن الإصلاحات طُبّقت
        fixes_verified = 0
        for issue in qa_result.issues:
            if issue.applied:
                # تحقق أن النص القديم لم يعد موجوداً
                if issue.target_segment not in approved_text:
                    fixes_verified += 1

        # 2. إعادة تقييم النص الجديد
        re_eval = self._raw_evaluate(source, approved_text)
        remaining_issues = re_eval["issues"]
        new_issues = []

        # 3. كشف المشاكل الجديدة (لم تكن في التقييم الأول)
        original_segments = {i.target_segment for i in qa_result.issues}
        for issue in remaining_issues:
            if issue.target_segment not in original_segments:
                new_issues.append(issue)

        all_clear = len(remaining_issues) == 0

        verification = VerificationResult(
            text_before=qa_result.target,
            text_after=approved_text,
            remaining_issues=remaining_issues,
            new_issues=new_issues,
            fixes_verified=fixes_verified,
            all_clear=all_clear,
        )

        qa_result.verification = verification
        qa_result.final_score = self.calculate_score(remaining_issues)

        if all_clear:
            self.stats["verifications_passed"] += 1
        else:
            self.stats["verifications_failed"] += 1

        return qa_result

    def _raw_evaluate(self, source: str, target: str) -> dict:
        """تقييم خام بدون تحديث الإحصائيات."""
        issues = []
        issues.extend(self.check_literal_translation(source, target))
        issues.extend(self.check_untranslated_words(target))
        issues.extend(self.check_passive_voice(target))
        issues.extend(self.check_weak_style(target))
        issues.extend(self.check_glossary_consistency(source, target))
        # نتخطى discovered_rules لتفادي تحديث العداد
        return {"issues": issues, "score": self.calculate_score(issues)}

    # ═══════════════════════════════════════════
    # الدورة الكاملة التفاعلية
    # ═══════════════════════════════════════════

    def interactive_review(self, source: str, target: str,
                           decision_callback: Callable) -> QAResult:
        """
        الدورة الكاملة في خطوة واحدة مع callback.

        Args:
            source: النص المصدر
            target: النص المترجم
            decision_callback: دالة تستقبل الاقتراحات وتعيد القرارات
                callback(proposals: list[dict]) -> list[dict]
                كل قرار: {"issue_id": int, "decision": "approve"|"reject"|"modify",
                          "correction": "..." (اختياري)}

        Returns:
            QAResult كامل بعد كل المراحل
        """
        # المرحلة 1: تقييم
        qa_result = self.evaluate(source, target)

        if not qa_result.issues:
            # لا مشاكل — النص ممتاز
            qa_result.approved_text = target
            qa_result.final_score = qa_result.score
            return qa_result

        # المرحلة 2: اقتراحات
        proposals = self.propose_fixes(qa_result)

        # المرحلة 3: قرارات المستخدم
        decisions = decision_callback(proposals)
        qa_result = self.submit_decisions(qa_result, decisions)

        # المرحلة 4: تطبيق
        qa_result = self.apply_approved(qa_result)

        # المرحلة 5: تحقق
        qa_result = self.verify(qa_result)

        return qa_result

    def auto_review(self, source: str, target: str,
                    auto_approve_severity: Optional[list[str]] = None
                    ) -> QAResult:
        """
        دورة تلقائية — تعتمد تلقائياً حسب خطورة المشكلة.
        مفيدة للمعالجة الدفعية عندما لا يكون المستخدم متاحاً.

        Args:
            source: النص المصدر
            target: النص المترجم
            auto_approve_severity: مستويات الخطورة للاعتماد التلقائي
                                   مثال: ["high", "critical"]
        """
        if auto_approve_severity is None:
            auto_approve_severity = ["high", "critical"]

        def auto_callback(proposals):
            decisions = []
            for p in proposals:
                if p["severity"] in auto_approve_severity:
                    decisions.append({
                        "issue_id": p["issue_id"],
                        "decision": "approve",
                    })
                else:
                    decisions.append({
                        "issue_id": p["issue_id"],
                        "decision": "reject",
                    })
            return decisions

        return self.interactive_review(source, target, auto_callback)

    def get_stats(self) -> dict:
        return self.stats.copy()
