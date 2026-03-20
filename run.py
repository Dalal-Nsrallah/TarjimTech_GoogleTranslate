"""
🚀 تشغيل نظام TarjimTech — واجهة بسيطة بالعربي
═══════════════════════════════════════════════════
شغّلي هذا الملف: python run.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.pipeline import Pipeline


def main():
    print("\n" + "=" * 60)
    print("  مرحباً بك في نظام TarjimTech")
    print("  نظام الوكلاء الستة لتحسين الترجمة العربية")
    print("=" * 60)

    # إنشاء النظام
    pipeline = Pipeline(
        data_dir="data",
        glossary_path="glossary/technical_terms.json"
        if os.path.exists("glossary/technical_terms.json") else None,
    )

    while True:
        print("\n" + "─" * 40)
        print("  اختاري:")
        print("  1. تحسين ترجمة")
        print("  2. تحسين ترجمة (مع أخذ رأيك)")
        print("  3. تحسين ترجمة (تلقائي)")
        print("  4. تقرير النظام")
        print("  5. خروج")
        print("─" * 40)

        choice = input("\n  اختيارك (1-5): ").strip()

        if choice == "1":
            run_basic(pipeline)
        elif choice == "2":
            run_interactive(pipeline)
        elif choice == "3":
            run_auto(pipeline)
        elif choice == "4":
            show_report(pipeline)
        elif choice == "5":
            print("\n  شكراً لاستخدام TarjimTech! 👋\n")
            break
        else:
            print("  ⚠ اختيار غير صحيح، حاولي مرة ثانية")


def get_texts():
    """طلب النصوص من المستخدم."""
    print("\n  أدخلي النص الإنجليزي (المصدر):")
    source = input("  EN> ").strip()
    if not source:
        print("  ⚠ النص فارغ!")
        return None, None

    print("\n  أدخلي الترجمة العربية (من Google Translate مثلاً):")
    target = input("  AR> ").strip()
    if not target:
        print("  ⚠ النص فارغ!")
        return None, None

    return source, target


def show_result(result, pipeline):
    """عرض النتائج بشكل واضح."""
    print("\n" + "=" * 60)
    print("  النتائج")
    print("=" * 60)

    print(f"\n  📝 النص الأصلي:")
    print(f"     {result.target_original}")

    print(f"\n  ✅ النص المحسّن:")
    print(f"     {result.final_text}")

    print(f"\n  📊 درجة الجودة: {result.quality_score:.0f}/100 ({result.quality_grade})")

    if result.eloquence_fixes:
        print(f"\n  📖 تحسينات الفصاحة ({len(result.eloquence_fixes)}):")
        for fix in result.eloquence_fixes:
            print(f"     • {fix['original']} → {fix['improved']}")
            print(f"       السبب: {fix['explanation']}")

    if result.quality_issues:
        print(f"\n  ⚠ ملاحظات الجودة ({len(result.quality_issues)}):")
        for issue in result.quality_issues:
            status = "✓" if issue.get("applied") else "!"
            print(f"     [{status}] {issue['description']}")

    if result.bidi_issues:
        print(f"\n  🔄 إصلاحات الاتجاه: {len(result.bidi_issues)}")

    if result.normalizer_changes:
        print(f"\n  🔧 تطبيعات: {len(result.normalizer_changes)}")

    # عرض خيار التصدير
    print("\n" + "─" * 40)
    print("  هل تريدين حفظ النتيجة؟")
    print("  1. حفظ كملف نصي (TXT)")
    print("  2. حفظ كملف Word (DOCX)")
    print("  3. حفظ كل الصيغ")
    print("  4. لا، شكراً")

    export_choice = input("\n  اختيارك (1-4): ").strip()

    if export_choice == "1":
        path = pipeline.export_txt(result)
        print(f"\n  ✓ تم الحفظ: {path}")
    elif export_choice == "2":
        path = pipeline.export_docx(result)
        print(f"\n  ✓ تم الحفظ: {path}")
    elif export_choice == "3":
        paths = pipeline.export_all(result)
        print(f"\n  ✓ تم الحفظ:")
        for fmt, path in paths.items():
            print(f"     {fmt}: {path}")


def run_basic(pipeline):
    """تشغيل بسيط بدون تفاعل."""
    source, target = get_texts()
    if not source:
        return

    print("\n  ⏳ جاري التحسين...")
    result = pipeline.process(source, target)
    show_result(result, pipeline)


def run_interactive(pipeline):
    """تشغيل تفاعلي — يأخذ رأي المستخدم."""
    source, target = get_texts()
    if not source:
        return

    def user_decision(proposals):
        """عرض المقترحات وأخذ رأي المستخدم."""
        if not proposals:
            return []

        print("\n" + "─" * 40)
        print("  🔍 وجدت مشاكل في الترجمة — ما رأيك؟")
        print("─" * 40)

        decisions = []
        for p in proposals:
            print(f"\n  المشكلة: {p['description']}")
            print(f"  النوع: {p['category']} | الخطورة: {p['severity']}")
            if p.get("suggestion"):
                print(f"  الاقتراح: {p['suggestion']}")

            print("    1. اعتمد التصحيح ✓")
            print("    2. ارفض ✗")
            print("    3. عدّل بنفسك ✎")

            choice = input("    قرارك (1-3): ").strip()

            if choice == "1":
                decisions.append({
                    "issue_id": p["issue_id"],
                    "decision": "approve",
                })
            elif choice == "3":
                correction = input("    أدخلي التصحيح: ").strip()
                decisions.append({
                    "issue_id": p["issue_id"],
                    "decision": "modify",
                    "correction": correction,
                })
            else:
                decisions.append({
                    "issue_id": p["issue_id"],
                    "decision": "reject",
                })

        return decisions

    print("\n  ⏳ جاري التحليل...")
    result = pipeline.process(
        source, target,
        decision_callback=user_decision,
    )
    show_result(result, pipeline)


def run_auto(pipeline):
    """تشغيل تلقائي — يعتمد المشاكل الكبيرة تلقائياً."""
    source, target = get_texts()
    if not source:
        return

    print("\n  ⏳ جاري التحسين التلقائي...")
    result = pipeline.process(source, target, auto_approve=True)
    show_result(result, pipeline)


def show_report(pipeline):
    """عرض تقرير النظام."""
    report = pipeline.get_system_report()
    print("\n" + "=" * 60)
    print("  تقرير النظام")
    print("=" * 60)
    print(f"\n  نصوص معالَجة: {report['texts_processed']}")
    print(f"  تطبيقات مُصدَرة: {report['released_apps_count']}")

    stats = report["agent_stats"]
    print("\n  إحصائيات الوكلاء:")
    for agent_name, agent_stats in stats.items():
        processed = agent_stats.get("texts_processed",
                                     agent_stats.get("evaluations", 0))
        print(f"    • {agent_name}: {processed} نص")


if __name__ == "__main__":
    main()
