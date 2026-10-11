# خطة الفحص الشامل والإصلاح وإعادة التصميم لنظام إدارة صيانة الأجهزة الطبية (MEMMS)

نظام **MEMMS — Medical Equipment Maintenance Management System** هو تطبيق مكتبي متكامل لإدارة وصيانة الأجهزة الطبية في المستشفيات والمراكز الصحية.
تم إجراء فحص شامل (Full Audit) لجميع مكونات المشروع الحالية (Models, Repositories, Services, Views, Dialogs, Theme, Database, Reports, Tests).

---

## 1. نتائج الفحص الشامل للمشروع (Full Project Audit Findings)

### أ. القيود والقرارات الإلزامية التي تم رصد مخالفتها في الكود الحالي:
1. **اللغة والاتجاه (Arabic Only & RTL):**
   - البرنامج يحتوي حاليًا على أزرار تبديل اللغة (Language Switcher) وملف ترجمة إنجليزي `en.json`.
   - بعض النصوص في الواجهات مكتوبة مباشرة بالإنجليزية أو تخلط بين العربية والإنجليزية.
   - الاتجاه الافتراضي يحتاج إلى ضبط وتطبيق `RTL` الصارم على مستوى التطبيق `QApplication.setLayoutDirection(Qt.LayoutDirection.RightToLeft)`.
2. **الوضع الداكن (Light Theme Only):**
   - يحتوي `TopNavbar` و `ThemeManager` على زر تبديل الثيم (Moon/Sun) و `DARK_PALETTE`.
   - يجب حذف الوضع الداكن وأزراره والاعتماد حصريًا على **Light Theme** طبي مؤسسي نظيف ومريح للعين.
3. **الأيقونات والـ Emojis:**
   - الواجهة لا تحتوي على إيموجي ظاهرة، ولكن يجب التحقق المستمر واستخدام مكتبة `qtawesome` / `IconHelper` الموحدة لجميع الأيقونات بدقة.
4. **أزرار الإضافة (Add Buttons) المخفية:**
   - مكون `DataTable` في `src/ui/components/data_table.py` يحتوي على `self.add_btn.setVisible(False)` افتراضيًا، مما تسبب في اختفاء زر `+ إضافة` في شاشات الأجهزة، الأقسام، الشركات، الفنيين وغيرها.
5. **البيانات الوهمية في لوحة التحكم (Mock Dashboard Data):**
   - شاشة `dashboard_view.py` تحتوي على قيم ثابتة وهمية `(1, 2, 3, 4)` في رسم الأولويات `BarPriorityChart` بدل حسابها من قاعدة البيانات.
   - الدالة `main.py:seed_demo_hospital_data()` كانت تفرض بيانات أجهزة تجريبية افتراضيًا. يجب إتاحة نظام نظيف يعرض "لا توجد بيانات" (Empty State) عند خلو النظام، مع إمكانية التهيئة الحقيقية للمنشأة.

---

### ب. الأخطاء البرمجية وعدم تطابق الحقول (Field Mismatches & Bugs):
1. **`eq.asset_id` بدل `eq.asset_number`:**
   - في `src/ui/views/pm_execution_dialog.py` (سطر 186): استدعاء `eq.asset_id` غير الموجود في `Equipment`.
   - في `src/ui/views/preventive_view.py` (أسطر 205، 372): استدعاء `eq.asset_id` غير الموجود.
   - في `src/ui/views/pm_plan_dialog.py` (سطر 171): استدعاء `eq.asset_id` غير الموجود.
2. **`wo.title` غير الموجود:**
   - في `src/ui/views/stock_transaction_dialog.py` (سطر 142): `wo.title[:25]` يسبب `AttributeError` لأن `WorkOrder` لا يحتوي على `title` بل `work_order_number` و `failure_description`.
3. **أخطاء تقارير أوامر العمل والمخزون في `report_service.py`:**
   - استدعاء `o.total_cost` بينما الحقول في الموديل هي `total_labor_cost` و `total_parts_cost`.
   - استدعاء `o.parts_cost` و `o.labor_cost` و `o.order_number`.
   - استدعاء `s.execution.technician.name_ar` بينما حقل الفني هو `full_name`.
   - استدعاء `p.manufacturer.name_ar` بينما حقل المورد هو `name`.
4. **الاعتماد على ترتيب القاموس في تصدير التقارير:**
   - في `report_service.py` (تصدير Excel و HTML): الاعتماد على `list(row.values())[1:]` مما يؤدي إلى إزاحة البيانات بين الأعمدة في حال إضافة حقول جديدة. يجب الاعتماد على مصفوفة مفاتيح صريحة (Explicit Column Mapping).

---

## 2. التغييرات المقترحة (Proposed Changes)

### أ. قاعدة البيانات والنماذج (Database & Models Layer)
- [MODIFY] [`src/models/work_order.py`](file:///e:/cmms/src/models/work_order.py):
  - إضافة خاصية `@property def total_cost(self)` لحساب مجموع تكلفة قطع الغيار والعمالة تلقائيًا.
  - تعزيز ربط قطع الغيار بأمر العمل `WorkOrderPart` مع حركات المخزون.
- [MODIFY] [`src/core/database.py`](file:///e:/cmms/src/core/database.py):
  - تحسين آلية إنشاء الجداول والتأكد من وجود المستخدم الإداري الأول والأدوار الأساسية بشكل آمن.

---

### ب. خدمات النظام ومنطق الأعمال (Business Logic & Services)
- [MODIFY] [`src/services/equipment_service.py`](file:///e:/cmms/src/services/equipment_service.py):
  - التحقق من فرادة رقم الأصل والرقم التسلسلي.
  - دعم إحصائيات الأجهزة الحقيقية المحدثة.
- [MODIFY] [`src/services/work_order_service.py`](file:///e:/cmms/src/services/work_order_service.py):
  - ضبط استهلاك قطع الغيار وخصمها من المخزون مع التحقق من توفر الكمية.
  - تسجيل حركات المخزون من نوع `out_work_order` عند صرف قطعة.
  - تحديث تكلفة أمر العمل تلقائيًا.
- [MODIFY] [`src/services/pm_service.py`](file:///e:/cmms/src/services/pm_service.py):
  - تصحيح استدعاءات `eq.asset_number`.
  - إدارة الجداول الوقائية وتحديث حالة الأجهزة عند التنفيذ وتوليد الجدول القادم تلقائيًا.
- [MODIFY] [`src/services/report_service.py`](file:///e:/cmms/src/services/report_service.py):
  - تصحيح جميع أسماء الحقول ومواءمتها مع الـ Models.
  - تطبيق Mapping صريح بالأعمدة لجميع التقارير (الأجهزة، أوامر الصيانة، الصيانة الوقائية، المخزون).
  - بناء تقارير PDF بتنسيق عربي RTL أنيق يشمل ترويسة المنشأة، بطاقات الملخص، والجداول ذات التنسيق المحاذي لليمين.
  - تحسين تصدير Excel بتنسيق RTL وأعمدة واضحة وأرقام مالية مهيأة.

---

### ج. واجهة المستخدم وتجربة المستخدم (UI/UX Redesign & Fixes)
- [MODIFY] [`src/ui/theme/tokens.py`](file:///e:/cmms/src/ui/theme/tokens.py) & [`src/ui/theme/theme_manager.py`](file:///e:/cmms/src/ui/theme/theme_manager.py):
  - حصر النظام على **Light Theme** طبي احترافي عالي التباين والأناقة.
  - إزالة كود Dark Mode والأزرار المرتبطة به.
- [MODIFY] [`src/core/i18n.py`](file:///e:/cmms/src/core/i18n.py):
  - فرض اللغة العربية كلغة وحيدة للتطبيق، وضبط اتجاه التطبيق RTL.
- [MODIFY] [`src/ui/components/top_navbar.py`](file:///e:/cmms/src/ui/components/top_navbar.py):
  - إزالة زر تبديل اللغة وزر تبديل الثيم.
  - عرض عنوان القسم الحالي، شارة المنشأة، التنبيهات، ومعلومات المستخدم مع زر تسجيل الخروج.
- [MODIFY] [`src/ui/components/sidebar.py`](file:///e:/cmms/src/ui/components/sidebar.py):
  - ترتيب القوائم الجانبية باللغة العربية: لوحة التحكم، الأجهزة الطبية، الأقسام، المواقع، أوامر العمل، الصيانة الوقائية، قطع الغيار، الموردين، العقود، التقارير، سجل التدقيق، الإعدادات.
- [MODIFY] [`src/ui/components/data_table.py`](file:///e:/cmms/src/ui/components/data_table.py):
  - تفعيل زر الإضافة وجعله ظاهرًا افتراضيًا مع نصوص عربية واضحة ومخصصة لكل شاشة (`+ إضافة جهاز`، `+ إضافة قسم`، إلخ).
- [MODIFY] [`src/ui/views/dashboard_view.py`](file:///e:/cmms/src/ui/views/dashboard_view.py):
  - حذف أي أرقام Mock/Hardcoded نهائيًا.
  - حساب مؤشرات الأجهزة وأوامر العمل ذات الأولوية المختلفة مباشرة من قاعدة البيانات.
  - إظهار حالة فارغة (Empty State) أنيقة عند خلو البيانات.
- [MODIFY] [`src/ui/views/equipment_view.py`](file:///e:/cmms/src/ui/views/equipment_view.py) & [`equipment_dialog.py`](file:///e:/cmms/src/ui/views/equipment_dialog.py):
  - إظهار زر `+ إضافة جهاز` بوضوح.
  - استكمال نموذج إضافة وتعديل الجهاز بالعربية مع فحص الحقول المطلوبة والتأكد من صحة التواريخ.
- [MODIFY] [`src/ui/views/equipment_details_dialog.py`](file:///e:/cmms/src/ui/views/equipment_details_dialog.py):
  - تنظيم تفاصيل الجهاز في تبويبات واضحة: عام والموقع، البيانات المالية والضمان، سجل النقل، أوامر الصيانة، الصيانة الوقائية، المرفقات.
- [MODIFY] [`src/ui/views/preventive_view.py`](file:///e:/cmms/src/ui/views/preventive_view.py), [`pm_plan_dialog.py`](file:///e:/cmms/src/ui/views/pm_plan_dialog.py), [`pm_execution_dialog.py`](file:///e:/cmms/src/ui/views/pm_execution_dialog.py):
  - تصحيح حقول `asset_id` إلى `asset_number`.
  - التحقق من عمل مهام وقوائم الفحص (Checklists) وحفظ النتائج.
- [MODIFY] [`src/ui/views/inventory_view.py`](file:///e:/cmms/src/ui/views/inventory_view.py) & [`stock_transaction_dialog.py`](file:///e:/cmms/src/ui/views/stock_transaction_dialog.py):
  - تصحيح `wo.title` واستبدالها برقم أمر العمل والوصف.
  - ربط حركات الاستلام والصرف بدقة.
- [MODIFY] [`src/ui/views/reports_view.py`](file:///e:/cmms/src/ui/views/reports_view.py):
  - تعريب كامل لشاشة التقارير وتوفير أزرار تصدير PDF و Excel حقيقية بدون مفاتيح ترجمة إنجليزية.
- [MODIFY] [`src/ui/views/settings_view.py`](file:///e:/cmms/src/ui/views/settings_view.py):
  - تمكين حفظ وتعديل بيانات المنشأة الطبية (الاسم، الكود، الهاتف، العنوان) واستخدامها في ترويسات التقارير.
  - فحص النسخ الاحتياطي والاستعادة.
- [MODIFY] [`main.py`](file:///e:/cmms/main.py):
  - تطبيق RTL العام على `QApplication`.
  - تنظيف آلية بدء التشغيل لتعمل بشكل نظامي.

---

## 3. خطة التحقق والاختبار (Verification Plan)

### الاختبارات المؤتمتة (Automated Tests):
تشغيل حزمة الاختبارات بالكامل بعد كل مرحلة:
```bash
python -m pytest
```
كتابة وتحديث اختبارات شاملة تغطي:
1. `tests/test_phase2_core.py`: اختبارات الـ Models، الصلاحيات، والمصادقة.
2. `tests/test_phase3_equipment.py`: اختبارات إضافة، تعديل، نقل وحذف الأجهزة.
3. `tests/test_phase8_reports.py`: اختبارات تصدير التقارير ببيانات حقيقية بصيغتي Excel و PDF والتأكد من صحة الأعمدة.
4. `tests/test_maintenance_and_inventory.py`: اختبارات تكامل دورة أوامر الصيانة واستهلاك قطع الغيار وتحديث المخزون والخطط الوقائية.

### التحقق الوظيفي الشامل (End-to-End Manual / Integration Workflow):
تنفيذ سيناريو تفاعلي حقيقي يمر بالخطوات التالية:
1. تسجيل الدخول كمدير للنظام.
2. فتح الإعدادات وتحديث بيانات المستشفى.
3. إضافة قسم وموقع ومورد وفني.
4. إضافة جهاز طبي جديد والتحقق من ظهوره في جدول الأجهزة.
5. فتح تفاصيل الجهاز وتعديل بياناته ونقله لموقع آخر.
6. إنشاء أمر صيانة للجهاز وتعيين الفني وصرف قطعة غيار له والتحقق من خصم المخزون وإغلاق الأمر.
7. إنشاء خطة صيانة وقائية وتنفيذ مهمة فحص وتسجيل النتيجة وتحديث تاريخ الصيانة القادم.
8. فتح لوحة التحكم والتحقق من أن جميع الأرقام والرسوم البيانية مطابقة للواقع دون أرقام تجريبية.
9. إنشاء تقرير وتصدير ملف PDF وفتحه للتأكد من تنسيق اللغة العربية واتجاه RTL.
10. تصدير ملف Excel والتأكد من دقة الأعمدة والبيانات.
11. إنشاء نسخة احتياطية من قاعدة البيانات بنجاح.
