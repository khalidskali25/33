#!/usr/bin/env python3
"""
بناء النسخة العامة من مواكبة (دون جسر مسار).

الاستعمال:
    python3 tools/build_public.py  <مجلد المستودع الخاص>  <مجلد المستودع العام>

- ينسخ index.html و sw.js و version.json و manifest.webmanifest و icons/ و README.md و .nojekyll
- يحذف من index.html كل ما بين العلامتين /*@MASSAR{*/ و /*}@MASSAR*/
- يحذف عناصر الجسر داخل تبويب «المجموع الشهري» (زر النسخ وخانة الرمز) ويعوض الإرشاد بإرشاد للإدخال اليدوي
- يتوقف فورا إذا لم يجد أي موضع متوقع، أو إذا بقي أي أثر للجسر في الناتج
"""
import os
import re
import shutil
import sys

START, END = '/*@MASSAR{*/', '/*}@MASSAR*/'

# تعويضات دقيقة داخل تبويب المجموع الشهري: (النص الأصلي، النص البديل)
REPLACEMENTS = [
    (",code=msmCode(rgC,ym,c)", ""),
    ("<button class=\"btn sm\" style=\"background:#1B4332\" onclick=\"msrCopy($('#msmT').value)\">نسخ رمز النقل نحو مسار</button>", ""),
    (" <textarea id=\"msmT\" readonly dir=\"ltr\" style=\"width:100%;min-height:60px;font:12px monospace\">${esc(code)}</textarea>\n", ""),
    ("، ثم زر «مسار» ← «لصق» ← «تأشير»، فتُملأ خانات الأيام والساعات. راجع ثم اضغط «حفظ» في مسار بنفسك. الخانات التي قيمتها 0 تبقى كما هي.",
     "، ثم أدخل قيم الأيام وعدد الساعات يدويا انطلاقا من هذا الجدول أو من نسخته المطبوعة، واضغط «حفظ» في مسار."),
]

# أي أثر من هذه الآثار في الناتج = فشل البناء
LEAKS = re.compile(r'MSR_|msr[A-Z]|msmCode|msmT\b|jisr|JM1|JM2|@MASSAR|رمز النقل|شيفرة الزر|زر «مسار»|نحو مسار|جسر')

COPY = ['sw.js', 'version.json', 'manifest.webmanifest', 'README.md', '.nojekyll']


def strip(html: str) -> str:
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
    if n == 0:
        sys.exit('خطأ: لم يُعثر على أي كتلة @MASSAR')
    html = ''.join(out)
    for old, new in REPLACEMENTS:
        if html.count(old) != 1:
            sys.exit('خطأ: الموضع غير موجود أو مكرر: ' + old[:60])
        html = html.replace(old, new)
    print(f'✓ حُذفت {n} كتل و{len(REPLACEMENTS)} عناصر من تبويب المجموع الشهري')
    return html


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    html = strip(open(os.path.join(src, 'index.html'), encoding='utf-8').read())
    leaks = sorted(set(m.group(0) for m in LEAKS.finditer(html)))
    if leaks:
        sys.exit('⛔ بقيت آثار للجسر: ' + ', '.join(leaks))
    open(os.path.join(dst, 'index.html'), 'w', encoding='utf-8').write(html)
    for f in COPY:
        if os.path.exists(os.path.join(src, f)):
            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
    if os.path.isdir(os.path.join(src, 'icons')):
        shutil.copytree(os.path.join(src, 'icons'), os.path.join(dst, 'icons'), dirs_exist_ok=True)
    print('✓ لا أثر للجسر في النسخة العامة')


if __name__ == '__main__':
    main()
