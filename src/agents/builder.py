"""
وكيل 6: المُنتِج (Builder Agent)
==================================
يراقب عمل كل الوكلاء، يتعلّم من وكيل المكتشف،
ويستخدم الخوارزميات الناتجة لبناء تطبيقات تحل مشاكل اللغة العربية.

⚠️ قواعد أساسية:
  - لا يُصدر أي تطبيق بدون موافقة المستخدم
  - كل التطبيقات تُنشر بسرية تامة (محلي فقط)
  - المستخدم يرى التطبيق كاملاً قبل أي قرار

الدورة:
  1. يراقب كل الوكلاء ويجمع الإحصائيات
  2. يتعلّم من اكتشافات وكيل المكتشف
  3. يأخذ الخوارزميات الناجحة
  4. يبني منها تطبيقات/أدوات مستقلة
  5. يعرض التطبيق على المستخدم ← المستخدم يوافق أو يرفض
  6. يُصدر بسرية فقط بعد الموافقة
"""

import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from enum import Enum


class ReleaseDecision(Enum):
    """قرار المستخدم بخصوص إصدار تطبيق."""
    APPROVE = "approve"        # وافق — انشره بسرية
    REJECT = "reject"          # ارفض — لا تنشره
    MODIFY = "modify"          # عدّل أولاً ثم أعد العرض
    DEFER = "defer"            # أجّل — مو الحين


class PrivacyLevel(Enum):
    """مستوى السرية."""
    LOCAL_ONLY = "local_only"           # محلي فقط — لا يخرج من الجهاز
    PRIVATE_EXPORT = "private_export"   # تصدير مشفّر خاص
    RESTRICTED = "restricted"           # مقيّد — أشخاص محددون فقط


@dataclass
class AppSpec:
    """مواصفات تطبيق واحد."""
    app_id: str
    name: str
    name_ar: str
    description: str
    problem_solved: str
    source_algorithms: list = field(default_factory=list)
    rules: list = field(default_factory=list)
    version: int = 1
    created_at: str = ""
    updated_at: str = ""
    status: str = "draft"          # draft, testing, awaiting_approval, released, rejected
    test_results: dict = field(default_factory=dict)
    # حقول الموافقة والسرية
    privacy_level: str = "local_only"
    user_decision: Optional[str] = None
    user_notes: str = ""
    approved_at: str = ""
    approved_by: str = ""


@dataclass
class ReleaseProposal:
    """عرض تطبيق للمستخدم قبل الإصدار."""
    app_id: str
    name_ar: str
    description: str
    problem_solved: str
    rules_count: int
    accuracy: float
    privacy_level: str
    test_summary: dict = field(default_factory=dict)
    sample_rules: list = field(default_factory=list)


@dataclass
class AppTestResult:
    """نتيجة اختبار تطبيق."""
    app_id: str
    total_tests: int
    passed: int
    failed: int
    accuracy: float
    details: list = field(default_factory=list)


@dataclass
class BuilderInsight:
    """ملاحظة من المُنتِج عن أداء النظام."""
    timestamp: str
    insight_type: str
    description: str
    data: dict = field(default_factory=dict)
    action_taken: str = ""


class BuilderAgent:
    """
    الوكيل السادس — المُنتِج.
    يبني تطبيقات ولا يُصدر شيئاً بدون إذن المستخدم.
    كل شيء يبقى سري ومحلي.
    """

    APP_TEMPLATES = {
        "spellchecker": {
            "name": "Arabic Spellchecker",
            "name_ar": "المصحح الإملائي العربي",
            "description": "مصحح إملائي يكتشف ويصلح الأخطاء الشائعة في الكتابة العربية",
            "categories": ["normalization", "taa_marbuta_fix", "hamza_normalization"],
        },
        "translation_qa": {
            "name": "Translation Quality Analyzer",
            "name_ar": "محلل جودة الترجمة",
            "description": "أداة تقيّم جودة الترجمة من الإنجليزية للعربية وتقترح تحسينات",
            "categories": ["ترجمة_حرفية", "كلمة_غير_مترجمة", "مبني_للمجهول", "أسلوب_ضعيف"],
        },
        "bidi_tool": {
            "name": "BiDi Text Fixer",
            "name_ar": "مصلح اتجاهات النص",
            "description": "أداة تصلح مشاكل اتجاه النص في المحتوى المختلط عربي-إنجليزي",
            "categories": ["latin_isolation", "number_fix", "punctuation_direction"],
        },
        "smart_glossary": {
            "name": "Smart Arabic Glossary",
            "name_ar": "المعجم الذكي",
            "description": "معجم يتطوّر تلقائياً من أخطاء الترجمة ويقترح المصطلحات الصحيحة",
            "categories": ["تناسق_معجم", "ترجمة_حرفية"],
        },
        "arabic_style": {
            "name": "Arabic Style Corrector",
            "name_ar": "مصحح الأسلوب العربي",
            "description": "أداة تكتشف الأساليب الركيكة في النص العربي وتقترح بدائل فصيحة",
            "categories": ["أسلوب_ضعيف", "مبني_للمجهول"],
        },
    }

    def __init__(self, data_dir: str = "data", discovery_agent=None,
                 release_callback: Optional[Callable] = None):
        self.data_dir = Path(data_dir)
        self.apps_dir = self.data_dir / "apps"
        self.apps_dir.mkdir(parents=True, exist_ok=True)

        self.discovery = discovery_agent
        self.release_callback = release_callback
        self.apps: list[AppSpec] = self._load_apps()
        self.insights: list[BuilderInsight] = self._load_insights()

        self.stats = {
            "apps_built": len(self.apps),
            "apps_released": sum(1 for a in self.apps if a.status == "released"),
            "apps_testing": sum(1 for a in self.apps if a.status == "testing"),
            "apps_awaiting": sum(1 for a in self.apps if a.status == "awaiting_approval"),
            "apps_rejected": sum(1 for a in self.apps if a.status == "rejected"),
            "insights_generated": len(self.insights),
            "total_rules_deployed": sum(len(a.rules) for a in self.apps if a.status == "released"),
            "observation_cycles": 0,
            "user_approvals": 0,
            "user_rejections": 0,
        }

    # ─── تحميل وحفظ ───

    def _load_json(self, filename: str) -> list:
        path = self.apps_dir / filename
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_json(self, filename: str, data):
        path = self.apps_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_apps(self) -> list[AppSpec]:
        raw = self._load_json("apps_registry.json")
        return [AppSpec(**a) for a in raw] if raw else []

    def _load_insights(self) -> list[BuilderInsight]:
        raw = self._load_json("builder_insights.json")
        return [BuilderInsight(**i) for i in raw] if raw else []

    def save_all(self):
        self._save_json("apps_registry.json",
                        [asdict(a) for a in self.apps])
        self._save_json("builder_insights.json",
                        [asdict(i) for i in self.insights])
        self._save_json("builder_stats.json", self.stats)

    # ─── المرحلة 1: المراقبة ───

    def observe_system(self, agent_stats: dict[str, dict]) -> list[BuilderInsight]:
        new_insights = []
        self.stats["observation_cycles"] += 1

        normalizer_stats = agent_stats.get("normalizer", {})
        if normalizer_stats.get("extra_rules_applied", 0) > 0:
            new_insights.append(BuilderInsight(
                timestamp=datetime.now().isoformat(),
                insight_type="improvement",
                description="وكيل المطبّع بدأ يستخدم قواعد مكتشفة — النظام يتطوّر",
                data={"extra_rules": normalizer_stats.get("extra_rules_applied")},
            ))

        qa_stats = agent_stats.get("qa_evaluator", {})
        avg_score = qa_stats.get("avg_score", 0)
        if avg_score > 0 and avg_score < 70:
            new_insights.append(BuilderInsight(
                timestamp=datetime.now().isoformat(),
                insight_type="opportunity",
                description=f"متوسط جودة الترجمة {avg_score:.1f}% — فرصة لبناء أداة تحسين",
                data={"avg_score": avg_score},
            ))

        discovery_stats = agent_stats.get("discovery", {})
        if discovery_stats.get("patterns_discovered", 0) > 5:
            new_insights.append(BuilderInsight(
                timestamp=datetime.now().isoformat(),
                insight_type="opportunity",
                description="عدد كافٍ من الأنماط لبناء تطبيق جديد",
                data={"patterns": discovery_stats.get("patterns_discovered")},
            ))

        literal_count = qa_stats.get("literal_detections", 0)
        if literal_count > 10:
            new_insights.append(BuilderInsight(
                timestamp=datetime.now().isoformat(),
                insight_type="gap",
                description=f"مشكلة الترجمة الحرفية مستمرة ({literal_count} حالة) — يلزم تطبيق متخصص",
                data={"literal_count": literal_count},
            ))

        self.insights.extend(new_insights)
        self.stats["insights_generated"] += len(new_insights)
        return new_insights

    # ─── المرحلة 2: التعلّم من المكتشف ───

    def learn_from_discovery(self) -> dict:
        if not self.discovery:
            return {"status": "no_discovery_agent", "learned": 0}

        exported_rules = self.discovery.export_rules_for_agents()
        learned_rules = len(exported_rules)

        algorithms = self.discovery.algorithms
        learned_algorithms = len(algorithms)

        discovery_insights = self.discovery.get_insights()

        return {
            "status": "learned",
            "rules_available": learned_rules,
            "algorithms_available": learned_algorithms,
            "top_patterns": discovery_insights.get("top_patterns", [])[:5],
        }

    # ─── المرحلة 3: بناء التطبيقات ───

    def build_app(self, app_type: str,
                  custom_rules: Optional[list] = None) -> Optional[AppSpec]:
        template = self.APP_TEMPLATES.get(app_type)
        if not template:
            return None

        app_id = hashlib.md5(
            f"{app_type}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        rules = []

        if self.discovery:
            for rule in self.discovery.discovered_rules:
                if rule.accuracy >= 0.75:
                    for cat in template["categories"]:
                        if cat in rule.description:
                            rules.append(asdict(rule))
                            break

        if custom_rules:
            rules.extend(custom_rules)

        source_algos = []
        if self.discovery:
            for algo in self.discovery.algorithms:
                for cat in template["categories"]:
                    if cat in algo.problem:
                        source_algos.append(algo.algo_id)
                        break

        now = datetime.now().isoformat()
        app = AppSpec(
            app_id=app_id,
            name=template["name"],
            name_ar=template["name_ar"],
            description=template["description"],
            problem_solved=f"يحل مشاكل: {', '.join(template['categories'])}",
            source_algorithms=source_algos,
            rules=rules,
            created_at=now,
            updated_at=now,
            status="draft",
            privacy_level=PrivacyLevel.LOCAL_ONLY.value,
        )

        self.apps.append(app)
        self.stats["apps_built"] += 1

        self._add_insight(
            "improvement",
            f"تم بناء تطبيق جديد: {template['name_ar']}",
            {"app_id": app_id, "rules_count": len(rules)},
            f"بناء {template['name_ar']}",
        )

        return app

    def build_custom_app(self, name: str, name_ar: str,
                         description: str, problem: str,
                         categories: list[str]) -> Optional[AppSpec]:
        app_id = hashlib.md5(
            f"custom_{name}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        rules = []
        if self.discovery:
            for rule in self.discovery.discovered_rules:
                if rule.accuracy >= 0.75:
                    for cat in categories:
                        if cat in rule.description:
                            rules.append(asdict(rule))
                            break

        now = datetime.now().isoformat()
        app = AppSpec(
            app_id=app_id,
            name=name,
            name_ar=name_ar,
            description=description,
            problem_solved=problem,
            rules=rules,
            created_at=now,
            updated_at=now,
            status="draft",
            privacy_level=PrivacyLevel.LOCAL_ONLY.value,
        )

        self.apps.append(app)
        self.stats["apps_built"] += 1
        return app

    # ─── المرحلة 4: اختبار التطبيقات ───

    def test_app(self, app_id: str,
                 test_data: Optional[list[dict]] = None) -> AppTestResult:
        app = self._get_app(app_id)
        if not app:
            return AppTestResult(
                app_id=app_id, total_tests=0, passed=0, failed=0,
                accuracy=0.0, details=["التطبيق غير موجود"],
            )

        total = 0
        passed = 0
        details = []

        for rule in app.rules:
            pattern = rule.get("pattern", "")
            test_cases = rule.get("test_cases", [])

            for case in test_cases:
                total += 1
                text = case.get("input", "")
                should_match = case.get("should_match", True)

                try:
                    match = bool(re.search(pattern, text))
                    if match == should_match:
                        passed += 1
                    else:
                        details.append(f"فشل: '{text[:30]}...' — متوقع {should_match}")
                except re.error as e:
                    details.append(f"خطأ regex: {e}")

        if test_data:
            for td in test_data:
                total += 1
                text = td.get("input", "")
                matched_any = False
                for rule in app.rules:
                    pattern = rule.get("pattern", "")
                    try:
                        if re.search(pattern, text):
                            matched_any = True
                            break
                    except re.error:
                        pass
                if matched_any == td.get("should_detect", True):
                    passed += 1

        accuracy = passed / total if total > 0 else 0.0

        result = AppTestResult(
            app_id=app_id,
            total_tests=total,
            passed=passed,
            failed=total - passed,
            accuracy=accuracy,
            details=details,
        )

        app.test_results = asdict(result)
        if accuracy >= 0.75:
            app.status = "testing"
            self.stats["apps_testing"] = sum(
                1 for a in self.apps if a.status == "testing"
            )

        return result

    # ═══════════════════════════════════════════
    # المرحلة 5: طلب الموافقة قبل النشر
    # ═══════════════════════════════════════════

    def prepare_release_proposal(self, app_id: str) -> Optional[ReleaseProposal]:
        """
        تجهيز عرض التطبيق للمستخدم قبل النشر.
        يعرض كل تفاصيل التطبيق ليقرر المستخدم.
        """
        app = self._get_app(app_id)
        if not app:
            return None

        # عيّنة من القواعد للعرض (أول 5)
        sample_rules = []
        for rule in app.rules[:5]:
            sample_rules.append({
                "pattern": rule.get("pattern", ""),
                "description": rule.get("description", ""),
                "suggestion": rule.get("suggestion", ""),
                "accuracy": rule.get("accuracy", 0),
            })

        return ReleaseProposal(
            app_id=app.app_id,
            name_ar=app.name_ar,
            description=app.description,
            problem_solved=app.problem_solved,
            rules_count=len(app.rules),
            accuracy=app.test_results.get("accuracy", 0)
            if isinstance(app.test_results, dict) else 0,
            privacy_level=app.privacy_level,
            test_summary=app.test_results if isinstance(app.test_results, dict) else {},
            sample_rules=sample_rules,
        )

    def submit_release_decision(self, app_id: str, decision: str,
                                notes: str = "",
                                approved_by: str = "") -> dict:
        """
        استلام قرار المستخدم بخصوص إصدار التطبيق.

        Args:
            app_id: معرف التطبيق
            decision: "approve" | "reject" | "modify" | "defer"
            notes: ملاحظات المستخدم
            approved_by: من وافق

        Returns:
            نتيجة القرار
        """
        app = self._get_app(app_id)
        if not app:
            return {"status": "error", "message": "التطبيق غير موجود"}

        app.user_decision = decision
        app.user_notes = notes
        now = datetime.now().isoformat()

        if decision == ReleaseDecision.APPROVE.value:
            # ✓ المستخدم وافق — انشره بسرية
            app.status = "released"
            app.privacy_level = PrivacyLevel.LOCAL_ONLY.value  # دائماً سري
            app.approved_at = now
            app.approved_by = approved_by or "owner"
            app.updated_at = now
            self.stats["apps_released"] += 1
            self.stats["user_approvals"] += 1
            self.stats["total_rules_deployed"] = sum(
                len(a.rules) for a in self.apps if a.status == "released"
            )

            self._add_insight(
                "improvement",
                f"تم إصدار تطبيق بموافقة المستخدم: {app.name_ar} (v{app.version}) — سري",
                {"app_id": app_id, "approved_by": approved_by,
                 "privacy": app.privacy_level},
                f"إصدار سري: {app.name_ar}",
            )

            return {
                "status": "released",
                "message": f"تم إصدار '{app.name_ar}' بسرية تامة — محلي فقط",
                "privacy": app.privacy_level,
                "app_id": app_id,
            }

        elif decision == ReleaseDecision.REJECT.value:
            # ✗ المستخدم رفض
            app.status = "rejected"
            app.updated_at = now
            self.stats["apps_rejected"] += 1
            self.stats["user_rejections"] += 1

            self._add_insight(
                "regression",
                f"المستخدم رفض إصدار: {app.name_ar}",
                {"app_id": app_id, "reason": notes},
                "رفض الإصدار",
            )

            return {
                "status": "rejected",
                "message": f"تم رفض إصدار '{app.name_ar}'",
                "reason": notes,
            }

        elif decision == ReleaseDecision.MODIFY.value:
            # ✎ المستخدم يريد تعديلات
            app.status = "draft"
            app.updated_at = now

            return {
                "status": "needs_modification",
                "message": f"'{app.name_ar}' يحتاج تعديل قبل الإصدار",
                "notes": notes,
            }

        elif decision == ReleaseDecision.DEFER.value:
            # ⏸ المستخدم يريد التأجيل
            app.status = "awaiting_approval"
            app.updated_at = now
            self.stats["apps_awaiting"] = sum(
                1 for a in self.apps if a.status == "awaiting_approval"
            )

            return {
                "status": "deferred",
                "message": f"تم تأجيل إصدار '{app.name_ar}'",
            }

        return {"status": "error", "message": "قرار غير معروف"}

    def request_release(self, app_id: str,
                        callback: Optional[Callable] = None) -> dict:
        """
        طلب إصدار تطبيق — يعرضه على المستخدم ويأخذ قراره.

        Args:
            app_id: معرف التطبيق
            callback: دالة لأخذ قرار المستخدم
                callback(proposal: dict) -> dict
                يجب أن تعيد: {"decision": "approve"|"reject"|"modify"|"defer",
                              "notes": "...", "approved_by": "..."}

        Returns:
            نتيجة العملية
        """
        cb = callback or self.release_callback
        if not cb:
            # لا توجد دالة callback — ضع التطبيق في الانتظار
            app = self._get_app(app_id)
            if app:
                app.status = "awaiting_approval"
                self.stats["apps_awaiting"] = sum(
                    1 for a in self.apps if a.status == "awaiting_approval"
                )
            return {
                "status": "awaiting",
                "message": "التطبيق ينتظر موافقة المستخدم",
                "app_id": app_id,
            }

        # تجهيز العرض
        proposal = self.prepare_release_proposal(app_id)
        if not proposal:
            return {"status": "error", "message": "التطبيق غير موجود"}

        # عرض على المستخدم وأخذ القرار
        proposal_dict = asdict(proposal)
        user_response = cb(proposal_dict)

        # تطبيق القرار
        return self.submit_release_decision(
            app_id=app_id,
            decision=user_response.get("decision", "defer"),
            notes=user_response.get("notes", ""),
            approved_by=user_response.get("approved_by", ""),
        )

    # ─── المرحلة 6: تشغيل التطبيقات ───

    def run_app(self, app_id: str, text: str) -> dict:
        app = self._get_app(app_id)
        if not app:
            return {"error": "التطبيق غير موجود", "processed": False}

        # فقط التطبيقات المُصدرة (الموافق عليها) يمكن تشغيلها
        if app.status != "released":
            return {
                "error": f"التطبيق '{app.name_ar}' لم يُصدر بعد (الحالة: {app.status})",
                "processed": False,
            }

        issues_found = []
        modified_text = text

        for rule in app.rules:
            pattern = rule.get("pattern", "")
            replacement = rule.get("replacement", "")
            suggestion = rule.get("suggestion", "")

            try:
                if re.search(pattern, modified_text):
                    match = re.search(pattern, modified_text)
                    issues_found.append({
                        "matched": match.group(),
                        "position": match.start(),
                        "suggestion": suggestion,
                        "rule": rule.get("name", rule.get("rule_id", "unknown")),
                    })

                    if replacement:
                        modified_text = re.sub(pattern, replacement, modified_text)
            except re.error:
                pass

        return {
            "app_name": app.name_ar,
            "processed": True,
            "original": text,
            "result": modified_text,
            "was_modified": text != modified_text,
            "issues_found": issues_found,
            "issues_count": len(issues_found),
            "privacy": app.privacy_level,
        }

    def run_all_released_apps(self, text: str) -> list[dict]:
        """تشغيل كل التطبيقات المُصدرة (الموافق عليها فقط) على نص."""
        results = []
        for app in self.apps:
            if app.status == "released" and app.user_decision == ReleaseDecision.APPROVE.value:
                result = self.run_app(app.app_id, text)
                results.append(result)
                if result.get("was_modified"):
                    text = result["result"]
        return results

    # ─── الدورة الكاملة للمُنتِج ───

    def run_builder_cycle(self, agent_stats: dict[str, dict],
                          release_callback: Optional[Callable] = None) -> dict:
        """
        دورة كاملة:
        1. مراقبة
        2. تعلّم
        3. بناء تطبيقات
        4. اختبار
        5. طلب موافقة المستخدم (لا إصدار بدون إذن)
        6. حفظ
        """
        cb = release_callback or self.release_callback

        # 1. مراقبة
        new_insights = self.observe_system(agent_stats)

        # 2. تعلّم
        learned = self.learn_from_discovery()

        # 3. بناء تطبيقات جديدة
        new_apps = []
        for insight in new_insights:
            if insight.insight_type == "gap":
                for app_type, template in self.APP_TEMPLATES.items():
                    existing = any(a.name == template["name"] for a in self.apps)
                    if not existing:
                        app = self.build_app(app_type)
                        if app:
                            new_apps.append(app.name_ar)

            elif insight.insight_type == "opportunity":
                if learned.get("rules_available", 0) > 3:
                    for app_type, template in self.APP_TEMPLATES.items():
                        existing = any(a.name == template["name"] for a in self.apps)
                        if not existing:
                            app = self.build_app(app_type)
                            if app:
                                new_apps.append(app.name_ar)
                            break

        # 4. اختبار التطبيقات
        test_results = {}
        for app in self.apps:
            if app.status in ("draft", "testing"):
                result = self.test_app(app.app_id)
                test_results[app.name_ar] = result.accuracy

        # 5. طلب الموافقة للتطبيقات الجاهزة
        release_requests = []
        for app in self.apps:
            if app.status == "testing" and app.user_decision is None:
                if cb:
                    # عرض على المستخدم
                    req_result = self.request_release(app.app_id, callback=cb)
                    release_requests.append({
                        "app": app.name_ar,
                        "result": req_result,
                    })
                else:
                    # لا callback — ضع في الانتظار
                    app.status = "awaiting_approval"
                    release_requests.append({
                        "app": app.name_ar,
                        "result": {"status": "awaiting", "message": "ينتظر موافقتك"},
                    })

        self.stats["apps_awaiting"] = sum(
            1 for a in self.apps if a.status == "awaiting_approval"
        )

        self.save_all()

        return {
            "new_insights": len(new_insights),
            "learned": learned,
            "new_apps_built": new_apps,
            "test_results": test_results,
            "release_requests": release_requests,
            "total_apps": len(self.apps),
            "released_apps": self.stats["apps_released"],
            "awaiting_approval": self.stats["apps_awaiting"],
        }

    # ─── عرض التطبيقات المعلّقة ───

    def get_pending_approvals(self) -> list[dict]:
        """عرض التطبيقات التي تنتظر موافقة المستخدم."""
        pending = []
        for app in self.apps:
            if app.status in ("testing", "awaiting_approval"):
                proposal = self.prepare_release_proposal(app.app_id)
                if proposal:
                    pending.append(asdict(proposal))
        return pending

    # ─── أدوات مساعدة ───

    def _get_app(self, app_id: str) -> Optional[AppSpec]:
        for app in self.apps:
            if app.app_id == app_id:
                return app
        return None

    def _add_insight(self, insight_type: str, description: str,
                     data: dict, action: str = ""):
        self.insights.append(BuilderInsight(
            timestamp=datetime.now().isoformat(),
            insight_type=insight_type,
            description=description,
            data=data,
            action_taken=action,
        ))

    def get_stats(self) -> dict:
        return self.stats.copy()

    def get_apps_summary(self) -> list[dict]:
        return [
            {
                "id": app.app_id,
                "name": app.name_ar,
                "status": app.status,
                "privacy": app.privacy_level,
                "rules_count": len(app.rules),
                "version": app.version,
                "user_decision": app.user_decision,
                "accuracy": app.test_results.get("accuracy", 0)
                if isinstance(app.test_results, dict) else 0,
            }
            for app in self.apps
        ]

    def get_released_apps(self) -> list[AppSpec]:
        return [a for a in self.apps if a.status == "released"]
