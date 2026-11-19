#!/usr/bin/env python3
"""
نشر النسخة الخاصة كتطبيق PWA مشفّر بكلمة سر (للاستضافة في مستودع عام على GitHub Pages).

الاستعمال:
    MKB_PASS='كلمة السر' python3 tools/build_private_pwa.py  <المستودع الخاص>  <مجلد مستودع النشر>

- يشفّر index.html كاملا بـ AES-256-GCM، والمفتاح مشتق من كلمة السر بـ PBKDF2-SHA256 (600000 دورة).
- لا يبقى في مستودع النشر أي نص مقروء من شيفرة التطبيق: فقط صفحة إدخال كلمة السر والمحتوى المشفّر.
- ينسخ sw.js و version.json و manifest.webmanifest و icons/ حتى يعمل التطبيق كـ PWA ودون اتصال.
- كلمة السر لا تُكتب في أي ملف، وتُقرأ من متغير البيئة MKB_PASS فقط.
"""
import base64
import json
import os
import re
import shutil
import sys

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITER = 600000

SHELL = r'''<!DOCTYPE html>
<html lang="ar" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#C2410C"><meta name="robots" content="noindex,nofollow">
<link rel="manifest" href="manifest.webmanifest"><link rel="icon" href="icons/icon-192.png">
<title>مواكبة</title>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#FBF8F2;font-family:Arial,Tahoma,sans-serif;color:#1d1d1d}
.box{width:min(92vw,380px);background:#fff;border:1px solid #D9CDB5;border-top:6px solid #C2410C;border-radius:12px;padding:22px 20px;box-shadow:0 6px 24px #0002;text-align:center}
h1{margin:0 0 4px;font-size:22px;color:#C2410C}p{margin:0 0 14px;color:#595959;font-size:14px}
input[type=password]{width:100%;box-sizing:border-box;padding:12px;font-size:17px;border:1px solid #bbb;border-radius:8px;text-align:center}
label{display:flex;gap:8px;align-items:center;justify-content:center;margin:12px 0;font-size:14px;color:#333}
button{width:100%;padding:12px;font-size:17px;border:0;border-radius:8px;background:#C2410C;color:#fff;font-weight:bold}
#msg{min-height:20px;margin-top:10px;font-size:14px;color:#9B2226}
</style></head><body>
<div class="box" id="box"><h1>مواكبة</h1><p>النسخة الخاصة — أدخل كلمة السر</p>
<form id="f"><input type="password" id="pw" autocomplete="current-password" placeholder="كلمة السر" autofocus>
<label><input type="checkbox" id="rm" checked> تذكّر كلمة السر في هذا الجهاز</label>
<button type="submit">فتح التطبيق</button></form><div id="msg"></div></div>
<script>
const P=__PAYLOAD__;
const d64=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
const e64=a=>{let s='';for(let i=0;i<a.length;i+=8192)s+=String.fromCharCode.apply(null,a.subarray(i,i+8192));return btoa(s);};
async function keyFrom(pw){const base=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
 return crypto.subtle.deriveKey({name:'PBKDF2',salt:d64(P.salt),iterations:P.iter,hash:'SHA-256'},base,{name:'AES-GCM',length:256},true,['decrypt']);}
async function openWith(key,remember){const plain=await crypto.subtle.decrypt({name:'AES-GCM',iv:d64(P.iv)},key,d64(P.ct));
 if(remember){try{localStorage.setItem('mkb_pwa_k',P.salt+'.'+e64(new Uint8Array(await crypto.subtle.exportKey('raw',key))));}catch(e){}}
 const html=new TextDecoder().decode(plain);document.open();document.write(html);document.close();}
async function auto(){try{const s=localStorage.getItem('mkb_pwa_k')||'';const [salt,k]=s.split('.');if(!k||salt!==P.salt)return;
 const key=await crypto.subtle.importKey('raw',d64(k),{name:'AES-GCM'},false,['decrypt']);await openWith(key,false);}catch(e){try{localStorage.removeItem('mkb_pwa_k');}catch(_){}}}
document.getElementById('f').onsubmit=async ev=>{ev.preventDefault();const m=document.getElementById('msg');m.style.color='#595959';m.textContent='جارٍ الفتح…';
 try{await openWith(await keyFrom(document.getElementById('pw').value),document.getElementById('rm').checked);}catch(e){m.style.color='#9B2226';m.textContent='كلمة السر غير صحيحة';}};
auto();
</script></body></html>
'''

COPY = ['sw.js', 'version.json', 'manifest.webmanifest', '.nojekyll']


def main():
    if len(sys.argv) != 3 or not os.environ.get('MKB_PASS'):
        sys.exit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    pw = os.environ['MKB_PASS'].encode('utf-8')
    if len(pw) < 8:
        sys.exit('كلمة السر قصيرة: 8 أحرف على الأقل')
    html = open(os.path.join(src, 'index.html'), 'rb').read()
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(pw)
    ct = AESGCM(key).encrypt(iv, html, None)
    b = lambda x: base64.b64encode(x).decode()
    payload = json.dumps({'v': 1, 'iter': ITER, 'salt': b(salt), 'iv': b(iv), 'ct': b(ct)})
    open(os.path.join(dst, 'index.html'), 'w', encoding='utf-8').write(SHELL.replace('__PAYLOAD__', payload))
    for f in COPY:
        if os.path.exists(os.path.join(src, f)):
            shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
    if not os.path.exists(os.path.join(dst, '.nojekyll')):
        open(os.path.join(dst, '.nojekyll'), 'w').close()
    shutil.copytree(os.path.join(src, 'icons'), os.path.join(dst, 'icons'), dirs_exist_ok=True)
    open(os.path.join(dst, 'robots.txt'), 'w').write('User-agent: *\nDisallow: /\n')
    # تحقق: لا نص مقروء من شيفرة التطبيق في الصفحة المنشورة
    out = open(os.path.join(dst, 'index.html'), encoding='utf-8').read()
    for probe in ('MSR_', 'licDlg', 'APP_VERSION', 'function go('):
        if probe in out:
            sys.exit('⛔ نص مقروء من التطبيق في الصفحة المنشورة: ' + probe)
    print(f'✓ نسخة خاصة مشفّرة: {len(html)//1024} ك.ب ← {len(out)//1024} ك.ب، دون أي نص مقروء من الشيفرة')


if __name__ == '__main__':
    main()
