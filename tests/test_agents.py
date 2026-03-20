"""
اختبارات الوكلاء الخمسة وخط الأنابيب.
"""

import sys
import os
import json
import tempfile
import shutil

# إضافة مسار المشروع
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.agents.normalizer import NormalizerAgent
from src.agents.qa_evaluator import QAEvaluatorAgent
from src.agents.bidi_fixer import BidiFixerAgent
from src.agents.discovery import DiscoveryAgent
from src.agents.builder import BuilderAgent
from src.pipeline import Pipeline


# ═══════════════════════════════════════════
# اختبارات وكيل 1: المطبّع
# ═══════════════════════════════════════════

def test_normalizer_hamza():
    agent = NormalizerAgent()
    result = agent.normalize("إنسان أكل آخر")
    assert "ا" in result.normalized
    assert result.was_modified
    print("  ✓ توحيد الهمزة")


def test_normalizer_tashkeel():
    agent = NormalizerAgent()
    result = agent.normalize("مَدْرَسَةٌ")
    assert "َ" not in result.normalized
    assert "ْ" not in result.normalized
    print("  ✓ إزالة التشكيل")


def test_normalizer_taa_marbuta():
    agent = NormalizerAgent()
    result = agent.normalize("مدرسه جامعه")
    assert "مدرسة" in result.normalized
    assert "جامعة" in result.normalized
    print("  ✓ تصحيح التاء المربوطة")


def test_normalizer_punctuation():
    agent = NormalizerAgent()
    result = agent.normalize("كلمة, اخرى; سؤال?")
    assert "،" in result.normalized
    assert "؛" in result.normalized
    assert "؟" in result.normalized
    print("  ✓ توحيد علامات الترقيم")


def test_normalizer_hindi_numbers():
    agent = NormalizerAgent()
    result = agent.normalize("العدد ٥٦٧")
    assert "567" in result.normalized
    print("  ✓ تحويل الأرقام الهندية")


def test_normalizer_spaces():
    agent = NormalizerAgent()
    result = agent.normalize("كلمة   كلمة   كلمة")
    assert "   " not in result.normalized
    print("  ✓ تطبيع المسافات")


def test_normalizer_stats():
    agent = NormalizerAgent()
    agent.normalize("إنسان أكل")
    agent.normalize("مدرسه")
    stats = agent.get_stats()
    assert stats["texts_processed"] == 2
    print("  ✓ الإحصائيات")


# ═══════════════════════════════════════════
# اختبارات وكيل 2: مقيّم الجودة
# ═══════════════════════════════════════════

def test_qa_literal_translation():
    agent = QAEvaluatorAgent()
    result = agent.evaluate(
        "Please look up the information",
        "رجاء انظر فوق المعلومات"
    )
    assert any(i.category == "ترجمة_حرفية" for i in result.issues)
    print("  ✓ كشف الترجمة الحرفية")


def test_qa_untranslated():
    agent = QAEvaluatorAgent()
    result = agent.evaluate(
        "The system uses encryption",
        "النظام يستخدم encryption للحماية"
    )
    assert any(i.category == "كلمة_غير_مترجمة" for i in result.issues)
    print("  ✓ كشف الكلمات غير المترجمة")


def test_qa_weak_style():
    agent = QAEvaluatorAgent()
    result = agent.evaluate(
        "The report is being prepared",
        "يتم تجهيز التقرير بشكل سريع"
    )
    assert any(i.category == "أسلوب_ضعيف" for i in result.issues)
    print("  ✓ كشف الأسلوب الضعيف")


def test_qa_scoring():
    agent = QAEvaluatorAgent()
    # نص نظيف بدون مشاكل
    result = agent.evaluate(
        "Hello",
        "مرحبا"
    )
    assert result.score > 80
    assert result.passed
    print("  ✓ التقييم بالدرجات")


def test_qa_grade():
    agent = QAEvaluatorAgent()
    result = agent.evaluate("Hello", "مرحبا")
    assert result.grade in ("ممتاز", "جيد", "مقبول", "ضعيف", "مرفوض")
    print("  ✓ التصنيف")


def test_qa_glossary():
    # إنشاء معجم مؤقت
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"encryption": "تشفير"}, f)
        glossary_path = f.name

    try:
        agent = QAEvaluatorAgent(glossary_path=glossary_path)
        result = agent.evaluate(
            "We use encryption",
            "نحن نستخدم الترميز"  # خطأ — يجب أن تكون "تشفير"
        )
        assert any(i.category == "تناسق_معجم" for i in result.issues)
        print("  ✓ فحص المعجم")
    finally:
        os.unlink(glossary_path)


# ═══════════════════════════════════════════
# اختبارات وكيل 3: معالج BiDi
# ═══════════════════════════════════════════

def test_bidi_latin_isolation():
    agent = BidiFixerAgent()
    result = agent.fix("هذا نص يحتوي على Python وكلمات أخرى")
    assert result.was_modified
    assert "\u2066" in result.fixed  # LRI
    print("  ✓ عزل النص اللاتيني")


def test_bidi_rtl_paragraph():
    agent = BidiFixerAgent()
    result = agent.fix("مرحبا بالعالم")
    assert result.fixed.startswith("\u200F")  # RLM
    print("  ✓ ضمان اتجاه RTL")


def test_bidi_clean_marks():
    agent = BidiFixerAgent()
    text = "\u200Fمرحبا\u200E"
    result = agent.fix(text, clean_first=True)
    # يجب أن يُنظف العلامات القديمة ويضيف الجديدة
    assert result.was_modified
    print("  ✓ تنظيف العلامات القديمة")


def test_bidi_stats():
    agent = BidiFixerAgent()
    agent.fix("نص مع English فيه")
    stats = agent.get_stats()
    assert stats["texts_processed"] == 1
    print("  ✓ إحصائيات BiDi")


# ═══════════════════════════════════════════
# اختبارات وكيل 4: المكتشف
# ═══════════════════════════════════════════

def test_discovery_collect_errors():
    tmp = tempfile.mkdtemp()
    try:
        agent = DiscoveryAgent(data_dir=tmp)
        agent.collect_error(
            agent="qa_evaluator",
            category="ترجمة_حرفية",
            source_text="look up",
            target_text="انظر فوق",
            error_detail="ترجمة حرفية",
            severity="high",
        )
        assert len(agent.errors_log) == 1
        assert agent.stats["errors_collected"] == 1
        print("  ✓ جمع الأخطاء")
    finally:
        shutil.rmtree(tmp)


def test_discovery_pattern_analysis():
    tmp = tempfile.mkdtemp()
    try:
        agent = DiscoveryAgent(data_dir=tmp)
        # إضافة أخطاء متكررة (3+ مرات)
        for i in range(5):
            agent.collect_error(
                agent="qa_evaluator",
                category="ترجمة_حرفية",
                source_text=f"look up item {i}",
                target_text=f"انظر فوق عنصر {i}",
                error_detail="ترجمة حرفية لـ look up",
                severity="high",
            )
        patterns = agent.analyze_patterns()
        assert len(patterns) > 0
        print("  ✓ اكتشاف الأنماط")
    finally:
        shutil.rmtree(tmp)


def test_discovery_save_load():
    tmp = tempfile.mkdtemp()
    try:
        agent = DiscoveryAgent(data_dir=tmp)
        agent.collect_error(
            agent="test", category="test_cat",
            source_text="src", target_text="tgt",
            error_detail="detail",
        )
        agent.save_all()

        # تحميل مجدداً
        agent2 = DiscoveryAgent(data_dir=tmp)
        assert len(agent2.errors_log) == 1
        print("  ✓ حفظ واسترجاع البيانات")
    finally:
        shutil.rmtree(tmp)


def test_discovery_cycle():
    tmp = tempfile.mkdtemp()
    try:
        agent = DiscoveryAgent(data_dir=tmp)
        for i in range(5):
            agent.collect_error(
                agent="qa", category="test_cat",
                source_text=f"src {i}", target_text=f"tgt {i}",
                error_detail="repeated error",
            )
        summary = agent.run_discovery_cycle()
        assert "new_patterns" in summary
        assert "total_errors" in summary
        print("  ✓ دورة الاكتشاف الكاملة")
    finally:
        shutil.rmtree(tmp)


# ═══════════════════════════════════════════
# اختبارات وكيل 5: المُنتِج
# ═══════════════════════════════════════════

def test_builder_observe():
    tmp = tempfile.mkdtemp()
    try:
        builder = BuilderAgent(data_dir=tmp)
        stats = {
            "normalizer": {"texts_processed": 100, "extra_rules_applied": 5},
            "qa_evaluator": {"evaluations": 100, "avg_score": 55.0,
                             "literal_detections": 15, "untranslated_detections": 3,
                             "passive_issues": 2, "weak_style_issues": 5,
                             "total_issues": 25},
            "bidi_fixer": {"texts_processed": 100},
            "discovery": {"patterns_discovered": 8, "rules_generated": 3,
                          "algorithms_created": 1, "errors_collected": 50},
            "builder": {"apps_built": 0},
        }
        insights = builder.observe_system(stats)
        assert len(insights) > 0
        # يجب أن يكتشف فرصة تحسين (avg_score < 70)
        assert any(i.insight_type == "opportunity" for i in insights)
        print("  ✓ مراقبة النظام")
    finally:
        shutil.rmtree(tmp)


def test_builder_build_app():
    tmp = tempfile.mkdtemp()
    try:
        builder = BuilderAgent(data_dir=tmp)
        app = builder.build_app("spellchecker")
        assert app is not None
        assert app.name_ar == "المصحح الإملائي العربي"
        assert app.status == "draft"
        print("  ✓ بناء تطبيق")
    finally:
        shutil.rmtree(tmp)


def test_builder_build_custom_app():
    tmp = tempfile.mkdtemp()
    try:
        builder = BuilderAgent(data_dir=tmp)
        app = builder.build_custom_app(
            name="Dialect Detector",
            name_ar="كاشف اللهجات",
            description="يكشف اللهجة العربية في النص",
            problem="تحديد اللهجة",
            categories=["dialect"],
        )
        assert app is not None
        assert app.name_ar == "كاشف اللهجات"
        print("  ✓ بناء تطبيق مخصص")
    finally:
        shutil.rmtree(tmp)


def test_builder_save_load():
    tmp = tempfile.mkdtemp()
    try:
        builder = BuilderAgent(data_dir=tmp)
        builder.build_app("translation_qa")
        builder.save_all()

        builder2 = BuilderAgent(data_dir=tmp)
        assert len(builder2.apps) == 1
        print("  ✓ حفظ واسترجاع التطبيقات")
    finally:
        shutil.rmtree(tmp)


def test_builder_cycle():
    tmp = tempfile.mkdtemp()
    try:
        discovery = DiscoveryAgent(data_dir=tmp)
        builder = BuilderAgent(data_dir=tmp, discovery_agent=discovery)

        stats = {
            "normalizer": {"texts_processed": 50, "extra_rules_applied": 0},
            "qa_evaluator": {"evaluations": 50, "avg_score": 60.0,
                             "literal_detections": 12, "untranslated_detections": 3,
                             "passive_issues": 1, "weak_style_issues": 4,
                             "total_issues": 20},
            "bidi_fixer": {"texts_processed": 50},
            "discovery": {"patterns_discovered": 6, "rules_generated": 2,
                          "algorithms_created": 0, "errors_collected": 30},
            "builder": {"apps_built": 0},
        }
        summary = builder.run_builder_cycle(stats)
        assert "new_insights" in summary
        assert "total_apps" in summary
        print("  ✓ دورة المُنتِج الكاملة")
    finally:
        shutil.rmtree(tmp)


def test_builder_with_discovery_learning():
    tmp = tempfile.mkdtemp()
    try:
        discovery = DiscoveryAgent(data_dir=tmp)
        # إضافة أخطاء وتوليد قواعد
        for i in range(5):
            discovery.collect_error(
                agent="qa", category="literal",
                source_text=f"look up {i}", target_text=f"انظر فوق {i}",
                error_detail="literal translation",
            )
        discovery.run_discovery_cycle()

        builder = BuilderAgent(data_dir=tmp, discovery_agent=discovery)
        learned = builder.learn_from_discovery()
        assert learned["status"] == "learned"
        print("  ✓ التعلّم من المكتشف")
    finally:
        shutil.rmtree(tmp)


# ═══════════════════════════════════════════
# اختبارات خط الأنابيب
# ═══════════════════════════════════════════

def test_pipeline_basic():
    tmp = tempfile.mkdtemp()
    try:
        pipeline = Pipeline(data_dir=tmp)
        result = pipeline.process(
            source="The system uses encryption to protect data",
            target="النظام يستخدم encryption لحمايه البيانات",
        )
        # المطبّع يجب أن يصلح "لحمايه" → "لحماية" (لو كانت في القائمة)
        assert result.final_text != ""
        assert result.quality_score > 0
        print("  ✓ خط الأنابيب الأساسي")
    finally:
        shutil.rmtree(tmp)


def test_pipeline_full_flow():
    tmp = tempfile.mkdtemp()
    glossary_path = os.path.join(tmp, "glossary.json")
    with open(glossary_path, "w") as f:
        json.dump({"encryption": "تشفير"}, f)

    try:
        pipeline = Pipeline(data_dir=tmp, glossary_path=glossary_path)

        # معالجة عدة نصوص
        pairs = [
            ("Look up the data", "انظر فوق البيانات"),
            ("The encryption is strong", "الترميز قوي"),
            ("Set up the system", "ضع فوق النظام"),
        ]
        results = pipeline.process_batch(pairs)
        assert len(results) == 3
        assert all(r.quality_score >= 0 for r in results)

        report = pipeline.get_system_report()
        assert report["texts_processed"] == 3
        print("  ✓ التدفق الكامل لخط الأنابيب")
    finally:
        shutil.rmtree(tmp)


# ═══════════════════════════════════════════
# تشغيل كل الاختبارات
# ═══════════════════════════════════════════

def main():
    print("\n" + "=" * 60)
    print("  اختبارات نظام TarjimTech — الوكلاء الخمسة")
    print("=" * 60)

    sections = [
        ("وكيل 1: المطبّع", [
            test_normalizer_hamza,
            test_normalizer_tashkeel,
            test_normalizer_taa_marbuta,
            test_normalizer_punctuation,
            test_normalizer_hindi_numbers,
            test_normalizer_spaces,
            test_normalizer_stats,
        ]),
        ("وكيل 2: مقيّم الجودة", [
            test_qa_literal_translation,
            test_qa_untranslated,
            test_qa_weak_style,
            test_qa_scoring,
            test_qa_grade,
            test_qa_glossary,
        ]),
        ("وكيل 3: معالج BiDi", [
            test_bidi_latin_isolation,
            test_bidi_rtl_paragraph,
            test_bidi_clean_marks,
            test_bidi_stats,
        ]),
        ("وكيل 4: المكتشف", [
            test_discovery_collect_errors,
            test_discovery_pattern_analysis,
            test_discovery_save_load,
            test_discovery_cycle,
        ]),
        ("وكيل 5: المُنتِج", [
            test_builder_observe,
            test_builder_build_app,
            test_builder_build_custom_app,
            test_builder_save_load,
            test_builder_cycle,
            test_builder_with_discovery_learning,
        ]),
        ("خط الأنابيب", [
            test_pipeline_basic,
            test_pipeline_full_flow,
        ]),
    ]

    total = 0
    passed = 0
    failed = 0

    for section_name, tests in sections:
        print(f"\n{'─' * 40}")
        print(f"  {section_name}")
        print(f"{'─' * 40}")

        for test_fn in tests:
            total += 1
            try:
                test_fn()
                passed += 1
            except Exception as e:
                failed += 1
                print(f"  ✗ {test_fn.__name__}: {e}")

    print(f"\n{'=' * 60}")
    print(f"  النتيجة: {passed}/{total} نجح | {failed} فشل")
    print(f"{'=' * 60}\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
