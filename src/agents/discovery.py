"""
وكيل 4: المكتشف (Discovery Agent)
====================================
يراقب الوكلاء الثلاثة الأولين، يتعلّم من أخطائهم،
ويخترع خوارزميات جديدة لحل مشاكل اللغة العربية في الترجمة.
يعمل هجين — التحليل أوفلاين والاكتشاف المتقدم أونلاين.

الدورة:
  1. يجمع الأخطاء من كل الوكلاء
  2. يكشف الأنماط المتكررة
  3. يبني فرضية (لماذا يتكرر هذا الخطأ؟)
  4. يخترع قاعدة/خوارزمية جديدة
  5. يختبرها على بيانات سابقة
  6. يضيفها للنظام إذا نجحت
"""

import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from collections import Counter


@dataclass
class ErrorRecord:
    """سجل خطأ واحد من أي وكيل."""
    timestamp: str
    agent: str           # أي وكيل أنتج هذا الخطأ
    category: str        # نوع الخطأ
    source_text: str     # النص الأصلي
    target_text: str     # النص المترجم
    error_detail: str    # تفصيل الخطأ
    severity: str = "medium"


@dataclass
class Pattern:
    """نمط مكتشف من الأخطاء."""
    pattern_id: str
    description: str
    frequency: int           # كم مرة ظهر
    examples: list = field(default_factory=list)
    regex: str = ""          # التعبير النمطي المكتشف
    confidence: float = 0.0  # نسبة الثقة 0-1


@dataclass
class DiscoveredRule:
    """قاعدة مكتشفة جاهزة للتطبيق."""
    rule_id: str
    name: str
    description: str
    pattern: str             # regex للكشف
    replacement: str         # النص البديل (إن وُجد)
    suggestion: str          # اقتراح التصحيح
    severity: str            # خطورة المشكلة
    test_cases: list = field(default_factory=list)
    accuracy: float = 0.0   # نسبة الدقة بعد الاختبار
    created_at: str = ""
    source_pattern_id: str = ""


@dataclass
class Algorithm:
    """خوارزمية مولّدة لحل مشكلة معينة."""
    algo_id: str
    name: str
    description: str
    problem: str             # المشكلة التي تحلها
    rules: list = field(default_factory=list)  # قائمة القواعد
    accuracy: float = 0.0
    tests_passed: int = 0
    tests_total: int = 0
    created_at: str = ""
    version: int = 1


class DiscoveryAgent:
    """
    الوكيل الرابع — المكتشف.
    يراقب، يتعلّم، ويخترع خوارزميات جديدة.
    """

    # الحد الأدنى لتكرار النمط قبل اعتباره مشكلة حقيقية
    MIN_PATTERN_FREQUENCY = 3

    # الحد الأدنى للدقة لاعتماد قاعدة
    MIN_ACCURACY_THRESHOLD = 0.75

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.patterns_dir = self.data_dir / "patterns"
        self.algorithms_dir = self.data_dir / "algorithms"

        # إنشاء المجلدات
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        self.algorithms_dir.mkdir(parents=True, exist_ok=True)

        # تحميل البيانات الموجودة
        self.errors_log: list[ErrorRecord] = self._load_errors()
        self.discovered_patterns: list[Pattern] = self._load_patterns()
        self.discovered_rules: list[DiscoveredRule] = self._load_rules()
        self.algorithms: list[Algorithm] = self._load_algorithms()

        self.stats = {
            "errors_collected": len(self.errors_log),
            "patterns_discovered": len(self.discovered_patterns),
            "rules_generated": len(self.discovered_rules),
            "algorithms_created": len(self.algorithms),
            "accuracy_improvements": 0,
        }

    # ─── تحميل وحفظ البيانات ───

    def _load_json(self, filename: str) -> list:
        path = self.patterns_dir / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_json(self, filename: str, data: list):
        path = self.patterns_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_errors(self) -> list:
        return self._load_json("errors_log.json")

    def _load_patterns(self) -> list:
        raw = self._load_json("discovered_patterns.json")
        return [Pattern(**p) for p in raw] if raw else []

    def _load_rules(self) -> list:
        raw = self._load_json("discovered_rules.json")
        return [DiscoveredRule(**r) for r in raw] if raw else []

    def _load_algorithms(self) -> list:
        raw = self._load_json("algorithms.json")
        return [Algorithm(**a) for a in raw] if raw else []

    def save_all(self):
        """حفظ كل البيانات."""
        self._save_json("errors_log.json", self.errors_log)
        self._save_json("discovered_patterns.json",
                        [asdict(p) for p in self.discovered_patterns])
        self._save_json("discovered_rules.json",
                        [asdict(r) for r in self.discovered_rules])
        self._save_json("algorithms.json",
                        [asdict(a) for a in self.algorithms])
        # حفظ الإحصائيات
        self._save_json("stats.json", [self.stats])

    # ─── المرحلة 1: جمع الأخطاء ───

    def collect_error(self, agent: str, category: str,
                      source_text: str, target_text: str,
                      error_detail: str, severity: str = "medium"):
        """تسجيل خطأ جديد من أي وكيل."""
        record = ErrorRecord(
            timestamp=datetime.now().isoformat(),
            agent=agent,
            category=category,
            source_text=source_text,
            target_text=target_text,
            error_detail=error_detail,
            severity=severity,
        )
        self.errors_log.append(asdict(record))
        self.stats["errors_collected"] += 1

    def collect_from_normalizer(self, result):
        """جمع بيانات من وكيل المطبّع."""
        if result.was_modified:
            for change in result.changes:
                self.collect_error(
                    agent="normalizer",
                    category="normalization",
                    source_text=result.original,
                    target_text=result.normalized,
                    error_detail=change,
                    severity="low",
                )

    def collect_from_qa(self, result):
        """جمع بيانات من وكيل مقيّم الجودة."""
        for issue in result.issues:
            self.collect_error(
                agent="qa_evaluator",
                category=issue.category,
                source_text=result.source,
                target_text=result.target,
                error_detail=issue.description,
                severity=issue.severity,
            )

    def collect_from_bidi(self, result):
        """جمع بيانات من وكيل الاتجاهات."""
        if result.was_modified:
            for issue in result.issues:
                self.collect_error(
                    agent="bidi_fixer",
                    category=issue.issue_type,
                    source_text=result.original,
                    target_text=result.fixed,
                    error_detail=issue.description,
                    severity="low",
                )

    # ─── المرحلة 2: اكتشاف الأنماط ───

    def analyze_patterns(self) -> list[Pattern]:
        """تحليل الأخطاء واكتشاف الأنماط المتكررة."""
        # تجميع الأخطاء حسب النوع
        category_counter = Counter()
        category_examples = {}

        for error in self.errors_log:
            cat = error.get("category", "unknown")
            detail = error.get("error_detail", "")
            key = f"{cat}::{detail}"
            category_counter[key] += 1

            if key not in category_examples:
                category_examples[key] = []
            if len(category_examples[key]) < 5:  # أقصى 5 أمثلة
                category_examples[key].append({
                    "source": error.get("source_text", ""),
                    "target": error.get("target_text", ""),
                })

        # تحويل الأنماط المتكررة لكائنات Pattern
        new_patterns = []
        for key, freq in category_counter.most_common():
            if freq >= self.MIN_PATTERN_FREQUENCY:
                pattern_id = hashlib.md5(key.encode()).hexdigest()[:12]

                # تحقق أنه جديد
                existing_ids = {p.pattern_id for p in self.discovered_patterns}
                if pattern_id not in existing_ids:
                    cat, detail = key.split("::", 1)
                    pattern = Pattern(
                        pattern_id=pattern_id,
                        description=f"[{cat}] {detail}",
                        frequency=freq,
                        examples=category_examples.get(key, []),
                        confidence=min(freq / 10.0, 1.0),
                    )

                    # محاولة استخراج regex من الأمثلة
                    regex = self._extract_regex(pattern)
                    if regex:
                        pattern.regex = regex

                    new_patterns.append(pattern)
                    self.discovered_patterns.append(pattern)
                    self.stats["patterns_discovered"] += 1

        return new_patterns

    def _extract_regex(self, pattern: Pattern) -> str:
        """محاولة استخراج تعبير نمطي من أمثلة النمط."""
        if not pattern.examples:
            return ""

        targets = [ex.get("target", "") for ex in pattern.examples if ex.get("target")]
        if len(targets) < 2:
            return ""

        # استراتيجية بسيطة: البحث عن كلمات مشتركة
        words_sets = [set(t.split()) for t in targets]
        if not words_sets:
            return ""
        common = words_sets[0]
        for ws in words_sets[1:]:
            common &= ws

        if common:
            # بناء regex من الكلمات المشتركة
            escaped = [re.escape(w) for w in common]
            return r"(?:" + "|".join(escaped) + r")"

        return ""

    # ─── المرحلة 3: توليد القواعد ───

    def generate_rules(self) -> list[DiscoveredRule]:
        """توليد قواعد جديدة من الأنماط المكتشفة."""
        new_rules = []

        for pattern in self.discovered_patterns:
            if pattern.confidence < 0.5:
                continue

            # تحقق أنه لا توجد قاعدة مبنية على هذا النمط
            existing_sources = {r.source_pattern_id for r in self.discovered_rules}
            if pattern.pattern_id in existing_sources:
                continue

            rule = self._build_rule_from_pattern(pattern)
            if rule:
                # اختبار القاعدة
                accuracy = self._test_rule(rule)
                rule.accuracy = accuracy

                if accuracy >= self.MIN_ACCURACY_THRESHOLD:
                    self.discovered_rules.append(rule)
                    new_rules.append(rule)
                    self.stats["rules_generated"] += 1

        return new_rules

    def _build_rule_from_pattern(self, pattern: Pattern) -> Optional[DiscoveredRule]:
        """بناء قاعدة من نمط مكتشف."""
        if not pattern.regex:
            return None

        rule_id = f"rule_{pattern.pattern_id}"

        # بناء حالات اختبار من أمثلة النمط
        test_cases = []
        for ex in pattern.examples:
            if ex.get("source") and ex.get("target"):
                test_cases.append({
                    "input": ex["target"],
                    "should_match": True,
                })

        return DiscoveredRule(
            rule_id=rule_id,
            name=f"قاعدة مكتشفة: {pattern.description[:50]}",
            description=pattern.description,
            pattern=pattern.regex,
            replacement="",
            suggestion=f"مشكلة مكتشفة تلقائياً (تكررت {pattern.frequency} مرة)",
            severity="medium" if pattern.frequency < 10 else "high",
            test_cases=test_cases,
            created_at=datetime.now().isoformat(),
            source_pattern_id=pattern.pattern_id,
        )

    def _test_rule(self, rule: DiscoveredRule) -> float:
        """اختبار قاعدة على حالات الاختبار."""
        if not rule.test_cases:
            return 0.0

        passed = 0
        total = len(rule.test_cases)

        for case in rule.test_cases:
            text = case.get("input", "")
            should_match = case.get("should_match", True)

            try:
                match = bool(re.search(rule.pattern, text))
                if match == should_match:
                    passed += 1
            except re.error:
                pass

        return passed / total if total > 0 else 0.0

    # ─── المرحلة 4: بناء الخوارزميات ───

    def build_algorithm(self, problem_name: str,
                        related_categories: list[str]) -> Optional[Algorithm]:
        """
        بناء خوارزمية من مجموعة قواعد متعلقة بمشكلة معينة.

        Args:
            problem_name: اسم المشكلة (مثل "الترجمة الحرفية")
            related_categories: أنواع الأخطاء المتعلقة

        Returns:
            Algorithm جديدة أو None
        """
        # جمع القواعد المتعلقة
        related_rules = []
        for rule in self.discovered_rules:
            for cat in related_categories:
                if cat in rule.description:
                    related_rules.append(asdict(rule))
                    break

        if not related_rules:
            return None

        algo_id = hashlib.md5(problem_name.encode()).hexdigest()[:12]
        algo = Algorithm(
            algo_id=algo_id,
            name=f"خوارزمية: {problem_name}",
            description=f"خوارزمية مولّدة تلقائياً لحل مشكلة {problem_name}",
            problem=problem_name,
            rules=related_rules,
            created_at=datetime.now().isoformat(),
        )

        # اختبار الخوارزمية
        total, passed = self._test_algorithm(algo)
        algo.tests_total = total
        algo.tests_passed = passed
        algo.accuracy = passed / total if total > 0 else 0.0

        self.algorithms.append(algo)
        self.stats["algorithms_created"] += 1

        return algo

    def _test_algorithm(self, algo: Algorithm) -> tuple[int, int]:
        """اختبار خوارزمية على كل حالات الاختبار."""
        total = 0
        passed = 0
        for rule_data in algo.rules:
            for case in rule_data.get("test_cases", []):
                total += 1
                text = case.get("input", "")
                should_match = case.get("should_match", True)
                try:
                    match = bool(re.search(rule_data.get("pattern", ""), text))
                    if match == should_match:
                        passed += 1
                except re.error:
                    pass
        return total, passed

    # ─── الدورة الكاملة ───

    def run_discovery_cycle(self) -> dict:
        """
        تشغيل دورة اكتشاف كاملة:
        1. تحليل الأنماط
        2. توليد القواعد
        3. حفظ كل شيء

        Returns:
            ملخص الدورة
        """
        new_patterns = self.analyze_patterns()
        new_rules = self.generate_rules()
        self.save_all()

        return {
            "new_patterns": len(new_patterns),
            "new_rules": len(new_rules),
            "total_patterns": len(self.discovered_patterns),
            "total_rules": len(self.discovered_rules),
            "total_algorithms": len(self.algorithms),
            "total_errors": len(self.errors_log),
        }

    def export_rules_for_agents(self) -> list[dict]:
        """تصدير القواعد بتنسيق يفهمه الوكلاء الآخرون."""
        exported = []
        for rule in self.discovered_rules:
            if rule.accuracy >= self.MIN_ACCURACY_THRESHOLD:
                exported.append({
                    "pattern": rule.pattern,
                    "replacement": rule.replacement,
                    "description": rule.description,
                    "suggestion": rule.suggestion,
                    "severity": rule.severity,
                })
        return exported

    def get_stats(self) -> dict:
        return self.stats.copy()

    def get_insights(self) -> dict:
        """تقرير بأهم الاكتشافات."""
        top_patterns = sorted(
            self.discovered_patterns,
            key=lambda p: p.frequency,
            reverse=True,
        )[:10]

        top_rules = sorted(
            self.discovered_rules,
            key=lambda r: r.accuracy,
            reverse=True,
        )[:10]

        return {
            "top_patterns": [
                {"description": p.description, "frequency": p.frequency}
                for p in top_patterns
            ],
            "top_rules": [
                {"name": r.name, "accuracy": r.accuracy}
                for r in top_rules
            ],
            "algorithms_count": len(self.algorithms),
            "total_errors_analyzed": len(self.errors_log),
        }
