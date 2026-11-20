# BugfixedHL + Opposing Force (bhlop4)

مود لـHalf-Life يجمع **BugfixedHL** (الأساس) مع **أسلحة Opposing Force** العشرة.
الهدف مود سباق نظيف: مؤقت، وقوائم BHL، ومن دون ميزات زائدة.

## الحزمة الحالية (Linux)

- **الرابط:** [bhlop4-bhlbase-linux.zip](https://github.com/Abdo-X684/Bugfixhl-speedrun-op4/raw/d79fb84deeea1a19f0dd1b93a0866e3bfe2edc3f/build-evidence/bhl-base-linux-mod/bhlop4-bhlbase-linux.zip)
- **SHA256:** `93ca8939454dcb1dc9bd7f36708e17f157ad27d7aa42fc87f6959b6c47e10138`
- **التعليمات:** ملف `INSTALL.md` داخل الحزمة، والخطوات مكتوبة أدناه أيضاً.

## الحالة

| البند | الوضع |
| --- | --- |
| تشغيل اللعبة | ✅ يبدأ (أبلغ المستخدم) |
| قائمة BHL | ✅ تفتح (أبلغ المستخدم) |
| أسلحة OP4 | ✅ تعمل (أبلغ المستخدم) |
| الانهيار في HUD الذخيرة | ✅ اختفى بعد إعادة البناء بتحسين (`-O2`) |
| ثقل اللعبة | ✅ خفّ كثيراً بعد إعادة البناء بتحسين |
| إزالة التحديث التلقائي من Advanced > About | ✅ مُنفَّذ في الكود، ولم يُختبر بعد داخل اللعبة |
| اللون الافتراضي للـHUD أخضر (`0 160 0`) | ✅ مُنفَّذ في الكود، ولم يُختبر بعد داخل اللعبة |
| ملف الترجمة `bhlop4_english.txt` | ✅ مُضاف، ولم يُتحقق بعد من ظهور النصوص |
| الموسيقى | ❓ لم تُختبر على لينكس |
| بناء Windows | ❌ متوقف، فتشغيلات GitHub Actions تفشل قبل تنفيذ أي خطوة |

## التشغيل على Linux

1. تأكد من تثبيت Half-Life: Opposing Force، ومن وجود مجلد `gearbox/` بجانب `valve/`.
2. احذف أي مجلد `bhlop4` قديم.
3. فكّ الحزمة داخل مجلد اللعبة الرئيسي، بجانب `valve/` و`gearbox/`.
4. شغّل اللعبة بخيار `-game bhlop4` (حسب سكربت `hl.sh` عندك).

الخادم في الحزمة يستخدم `gearbox/dlls/opfor.so` الأصلي، والعميل هو BugfixedHL المبني.

## الرخص

- **BugfixedHL:** GPL-3.0. المصدر: [tmp64/BugfixedHL-Rebased](https://github.com/tmp64/BugfixedHL-Rebased).
- **أسلحة OP4:** رخصة Valve للـHalf-Life 1 SDK. توزيع مجاني فقط، والتجاري يحتاج إذناً من Valve. المصدر: [twhl-community/halflife-op4-updated](https://github.com/twhl-community/halflife-op4-updated).
- **أدوات الدمج والشِيمز:** MIT.

الحزمة تحتوي على مجلد `LICENSES/` بهذه النصوص، وملف `NOTICE.txt` يشرح مصدر كل جزء.
الحزمة لا تحتوي على أصول Valve (نماذج وأصوات وخرائط)، ويجب أن تملك اللعبة الأصلية.

## البناء من المصدر (Linux)

```bash
make fetch                                   # يجلب BugfixedHL وOP4 updated وValve SDK
git clone https://github.com/tmp64/hl1_source_sdk .cache/upstreams/hl1_source_sdk
git -C .cache/upstreams/hl1_source_sdk checkout 11f2665
python3 -m venv /tmp/zenv && /tmp/zenv/bin/pip install cmake==3.30.9 ziglang==0.17.1 PyYAML==6.0.3
/tmp/zenv/bin/python tools/build_bhl_base.py --out scratch/bhl-out
```

النتيجة: `client.so` (ELF32، يحتاج GLIBC 2.17 كحد أقصى)، ويُبنى بتحسين `-O2` بدون فحوص Zig.

## ما لم يُنجز بعد

1. **اسم المود:** لم يُحسم بعد. الاسم الحالي `bhlop4` مؤقت، وأي تغيير يتطلب تغيير المجلد وملف الترجمة والكود.
2. **شعار وعلامة:** لا نستخدم شعار Lambda ولا اسم Half-Life في الاسم أو الشعار (علامات تجارية لـValve).
3. **ترخيص الصور الصغيرة:** `sprites/ag_ctf.spr` و`ag_ctf_score.spr` من كود Adrenaline Gamer، ولم أجد ترخيصهما بعد. وهي لا تُستخدم في مود السباق.
4. **Windows:** لا يوجد ملف `client.dll` حديث. مصدر Windows الموجود مبني من شجرة OP4 القديمة، وليس من BHL الحالي.
5. **المود داخل اللعبة:** الاختبارات التي أبلغ عنها المستخدم محدودة. ما زالت هناك اختبارات لم تُنفَّذ: الموسيقى، وكل خريطة في الحملة، وكل سلاح مع الذخيرة.

## الوثائق

- [`docs/LICENSES.md`](docs/LICENSES.md) — تفاصيل الرخص.
- [`docs/BUILDING.md`](docs/BUILDING.md) — البناء.
- [`docs/UPSTREAMS.md`](docs/UPSTREAMS.md) — المصادر المثبتة.
- [`docs/LEGACY.md`](docs/LEGACY.md) — التوثيق القديم (مرحلة OP4 الأساس)، لا يعكس الحالة الحالية.

## المساهمة

انظر [CONTRIBUTING.md](CONTRIBUTING.md).
