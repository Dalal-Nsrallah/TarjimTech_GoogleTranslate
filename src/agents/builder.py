"""
وكيل 5: المُنتِج (Builder Agent)
==================================
يراقب عمل كل الوكلاء، يتعلّم من وكيل المكتشف،
ويستخدم الخوارزميات الناتجة لبناء تطبيقات تحل مشاكل اللغة العربية.

الدورة:
  1. يراقب كل الوكلاء ويجمع الإحصائيات
  2. يتعلّم من اكتشافات الوكيل الرابع
  3. يأخذ الخوارزميات الناجحة
  4. يبني منها تطبيقات/أدوات مستقلة
  5. يختبر التطبيقات ويُصدرها

التطبيقات التي يبنيها:
  - مصحح إملائي عربي متخصص
  - محلل جودة ترجمة
  - مصحح اتجاهات النص
  - معجم ذكي يتطوّر تلقائياً
  - أي أداة جديدة بناءً على الاكتشافات
"""

import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class AppSpec:
    """مواصفات تطبيق واحد."""
    app_id: str
    name: str
    name_ar: str                   # الاسم بالعربية
    description: str
    problem_solved: str            # المشكلة التي يحلها
    source_algorithms: list = field(default_factory=list)  # الخوارزميات المستخدمة
    rules: list = field(default_factory=list)              # القواعد المضمّنة
    version: int = 1
    created_at: str = ""
    updated_at: str = ""
    status: str = "draft"          # draft, testing, released
    test_results: dict = field(default_factory=dict)


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
    insight_type: str    # improvement, regression, opportunity, gap
    description: str
    data: dict = field(default_factory=dict)
    action_taken: str = ""


class BuilderAgent:
    """
    الوكيل الخامس — المُنتِج.
    يبني تطبيقات من الخوارزميات المكتشفة لحل مشاكل اللغة العربية.
    """

    # أنواع التطبيقات التي يمكن بناؤها
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

    def __init__(self, data_dir: str = "data", discovery_agent=None):
        self.data_dir = Path(data_dir)
        self.apps_dir = self.data_dir / "apps"
        self.apps_dir.mkdir(parents=True, exist_ok=True)

        self.discovery = discovery_agent
        self.apps: list[AppSpec] = self._load_apps()
        self.insights: list[BuilderInsight] = self._load_insights()

        self.stats = {
            "apps_built": len(self.apps),
            "apps_released": sum(1 for a in self.apps if a.status == "released"),
            "apps_testing": sum(1 for a in self.apps if a.status == "testing"),
            "insights_generated": len(self.insights),
            "total_rules_deployed": sum(len(a.rules) for a in self.apps),
            "observation_cycles": 0,
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
        """حفظ كل بيانات المُنتِج."""
        self._save_json("apps_registry.json",
                        [asdict(a) for a in self.apps])
        self._save_json("builder_insights.json",
                        [asdict(i) for i in self.insights])
        self._save_json("builder_stats.json", self.stats)

    # ─── المرحلة 1: المراقبة ───

    def observe_system(self, agent_stats: dict[str, dict]) -> list[BuilderInsight]:
        """
        يراقب إحصائيات كل الوكلاء ويستخلص ملاحظات.

        Args:
            agent_stats: إحصائيات كل وكيل {agent_name: stats_dict}

        Returns:
            قائمة الملاحظات الجديدة
        """
        new_insights = []
        self.stats["observation_cycles"] += 1

        # 1. كشف التحسّن
        normalizer_stats = agent_stats.get("normalizer", {})
        if normalizer_stats.get("extra_rules_applied", 0) > 0:
            new_insights.append(BuilderInsight(
                timestamp=datetime.now().isoformat(),
                insight_type="improvement",
                description="وكيل المطبّع بدأ يستخدم قواعد مكتشفة — النظام يتطوّر",
                data={"extra_rules": normalizer_stats.get("extra_rules_applied")},
            ))

        # 2. كشف فرص التحسين
        qa_stats = agent_stats.get("qa_evaluator", {})
        avg_score = qa_stats.get("avg_score", 0)
        if avg_score > 0 and avg_score < 70:
            new_insights.append(BuilderInsight(
                timestamp=datetime.now().isoformat(),
                insight_type="opportunity",
                description=f"متوسط جودة الترجمة {avg_score:.1f}% — فرصة لبناء أداة تحسين",
                data={"avg_score": avg_score},
            ))

        # 3. كشف الأنماط الأكثر شيوعاً
        discovery_stats = agent_stats.get("discovery", {})
        if discovery_stats.get("patterns_discovered", 0) > 5:
            new_insights.append(BuilderInsight(
                timestamp=datetime.now().isoformat(),
                insight_type="opportunity",
                description="عدد كافٍ من الأنماط لبناء تطبيق جديد",
                data={"patterns": discovery_stats.get("patterns_discovered")},
            ))

        # 4. كشف الفجوات — مشاكل بدون حلول
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
        """
        يتعلّم من وكيل المكتشف — يأخذ الخوارزميات والقواعد الناجحة.

        Returns:
            ملخص ما تعلّمه
        """
        if not self.discovery:
            return {"status": "no_discovery_agent", "learned": 0}

        learned_rules = 0
        learned_algorithms = 0

        # 1. أخذ القواعد الناجحة
        exported_rules = self.discovery.export_rules_for_agents()
        learned_rules = len(exported_rules)

        # 2. أخذ الخوارزميات
        algorithms = self.discovery.algorithms
        learned_algorithms = len(algorithms)

        # 3. أخذ الأفكار (insights)
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
        """
        بناء تطبيق جديد من نوع معيّن.

        Args:
            app_type: نوع التطبيق (من APP_TEMPLATES)
            custom_rules: قواعد إضافية مخصصة

        Returns:
            AppSpec للتطبيق المبني أو None
        """
        template = self.APP_TEMPLATES.get(app_type)
        if not template:
            return None

        app_id = hashlib.md5(
            f"{app_type}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]

        # جمع القواعد المناسبة
        rules = []

        # 1. قواعد من وكيل المكتشف
        if self.discovery:
            for rule in self.discovery.discovered_rules:
                if rule.accuracy >= 0.75:
                    for cat in template["categories"]:
                        if cat in rule.description:
                            rules.append(asdict(rule))
                            break

        # 2. قواعد مخصصة
        if custom_rules:
            rules.extend(custom_rules)

        # 3. تحديد الخوارزميات المصدر
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
        """
        بناء تطبيق مخصص بناءً على مشكلة محددة.

        يُستخدم عندما يكتشف المُنتِج مشكلة جديدة تحتاج تطبيقاً
        غير موجود في القوالب.
        """
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
        )

        self.apps.append(app)
        self.stats["apps_built"] += 1
        return app

    # ─── المرحلة 4: اختبار التطبيقات ───

    def test_app(self, app_id: str,
                 test_data: Optional[list[dict]] = None) -> AppTestResult:
        """
        اختبار تطبيق على بيانات.

        Args:
            app_id: معرف التطبيق
            test_data: بيانات اختبار [{input, expected_output}]
        """
        app = self._get_app(app_id)
        if not app:
            return AppTestResult(
                app_id=app_id, total_tests=0, passed=0, failed=0,
                accuracy=0.0, details=["التطبيق غير موجود"],
            )

        total = 0
        passed = 0
        details = []

        # اختبار كل قاعدة في التطبيق
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

        # اختبار على بيانات خارجية إن وُجدت
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

        # تحديث التطبيق
        app.test_results = asdict(result)
        if accuracy >= 0.75:
            app.status = "testing"
            self.stats["apps_testing"] = sum(
                1 for a in self.apps if a.status == "testing"
            )

        return result

    def release_app(self, app_id: str) -> bool:
        """إصدار تطبيق بعد اجتياز الاختبارات."""
        app = self._get_app(app_id)
        if not app:
            return False

        if app.status == "testing" and app.test_results.get("accuracy", 0) >= 0.75:
            app.status = "released"
            app.updated_at = datetime.now().isoformat()
            self.stats["apps_released"] += 1

            self._add_insight(
                "improvement",
                f"تم إصدار تطبيق: {app.name_ar} (v{app.version})",
                {"app_id": app_id, "accuracy": app.test_results.get("accuracy")},
                f"إصدار {app.name_ar}",
            )
            return True
        return False

    # ─── المرحلة 5: تشغيل التطبيقات ───

    def run_app(self, app_id: str, text: str) -> dict:
        """
        تشغيل تطبيق على نص.

        Args:
            app_id: معرف التطبيق
            text: النص المراد معالجته

        Returns:
            نتيجة المعالجة
        """
        app = self._get_app(app_id)
        if not app:
            return {"error": "التطبيق غير موجود", "processed": False}

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

                    # تطبيق الإصلاح إن وُجد
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
        }

    def run_all_released_apps(self, text: str) -> list[dict]:
        """تشغيل كل التطبيقات المُصدرة على نص واحد."""
        results = []
        for app in self.apps:
            if app.status == "released":
                result = self.run_app(app.app_id, text)
                results.append(result)
                # استخدام النتيجة كمدخل للتطبيق التالي
                if result.get("was_modified"):
                    text = result["result"]
        return results

    # ─── الدورة الكاملة للمُنتِج ───

    def run_builder_cycle(self, agent_stats: dict[str, dict]) -> dict:
        """
        دورة كاملة للمُنتِج:
        1. مراقبة النظام
        2. التعلّم من المكتشف
        3. بناء تطبيقات جديدة إن لزم
        4. اختبار التطبيقات الموجودة
        5. حفظ كل شيء

        Args:
            agent_stats: إحصائيات كل الوكلاء

        Returns:
            ملخص الدورة
        """
        # 1. مراقبة
        new_insights = self.observe_system(agent_stats)

        # 2. تعلّم
        learned = self.learn_from_discovery()

        # 3. بناء تطبيقات جديدة بناءً على الفجوات
        new_apps = []
        for insight in new_insights:
            if insight.insight_type == "gap":
                # كشف نوع المشكلة وبناء تطبيق مناسب
                for app_type, template in self.APP_TEMPLATES.items():
                    existing = any(a.name == template["name"] for a in self.apps)
                    if not existing:
                        app = self.build_app(app_type)
                        if app:
                            new_apps.append(app.name_ar)

            elif insight.insight_type == "opportunity":
                # فرصة لبناء تطبيق مخصص
                if learned.get("rules_available", 0) > 3:
                    # هناك قواعد كافية — ابنِ تطبيقاً
                    for app_type, template in self.APP_TEMPLATES.items():
                        existing = any(a.name == template["name"] for a in self.apps)
                        if not existing:
                            app = self.build_app(app_type)
                            if app:
                                new_apps.append(app.name_ar)
                            break  # تطبيق واحد في الدورة

        # 4. اختبار التطبيقات الموجودة
        test_results = {}
        for app in self.apps:
            if app.status in ("draft", "testing"):
                result = self.test_app(app.app_id)
                test_results[app.name_ar] = result.accuracy

        self.save_all()

        return {
            "new_insights": len(new_insights),
            "learned": learned,
            "new_apps_built": new_apps,
            "test_results": test_results,
            "total_apps": len(self.apps),
            "released_apps": self.stats["apps_released"],
        }

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
        """ملخص كل التطبيقات."""
        return [
            {
                "id": app.app_id,
                "name": app.name_ar,
                "status": app.status,
                "rules_count": len(app.rules),
                "version": app.version,
                "accuracy": app.test_results.get("accuracy", 0)
                if isinstance(app.test_results, dict) else 0,
            }
            for app in self.apps
        ]

    def get_released_apps(self) -> list[AppSpec]:
        """التطبيقات المُصدرة فقط."""
        return [a for a in self.apps if a.status == "released"]
