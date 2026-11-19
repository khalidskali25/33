#!/usr/bin/env python3
"""
بناء النسخة العامة «تطبيق مواكبة G» (دون جسر مسار).

الاستعمال:
    python3 tools/build_public.py  <مجلد المستودع الخاص>  <مجلد المستودع العام>

- ينسخ index.html و sw.js و version.json و manifest.webmanifest و icons/ و README.md و .nojekyll
- يحذف من index.html كل ما بين العلامتين /*@MASSAR{*/ و /*}@MASSAR*/
- يحذف عناصر الجسر داخل تبويب «المجموع الشهري» (زر النسخ وخانة الرمز) ويعوض الإرشاد بإرشاد للإدخال اليدوي
- يغير الاسم الظاهر إلى «تطبيق مواكبة G» (دون المس بمفاتيح التخزين ولا بمجلد Drive)
- يتوقف فورا إذا لم يجد أي موضع متوقع، أو إذا بقي أي أثر للجسر في الناتج
"""
import os
import re
import shutil
import sys

START, END = '/*@MASSAR{*/', '/*}@MASSAR*/'
PRIV_START, PRIV_END = '/*@PRIVATE{*/', '/*}@PRIVATE*/'   # اللون الافتراضي للنسخة الخاصة (برتقالي)

# 1) عناصر الجسر داخل تبويب المجموع الشهري — (الأصل، البديل، العدد المتوقع)
BRIDGE_REPLACEMENTS = [
    (",code=msmCode(rgC,ym,c)", "", 1),
    ("<button class=\"btn sm\" style=\"background:#1B4332\" onclick=\"msrCopy($('#msmT').value)\">نسخ رمز النقل نحو مسار</button>", "", 1),
    (" <textarea id=\"msmT\" readonly dir=\"ltr\" style=\"width:100%;min-height:60px;font:12px monospace\">${esc(code)}</textarea>\n", "", 1),
    ("، ثم زر «مسار» ← «لصق» ← «تأشير»، فتُملأ خانات الأيام والساعات. راجع ثم اضغط «حفظ» في مسار بنفسك. الخانات التي قيمتها 0 تبقى كما هي.",
     "، ثم أدخل قيم الأيام وعدد الساعات يدويا انطلاقا من هذا الجدول أو من نسخته المطبوعة، واضغط «حفظ» في مسار.", 1),
]

# 2) الاسم الظاهر للنسخة العامة — لا يُمس مجلد Drive (مواكبة_الحراسة_العامة) ولا مفاتيح التخزين
PUBLIC_NAME = 'تطبيق مواكبة G'
NAME_REPLACEMENTS = [
    ('تطبيق مواكبة', PUBLIC_NAME, 4),                 # العنوان، الشريط العلوي، شاشة التشغيل، «عن التطبيق»…
    ("'رخصة مواكبة':'تفعيل مواكبة'", "'رخصة مواكبة G':'تفعيل مواكبة G'", 1),
    ('*طلب رخصة تفعيل مواكبة*', '*طلب رخصة تفعيل مواكبة G*', 1),
    ('# طلب رخصة تفعيل — مواكبة\\n', '# طلب رخصة تفعيل — مواكبة G\\n', 1),
    ("'طلب-رخصة-مواكبة-'", "'طلب-رخصة-مواكبة-G-'", 1),
    ("title:'طلب رخصة مواكبة',text:'طلب رخصة تفعيل مواكبة —", "title:'طلب رخصة مواكبة G',text:'طلب رخصة تفعيل مواكبة G —", 1),
    ("'✓ تم تفعيل مواكبة'", "'✓ تم تفعيل مواكبة G'", 1),
    ('<div class="om-mark">مواكبة ·', '<div class="om-mark">مواكبة G ·', 2),   # الأوراق المقروءة آليا
]
MANIFEST_REPLACEMENTS = [
    ('"theme_color": "#C2410C"', '"theme_color": "#1B4332"', 1),
    ('"name": "مواكبة — فضاء الحراسة العامة"', '"name": "' + PUBLIC_NAME + ' — فضاء الحراسة العامة"', 1),
    ('"short_name": "مواكبة"', '"short_name": "مواكبة G"', 1),
]
README_REPLACEMENTS = [
    ('# مواكبة — فضاء الحراسة العامة', '# ' + PUBLIC_NAME + ' — فضاء الحراسة العامة', 1),
]

# أي أثر من هذه الآثار في الناتج = فشل البناء
LEAKS = re.compile(r'@PRIVATE|MKB_THEME_DEF=|MSR_|msr[A-Z]|msmCode|msmT\b|jisr|JM1|JM2|@MASSAR|رمز النقل|شيفرة الزر|زر «مسار»|نحو مسار|جسر')

COPY = ['sw.js', 'version.json', 'manifest.webmanifest', 'README.md', '.nojekyll']


def apply(text, rules, where):
    """rules: (الأصل، البديل، العدد). العدد = عدد المواضع المطلوب بالضبط، أو الحد الأدنى لقاعدة الاسم العامة."""
    for old, new, expected in rules:
        c = text.count(old)
        ok = c >= expected if old == 'تطبيق مواكبة' else c == expected
        if not ok:
            sys.exit(f'خطأ ({where}): وُجد {c} موضع بدل {expected}: ' + old[:60])
        text = text.replace(old, new)
    return text


def strip_blocks(html, START=START, END=END, need=True):
    out, pos, n = [], 0, 0
    while True:
        a = html.find(START, pos)
        if a < 0:
            break
        b = html.find(END, a)
        if b < 0:
            sys.exit('خطأ: علامة بداية دون علامة نهاية')
        out.append(html[pos:a])
        pos = b + len(END)
        if html[pos:pos + 1] == '\n':
            pos += 1
        n += 1
    out.append(html[pos:])
    if n == 0 and need:
        sys.exit('خطأ: لم يُعثر على أي كتلة ' + START)
    return ''.join(out), n


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]

    html, n = strip_blocks(open(os.path.join(src, 'index.html'), encoding='utf-8').read())
    html, np = strip_blocks(html, PRIV_START, PRIV_END)
    html = apply(html, [('<meta name="theme-color" content="#C2410C">', '<meta name="theme-color" content="#1B4332">', 1)], 'index.html')
    print(f'✓ اللون الافتراضي: الأخضر ({np} كتلة خاصة محذوفة)')
    html = apply(html, BRIDGE_REPLACEMENTS, 'index.html')
    print(f'✓ حُذفت {n} كتل و{len(BRIDGE_REPLACEMENTS)} عناصر من تبويب المجموع الشهري')
    html = apply(html, NAME_REPLACEMENTS, 'index.html')
    print('✓ الاسم: ' + PUBLIC_NAME)

    leaks = sorted(set(m.group(0) for m in LEAKS.finditer(html)))
    if leaks:
        sys.exit('⛔ بقيت آثار للجسر: ' + ', '.join(leaks))
    open(os.path.join(dst, 'index.html'), 'w', encoding='utf-8').write(html)

    for f in COPY:
        if os.path.exists(os.path.join(src, f)):
            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
    if os.path.isdir(os.path.join(src, 'icons')):
        shutil.copytree(os.path.join(src, 'icons'), os.path.join(dst, 'icons'), dirs_exist_ok=True)
    # النسخة العامة تحتفظ بالأيقونات الخضراء (أيقونات `icons/` في المستودع الخاص برتقالية)
    green = os.path.join(src, 'tools', 'icons-green')
    if not os.path.isdir(green):
        sys.exit('خطأ: مجلد الأيقونات الخضراء tools/icons-green غير موجود')
    shutil.copytree(green, os.path.join(dst, 'icons'), dirs_exist_ok=True)
    for f, rules in (('manifest.webmanifest', MANIFEST_REPLACEMENTS), ('README.md', README_REPLACEMENTS)):
        p = os.path.join(dst, f)
        with open(p, encoding='utf-8') as fh:
            text = apply(fh.read(), rules, f)
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write(text)
    print('✓ لا أثر للجسر في النسخة العامة')


if __name__ == '__main__':
    main()
