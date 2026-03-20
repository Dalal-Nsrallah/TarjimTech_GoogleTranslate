"""
اختبارات الوكلاء الستة وخط الأنابيب.
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
from src.agents.eloquence import EloquenceAgent
from src.agents.discovery import DiscoveryAgent
from src.agents.builder import BuilderAgent
from src.pipeline import Pipeline, PipelineResult
from src.exporter import Exporter


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


def test_qa_interactive_approve():
    """اختبار الدورة التفاعلية — المستخدم يعتمد التصحيح."""
    agent = QAEvaluatorAgent()

    def user_approves_all(proposals):
        return [{"issue_id": p["issue_id"], "decision": "approve"} for p in proposals]

    result = agent.interactive_review(
        "Please look up the information",
        "رجاء انظر فوق المعلومات",
        decision_callback=user_approves_all,
    )
    # يجب أن يُطبّق التصحيح
    assert "ابحث عن" in result.approved_text
    assert "انظر فوق" not in result.approved_text
    # يجب أن يتحقق
    assert result.verification is not None
    assert result.verification.fixes_verified > 0
    print("  ✓ الدورة التفاعلية — اعتماد")


def test_qa_interactive_reject():
    """اختبار الدورة التفاعلية — المستخدم يرفض التصحيح."""
    agent = QAEvaluatorAgent()

    def user_rejects_all(proposals):
        return [{"issue_id": p["issue_id"], "decision": "reject"} for p in proposals]

    result = agent.interactive_review(
        "Please look up the information",
        "رجاء انظر فوق المعلومات",
        decision_callback=user_rejects_all,
    )
    # النص لم يتغيّر لأن المستخدم رفض
    assert "انظر فوق" in result.approved_text
    print("  ✓ الدورة التفاعلية — رفض")


def test_qa_interactive_modify():
    """اختبار الدورة التفاعلية — المستخدم يعدّل بنفسه."""
    agent = QAEvaluatorAgent()

    def user_modifies(proposals):
        decisions = []
        for p in proposals:
            if p["category"] == "ترجمة_حرفية":
                decisions.append({
                    "issue_id": p["issue_id"],
                    "decision": "modify",
                    "correction": "ابحثي عن",  # تصحيح مخصص من المستخدم
                })
            else:
                decisions.append({
                    "issue_id": p["issue_id"],
                    "decision": "reject",
                })
        return decisions

    result = agent.interactive_review(
        "Please look up the information",
        "رجاء انظر فوق المعلومات",
        decision_callback=user_modifies,
    )
    assert "ابحثي عن" in result.approved_text
    print("  ✓ الدورة التفاعلية — تعديل مخصص")


def test_qa_auto_review():
    """اختبار الاعتماد التلقائي."""
    agent = QAEvaluatorAgent()
    result = agent.auto_review(
        "Please look up the information",
        "رجاء انظر فوق المعلومات",
        auto_approve_severity=["high", "critical"],
    )
    # الترجمة الحرفية = high → يجب أن تُعتمد تلقائياً
    assert "ابحث عن" in result.approved_text
    assert result.final_score > result.score  # الدرجة تحسّنت
    print("  ✓ الاعتماد التلقائي")


def test_qa_verify_after_apply():
    """اختبار التحقق الشامل بعد التطبيق."""
    agent = QAEvaluatorAgent()

    # تقييم
    qa_result = agent.evaluate(
        "Please look up the data",
        "رجاء انظر فوق البيانات"
    )
    assert len(qa_result.issues) > 0

    # اقتراحات
    proposals = agent.propose_fixes(qa_result)
    assert len(proposals) > 0
    assert proposals[0]["awaiting_decision"] is True

    # قرارات — اعتمد الكل
    decisions = [{"issue_id": p["issue_id"], "decision": "approve"} for p in proposals]
    qa_result = agent.submit_decisions(qa_result, decisions)

    # تطبيق
    qa_result = agent.apply_approved(qa_result)
    assert qa_result.approved_text != qa_result.target

    # تحقق
    qa_result = agent.verify(qa_result)
    assert qa_result.verification is not None
    assert qa_result.final_score >= qa_result.score
    print("  ✓ التحقق الشامل (5 مراحل)")


def test_qa_interactive_stats():
    """اختبار أن الإحصائيات تُحدّث في الدورة التفاعلية."""
    agent = QAEvaluatorAgent()

    def mixed_decisions(proposals):
        decisions = []
        for i, p in enumerate(proposals):
            if i == 0:
                decisions.append({"issue_id": p["issue_id"], "decision": "approve"})
            else:
                decisions.append({"issue_id": p["issue_id"], "decision": "reject"})
        return decisions

    agent.interactive_review(
        "Please look up the information",
        "رجاء انظر فوق المعلومات",
        decision_callback=mixed_decisions,
    )
    stats = agent.get_stats()
    assert stats["user_approvals"] >= 1
    assert stats["fixes_applied"] >= 1
    print("  ✓ إحصائيات الدورة التفاعلية")


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
# اختبارات وكيل 4: الفصاحة
# ═══════════════════════════════════════════

def test_eloquence_passive_voice():
    agent = EloquenceAgent()
    result = agent.improve("يتم إرسال البيانات إلى الخادم")
    assert "يُرسَل" in result.improved_text
    assert "يتم إرسال" not in result.improved_text
    assert result.was_modified
    print("  ✓ تحويل المبني للمجهول (يتم → يُفعل)")


def test_eloquence_passive_past():
    agent = EloquenceAgent()
    result = agent.improve("تم إنشاء الملف بنجاح")
    assert "أُنشئ" in result.improved_text
    assert "تم إنشاء" not in result.improved_text
    print("  ✓ تحويل الماضي المبني للمجهول (تم → فُعِل)")


def test_eloquence_padding_bishakl():
    agent = EloquenceAgent()
    result = agent.improve("النظام يعمل بشكل سريع")
    assert "سريعاً" in result.improved_text
    assert "بشكل سريع" not in result.improved_text
    print("  ✓ إزالة 'بشكل' واستبدالها بالحال")


def test_eloquence_padding_amaliya():
    agent = EloquenceAgent()
    result = agent.improve("عملية التحديث تستغرق وقتاً")
    assert "التحديث" in result.improved_text
    assert "عملية التحديث" not in result.improved_text
    print("  ✓ إزالة 'عملية' الزائدة")


def test_eloquence_calque_yaleb():
    agent = EloquenceAgent()
    result = agent.improve("التشفير يلعب دوراً مهماً في الحماية")
    assert "يؤدي دوراً" in result.improved_text
    assert "يلعب دوراً" not in result.improved_text
    print("  ✓ إصلاح 'يلعب دوراً' → 'يؤدي دوراً'")


def test_eloquence_calque_yatabar():
    agent = EloquenceAgent()
    result = agent.improve("هذا البرنامج يعتبر من أقوى البرامج")
    assert "يُعَدّ من" in result.improved_text
    print("  ✓ إصلاح 'يعتبر من' → 'يُعَدّ من'")


def test_eloquence_connectors():
    agent = EloquenceAgent()
    result = agent.improve("من الممكن أن يحدث خطأ في النظام")
    assert "قد" in result.improved_text
    assert "من الممكن أن" not in result.improved_text
    print("  ✓ تحسين حروف الربط")


def test_eloquence_grammar_comparative():
    agent = EloquenceAgent()
    result = agent.improve("هذا النظام أكثر سرعة من غيره")
    assert "أسرع" in result.improved_text
    assert "أكثر سرعة" not in result.improved_text
    print("  ✓ أفعل التفضيل بدل 'أكثر + مصدر'")


def test_eloquence_grammar_hunaka():
    agent = EloquenceAgent()
    result = agent.improve("يوجد هناك خطأ في الكود")
    assert "ثمة" in result.improved_text
    assert "يوجد هناك" not in result.improved_text
    print("  ✓ 'ثمة' بدل 'يوجد هناك'")


def test_eloquence_scoring():
    agent = EloquenceAgent()
    bad_text = "يتم إرسال البيانات بشكل سريع ومن الممكن أن يتم حذف الملفات"
    good_text = "يُرسَل البيانات سريعاً وقد يُحذَف الملفات"
    bad_score = agent.score_eloquence(bad_text)
    good_score = agent.score_eloquence(good_text)
    assert good_score > bad_score
    print("  ✓ تقييم الفصاحة (نص جيد > نص ركيك)")


def test_eloquence_combined():
    """اختبار شامل — عدة مشاكل في نص واحد."""
    agent = EloquenceAgent()
    text = "تم تنفيذ عملية التحديث بشكل كبير وبالتالي يعتبر من أفضل الأنظمة"
    result = agent.improve(text)
    assert result.was_modified
    assert len(result.fixes) >= 3  # على الأقل 3 إصلاحات
    assert result.eloquence_score_after > result.eloquence_score_before
    print("  ✓ إصلاحات متعددة في نص واحد")


def test_eloquence_clean_text():
    """نص فصيح لا يحتاج تعديل."""
    agent = EloquenceAgent()
    result = agent.improve("أُرسِلت الرسالة بنجاح")
    assert len(result.fixes) == 0
    print("  ✓ نص نظيف — لا تعديل")


def test_eloquence_stats():
    agent = EloquenceAgent()
    agent.improve("يتم إرسال البيانات بشكل سريع")
    stats = agent.get_stats()
    assert stats["texts_processed"] == 1
    assert stats["total_fixes"] >= 2
    assert stats["passive_fixes"] >= 1
    assert stats["padding_removals"] >= 1
    print("  ✓ إحصائيات الفصاحة")


# ═══════════════════════════════════════════
# اختبارات وكيل 5: المكتشف
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


def test_builder_no_release_without_approval():
    """اختبار أن التطبيق لا يُصدر بدون موافقة."""
    tmp = tempfile.mkdtemp()
    try:
        builder = BuilderAgent(data_dir=tmp)
        app = builder.build_app("spellchecker")
        assert app is not None
        assert app.status == "draft"
        # بدون callback — يبقى في الانتظار
        result = builder.request_release(app.app_id)
        assert result["status"] == "awaiting"
        assert app.status == "awaiting_approval"
        # لا يعمل لأنه ليس released
        run_result = builder.run_app(app.app_id, "نص اختبار")
        assert run_result["processed"] is False
        print("  ✓ لا إصدار بدون موافقة")
    finally:
        shutil.rmtree(tmp)


def test_builder_approve_release():
    """اختبار الموافقة على الإصدار."""
    tmp = tempfile.mkdtemp()
    try:
        def user_approves(proposal):
            return {"decision": "approve", "notes": "ممتاز", "approved_by": "دلال"}

        builder = BuilderAgent(data_dir=tmp, release_callback=user_approves)
        app = builder.build_app("spellchecker")
        # حوّل لـ testing يدوياً (عادةً يحصل بعد الاختبار)
        app.status = "testing"
        app.test_results = {"accuracy": 0.9}

        result = builder.request_release(app.app_id, callback=user_approves)
        assert result["status"] == "released"
        assert "سرية" in result["message"] or "سري" in result["message"]
        assert app.status == "released"
        assert app.privacy_level == "local_only"
        assert app.approved_by == "دلال"
        print("  ✓ الموافقة على الإصدار بسرية")
    finally:
        shutil.rmtree(tmp)


def test_builder_reject_release():
    """اختبار رفض الإصدار."""
    tmp = tempfile.mkdtemp()
    try:
        def user_rejects(proposal):
            return {"decision": "reject", "notes": "يحتاج تحسين"}

        builder = BuilderAgent(data_dir=tmp)
        app = builder.build_app("translation_qa")
        app.status = "testing"
        app.test_results = {"accuracy": 0.8}

        result = builder.request_release(app.app_id, callback=user_rejects)
        assert result["status"] == "rejected"
        assert app.status == "rejected"
        # التطبيق المرفوض لا يعمل
        run_result = builder.run_app(app.app_id, "نص")
        assert run_result["processed"] is False
        print("  ✓ رفض الإصدار")
    finally:
        shutil.rmtree(tmp)


def test_builder_defer_release():
    """اختبار تأجيل الإصدار."""
    tmp = tempfile.mkdtemp()
    try:
        def user_defers(proposal):
            return {"decision": "defer"}

        builder = BuilderAgent(data_dir=tmp)
        app = builder.build_app("bidi_tool")
        app.status = "testing"
        app.test_results = {"accuracy": 0.85}

        result = builder.request_release(app.app_id, callback=user_defers)
        assert result["status"] == "deferred"
        assert app.status == "awaiting_approval"
        print("  ✓ تأجيل الإصدار")
    finally:
        shutil.rmtree(tmp)


def test_builder_modify_before_release():
    """اختبار طلب تعديل قبل الإصدار."""
    tmp = tempfile.mkdtemp()
    try:
        def user_wants_changes(proposal):
            return {"decision": "modify", "notes": "أضف قاعدة للتاء المربوطة"}

        builder = BuilderAgent(data_dir=tmp)
        app = builder.build_app("spellchecker")
        app.status = "testing"
        app.test_results = {"accuracy": 0.9}

        result = builder.request_release(app.app_id, callback=user_wants_changes)
        assert result["status"] == "needs_modification"
        assert app.status == "draft"  # رجع لمسودة
        print("  ✓ طلب تعديل قبل الإصدار")
    finally:
        shutil.rmtree(tmp)


def test_builder_privacy_always_local():
    """اختبار أن كل التطبيقات تبقى محلية."""
    tmp = tempfile.mkdtemp()
    try:
        def user_approves(proposal):
            assert proposal["privacy_level"] == "local_only"
            return {"decision": "approve"}

        builder = BuilderAgent(data_dir=tmp)
        app = builder.build_app("smart_glossary")
        assert app.privacy_level == "local_only"

        app.status = "testing"
        app.test_results = {"accuracy": 0.8}
        builder.request_release(app.app_id, callback=user_approves)
        assert app.privacy_level == "local_only"
        print("  ✓ السرية — دائماً محلي فقط")
    finally:
        shutil.rmtree(tmp)


def test_builder_pending_approvals():
    """اختبار عرض التطبيقات المعلّقة."""
    tmp = tempfile.mkdtemp()
    try:
        builder = BuilderAgent(data_dir=tmp)
        app1 = builder.build_app("spellchecker")
        app2 = builder.build_app("translation_qa")
        app1.status = "awaiting_approval"
        app2.status = "testing"

        pending = builder.get_pending_approvals()
        assert len(pending) == 2
        print("  ✓ عرض التطبيقات المعلّقة")
    finally:
        shutil.rmtree(tmp)


def test_builder_cycle_with_approval():
    """اختبار الدورة الكاملة مع طلب الموافقة."""
    tmp = tempfile.mkdtemp()
    try:
        approvals = []

        def track_approvals(proposal):
            approvals.append(proposal["name_ar"])
            return {"decision": "approve", "approved_by": "دلال"}

        discovery = DiscoveryAgent(data_dir=tmp)
        builder = BuilderAgent(
            data_dir=tmp,
            discovery_agent=discovery,
            release_callback=track_approvals,
        )

        stats = {
            "normalizer": {"texts_processed": 50, "extra_rules_applied": 0},
            "qa_evaluator": {"evaluations": 50, "avg_score": 60.0,
                             "literal_detections": 12, "untranslated_detections": 3,
                             "passive_issues": 1, "weak_style_issues": 4,
                             "total_issues": 20},
            "bidi_fixer": {"texts_processed": 50},
            "eloquence": {"texts_processed": 50, "total_fixes": 30},
            "discovery": {"patterns_discovered": 6, "rules_generated": 2,
                          "algorithms_created": 0, "errors_collected": 30},
            "builder": {"apps_built": 0},
        }
        summary = builder.run_builder_cycle(stats, release_callback=track_approvals)
        assert "release_requests" in summary
        assert "awaiting_approval" in summary
        print("  ✓ دورة المُنتِج مع طلب الموافقة")
    finally:
        shutil.rmtree(tmp)


def test_builder_stats_track_decisions():
    """اختبار أن الإحصائيات تتبع قرارات المستخدم."""
    tmp = tempfile.mkdtemp()
    try:
        builder = BuilderAgent(data_dir=tmp)
        app1 = builder.build_app("spellchecker")
        app1.status = "testing"
        app1.test_results = {"accuracy": 0.9}

        app2 = builder.build_app("bidi_tool")
        app2.status = "testing"
        app2.test_results = {"accuracy": 0.8}

        builder.request_release(app1.app_id,
                                callback=lambda p: {"decision": "approve"})
        builder.request_release(app2.app_id,
                                callback=lambda p: {"decision": "reject", "notes": "لا"})

        stats = builder.get_stats()
        assert stats["user_approvals"] == 1
        assert stats["user_rejections"] == 1
        assert stats["apps_released"] == 1
        assert stats["apps_rejected"] == 1
        print("  ✓ إحصائيات قرارات المستخدم")
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


def test_pipeline_interactive():
    """اختبار خط الأنابيب مع الوضع التفاعلي."""
    tmp = tempfile.mkdtemp()
    try:
        pipeline = Pipeline(data_dir=tmp)

        def approve_all(proposals):
            return [{"issue_id": p["issue_id"], "decision": "approve"} for p in proposals]

        result = pipeline.process(
            source="Please look up the information",
            target="رجاء انظر فوق المعلومات",
            decision_callback=approve_all,
        )
        # التعديل المعتمد يجب أن يظهر في النص النهائي
        assert "انظر فوق" not in result.final_text
        assert result.quality_final_score >= result.quality_score
        assert result.quality_verification.get("fixes_verified", 0) > 0
        print("  ✓ خط الأنابيب التفاعلي")
    finally:
        shutil.rmtree(tmp)


def test_pipeline_auto_approve():
    """اختبار خط الأنابيب مع الاعتماد التلقائي."""
    tmp = tempfile.mkdtemp()
    try:
        pipeline = Pipeline(data_dir=tmp)
        result = pipeline.process(
            source="Please look up the data",
            target="رجاء انظر فوق البيانات",
            auto_approve=True,
        )
        # الترجمة الحرفية (high) تُعتمد تلقائياً
        assert "انظر فوق" not in result.final_text
        print("  ✓ خط الأنابيب مع اعتماد تلقائي")
    finally:
        shutil.rmtree(tmp)


# ═══════════════════════════════════════════
# اختبارات المُصدّر (Exporter)
# ═══════════════════════════════════════════

def _make_sample_result():
    """إنشاء نتيجة وهمية للاختبارات."""
    return PipelineResult(
        source="The system uses encryption to protect data",
        target_original="النظام يستخدم encryption لحمايه البيانات",
        target_normalized="النظام يستخدم encryption لحماية البيانات",
        normalizer_changes=[{"type": "taa_marbuta", "original": "لحمايه", "fixed": "لحماية"}],
        quality_score=72.0,
        quality_final_score=85.0,
        quality_grade="جيد",
        quality_issues=[{
            "issue_id": "Q001",
            "category": "كلمة_غير_مترجمة",
            "severity": "high",
            "description": "كلمة encryption غير مترجمة",
            "suggestion": "تشفير",
            "user_decision": "approve",
            "applied": True,
        }],
        target_bidi_fixed="النظام يستخدم التشفير لحماية البيانات",
        target_eloquent="يستخدم النظام التشفير لحماية البيانات",
        eloquence_fixes=[{
            "rule": "word_order",
            "category": "grammar",
            "original": "النظام يستخدم",
            "improved": "يستخدم النظام",
            "explanation": "تقديم الفعل على الفاعل",
        }],
        eloquence_score_before=65.0,
        eloquence_score_after=88.0,
        final_text="يستخدم النظام التشفير لحماية البيانات",
    )


def test_exporter_txt():
    tmp = tempfile.mkdtemp()
    try:
        exporter = Exporter(output_dir=tmp)
        result = _make_sample_result()
        path = exporter.to_txt(result, "test_output.txt")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "يستخدم النظام التشفير" in content
        assert "TarjimTech" in content
        assert "72.0" in content or "72" in content
        assert "تقديم الفعل" in content
        print("  ✓ تصدير TXT")
    finally:
        shutil.rmtree(tmp)


def test_exporter_txt_auto_filename():
    tmp = tempfile.mkdtemp()
    try:
        exporter = Exporter(output_dir=tmp)
        result = _make_sample_result()
        path = exporter.to_txt(result)
        assert os.path.exists(path)
        assert path.endswith(".txt")
        print("  ✓ تصدير TXT — اسم تلقائي")
    finally:
        shutil.rmtree(tmp)


def test_exporter_json():
    tmp = tempfile.mkdtemp()
    try:
        exporter = Exporter(output_dir=tmp)
        result = _make_sample_result()
        path = exporter.to_json(result, "test_report.json")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["source"] == result.source
        assert data["final_text"] == result.final_text
        assert "exported_at" in data
        print("  ✓ تصدير JSON")
    finally:
        shutil.rmtree(tmp)


def test_exporter_docx_fallback():
    """اختبار أن DOCX يعود لـ TXT إذا python-docx غير مثبتة."""
    tmp = tempfile.mkdtemp()
    try:
        exporter = Exporter(output_dir=tmp)
        result = _make_sample_result()
        path = exporter.to_docx(result, "test_output.docx")
        # إما ملف docx حقيقي أو fallback لـ txt
        assert os.path.exists(path.split("\n")[0])
        print("  ✓ تصدير DOCX (أو fallback)")
    finally:
        shutil.rmtree(tmp)


def test_exporter_export_all():
    tmp = tempfile.mkdtemp()
    try:
        exporter = Exporter(output_dir=tmp)
        result = _make_sample_result()
        paths = exporter.export_all(result, "test_all")
        assert "txt" in paths
        assert "json" in paths
        assert "docx" in paths
        assert os.path.exists(paths["txt"])
        assert os.path.exists(paths["json"])
        print("  ✓ تصدير الكل دفعة واحدة")
    finally:
        shutil.rmtree(tmp)


def test_pipeline_export():
    """اختبار التصدير من خط الأنابيب مباشرة."""
    tmp = tempfile.mkdtemp()
    output_dir = os.path.join(tmp, "output")
    try:
        pipeline = Pipeline(data_dir=tmp)
        result = pipeline.process(
            source="Hello world",
            target="مرحبا بالعالم",
        )
        path = pipeline.export_txt(result, output_dir=output_dir)
        assert os.path.exists(path)
        path_json = pipeline.export_json(result, output_dir=output_dir)
        assert os.path.exists(path_json)
        print("  ✓ التصدير من خط الأنابيب")
    finally:
        shutil.rmtree(tmp)


# ═══════════════════════════════════════════
# تشغيل كل الاختبارات
# ═══════════════════════════════════════════

def main():
    print("\n" + "=" * 60)
    print("  اختبارات نظام TarjimTech — الوكلاء الستة")
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
            test_qa_interactive_approve,
            test_qa_interactive_reject,
            test_qa_interactive_modify,
            test_qa_auto_review,
            test_qa_verify_after_apply,
            test_qa_interactive_stats,
        ]),
        ("وكيل 3: معالج BiDi", [
            test_bidi_latin_isolation,
            test_bidi_rtl_paragraph,
            test_bidi_clean_marks,
            test_bidi_stats,
        ]),
        ("وكيل 4: الفصاحة", [
            test_eloquence_passive_voice,
            test_eloquence_passive_past,
            test_eloquence_padding_bishakl,
            test_eloquence_padding_amaliya,
            test_eloquence_calque_yaleb,
            test_eloquence_calque_yatabar,
            test_eloquence_connectors,
            test_eloquence_grammar_comparative,
            test_eloquence_grammar_hunaka,
            test_eloquence_scoring,
            test_eloquence_combined,
            test_eloquence_clean_text,
            test_eloquence_stats,
        ]),
        ("وكيل 5: المكتشف", [
            test_discovery_collect_errors,
            test_discovery_pattern_analysis,
            test_discovery_save_load,
            test_discovery_cycle,
        ]),
        ("وكيل 6: المُنتِج", [
            test_builder_observe,
            test_builder_build_app,
            test_builder_build_custom_app,
            test_builder_save_load,
            test_builder_cycle,
            test_builder_with_discovery_learning,
            test_builder_no_release_without_approval,
            test_builder_approve_release,
            test_builder_reject_release,
            test_builder_defer_release,
            test_builder_modify_before_release,
            test_builder_privacy_always_local,
            test_builder_pending_approvals,
            test_builder_cycle_with_approval,
            test_builder_stats_track_decisions,
        ]),
        ("خط الأنابيب", [
            test_pipeline_basic,
            test_pipeline_full_flow,
            test_pipeline_interactive,
            test_pipeline_auto_approve,
        ]),
        ("المُصدّر (Exporter)", [
            test_exporter_txt,
            test_exporter_txt_auto_filename,
            test_exporter_json,
            test_exporter_docx_fallback,
            test_exporter_export_all,
            test_pipeline_export,
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
