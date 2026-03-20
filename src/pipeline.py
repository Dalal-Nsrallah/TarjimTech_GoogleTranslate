"""
خط الأنابيب (Pipeline)
========================
يُشغّل الوكلاء الستة بالتسلسل الصحيح ويربطهم ببعض.

ترتيب التنفيذ:
  1. المطبّع → يُطبّع النص العربي
  2. مقيّم الجودة → يقيّم جودة الترجمة (تفاعلي)
  3. معالج BiDi → يصلح الاتجاهات
  4. الفصاحة → يقرأ النص كاملاً ويحسّن اللغة العربية
  5. المكتشف → يجمع الأخطاء ويكتشف أنماط
  6. المُنتِج → يراقب ويبني تطبيقات

المدخلات:
  - source: النص المصدر (إنجليزي)
  - target: النص المترجم (عربي)

المخرجات:
  - النص المُحسّن بعربية فصيحة
  - تقرير الجودة
  - تقرير الفصاحة
  - اكتشافات جديدة
  - تطبيقات مبنية
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable

from .agents.normalizer import NormalizerAgent
from .agents.qa_evaluator import QAEvaluatorAgent
from .agents.bidi_fixer import BidiFixerAgent
from .agents.eloquence import EloquenceAgent
from .agents.discovery import DiscoveryAgent
from .agents.builder import BuilderAgent


@dataclass
class PipelineResult:
    """نتيجة تشغيل خط الأنابيب الكامل."""
    # المدخلات
    source: str
    target_original: str

    # مخرجات المطبّع
    target_normalized: str = ""
    normalizer_changes: list = field(default_factory=list)

    # مخرجات مقيّم الجودة
    quality_score: float = 0.0
    quality_final_score: float = 0.0
    quality_grade: str = ""
    quality_issues: list = field(default_factory=list)
    quality_proposals: list = field(default_factory=list)
    quality_verification: dict = field(default_factory=dict)

    # مخرجات معالج BiDi
    target_bidi_fixed: str = ""
    bidi_issues: list = field(default_factory=list)

    # مخرجات وكيل الفصاحة
    target_eloquent: str = ""
    eloquence_fixes: list = field(default_factory=list)
    eloquence_score_before: float = 0.0
    eloquence_score_after: float = 0.0

    # مخرجات المكتشف
    discovery_summary: dict = field(default_factory=dict)

    # مخرجات المُنتِج
    builder_summary: dict = field(default_factory=dict)
    app_results: list = field(default_factory=list)

    # النص النهائي
    final_text: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class Pipeline:
    """
    خط الأنابيب الرئيسي — يربط الوكلاء الستة.
    """

    def __init__(self, data_dir: str = "data",
                 glossary_path: Optional[str] = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        rules_path = str(self.data_dir / "patterns" / "discovered_rules.json")

        # إنشاء الوكلاء
        self.normalizer = NormalizerAgent(extra_rules_path=rules_path)
        self.qa_evaluator = QAEvaluatorAgent(
            glossary_path=glossary_path,
            discovered_rules_path=rules_path,
        )
        self.bidi_fixer = BidiFixerAgent()
        self.eloquence = EloquenceAgent(extra_rules_path=rules_path)
        self.discovery = DiscoveryAgent(data_dir=str(self.data_dir))
        self.builder = BuilderAgent(
            data_dir=str(self.data_dir),
            discovery_agent=self.discovery,
        )

        self.run_count = 0

    def process(self, source: str, target: str,
                run_discovery: bool = True,
                run_builder: bool = True,
                decision_callback: Optional[Callable] = None,
                auto_approve: bool = False) -> PipelineResult:
        """
        معالجة ترجمة كاملة عبر كل الوكلاء.

        Args:
            source: النص المصدر (الإنجليزي)
            target: النص المترجم (العربي)
            run_discovery: تشغيل وكيل المكتشف
            run_builder: تشغيل وكيل المُنتِج
            decision_callback: دالة تفاعلية لأخذ رأي المستخدم
            auto_approve: اعتماد تلقائي للمشاكل العالية والحرجة

        Returns:
            PipelineResult مع كل النتائج
        """
        result = PipelineResult(
            source=source,
            target_original=target,
        )

        # ── وكيل 1: المطبّع ──
        norm_result = self.normalizer.normalize(target)
        result.target_normalized = norm_result.normalized
        result.normalizer_changes = norm_result.changes
        current_text = norm_result.normalized

        # ── وكيل 2: مقيّم الجودة (تفاعلي) ──
        if decision_callback:
            qa_result = self.qa_evaluator.interactive_review(
                source, current_text, decision_callback
            )
        elif auto_approve:
            qa_result = self.qa_evaluator.auto_review(source, current_text)
        else:
            qa_result = self.qa_evaluator.evaluate(source, current_text)

        result.quality_score = qa_result.score
        result.quality_final_score = qa_result.final_score
        result.quality_grade = qa_result.grade
        result.quality_issues = [
            {
                "issue_id": i.issue_id,
                "category": i.category,
                "severity": i.severity,
                "description": i.description,
                "suggestion": i.suggestion,
                "user_decision": i.user_decision,
                "applied": i.applied,
            }
            for i in qa_result.issues
        ]

        if qa_result.issues:
            result.quality_proposals = self.qa_evaluator.propose_fixes(qa_result)

        if qa_result.verification:
            v = qa_result.verification
            result.quality_verification = {
                "fixes_verified": v.fixes_verified,
                "remaining_issues": len(v.remaining_issues),
                "new_issues": len(v.new_issues),
                "all_clear": v.all_clear,
            }

        if qa_result.approved_text:
            current_text = qa_result.approved_text

        # ── وكيل 3: معالج BiDi ──
        bidi_result = self.bidi_fixer.fix(current_text)
        result.target_bidi_fixed = bidi_result.fixed
        result.bidi_issues = [
            {
                "type": i.issue_type,
                "description": i.description,
                "fix": i.fix_applied,
            }
            for i in bidi_result.issues
        ]
        current_text = bidi_result.fixed

        # ── وكيل 4: الفصاحة ──
        eloquence_result = self.eloquence.improve(current_text)
        result.target_eloquent = eloquence_result.improved_text
        result.eloquence_fixes = [
            {
                "rule": f.rule_name,
                "category": f.category,
                "original": f.original,
                "improved": f.improved,
                "explanation": f.explanation,
            }
            for f in eloquence_result.fixes
        ]
        result.eloquence_score_before = eloquence_result.eloquence_score_before
        result.eloquence_score_after = eloquence_result.eloquence_score_after
        current_text = eloquence_result.improved_text

        # ── وكيل 5: المكتشف ──
        if run_discovery:
            self.discovery.collect_from_normalizer(norm_result)
            self.discovery.collect_from_qa(qa_result)
            self.discovery.collect_from_bidi(bidi_result)
            # جمع بيانات الفصاحة أيضاً
            if eloquence_result.was_modified:
                for fix in eloquence_result.fixes:
                    self.discovery.collect_error(
                        agent="eloquence",
                        category=fix.category,
                        source_text=fix.original,
                        target_text=fix.improved,
                        error_detail=fix.explanation,
                        severity="low",
                    )

            self.run_count += 1
            if self.run_count % 10 == 0:
                discovery_summary = self.discovery.run_discovery_cycle()
                result.discovery_summary = discovery_summary

        # ── وكيل 6: المُنتِج ──
        if run_builder:
            if self.run_count % 10 == 0:
                agent_stats = self._collect_all_stats()
                builder_summary = self.builder.run_builder_cycle(agent_stats)
                result.builder_summary = builder_summary

            app_results = self.builder.run_all_released_apps(current_text)
            if app_results:
                result.app_results = app_results
                for ar in reversed(app_results):
                    if ar.get("was_modified"):
                        current_text = ar["result"]
                        break

        result.final_text = current_text
        return result

    def process_batch(self, pairs: list[tuple[str, str]]) -> list[PipelineResult]:
        """معالجة دفعة من الترجمات."""
        results = []
        for source, target in pairs:
            result = self.process(source, target)
            results.append(result)

        self.discovery.run_discovery_cycle()
        agent_stats = self._collect_all_stats()
        self.builder.run_builder_cycle(agent_stats)

        return results

    def _collect_all_stats(self) -> dict:
        """جمع إحصائيات كل الوكلاء."""
        return {
            "normalizer": self.normalizer.get_stats(),
            "qa_evaluator": self.qa_evaluator.get_stats(),
            "bidi_fixer": self.bidi_fixer.get_stats(),
            "eloquence": self.eloquence.get_stats(),
            "discovery": self.discovery.get_stats(),
            "builder": self.builder.get_stats(),
        }

    def get_system_report(self) -> dict:
        """تقرير شامل عن حالة النظام."""
        stats = self._collect_all_stats()
        return {
            "texts_processed": self.run_count,
            "agent_stats": stats,
            "discovery_insights": self.discovery.get_insights(),
            "builder_apps": self.builder.get_apps_summary(),
            "released_apps_count": self.builder.stats["apps_released"],
        }

    def force_discovery_cycle(self) -> dict:
        return self.discovery.run_discovery_cycle()

    def force_builder_cycle(self) -> dict:
        agent_stats = self._collect_all_stats()
        return self.builder.run_builder_cycle(agent_stats)

    def save_all(self):
        self.discovery.save_all()
        self.builder.save_all()
