import os
import subprocess

locales_base = os.path.join(os.path.dirname(os.path.abspath(__file__)))

for lang in ['en_US', 'zh_CN', 'zh_Hant']:
    po_file = os.path.join(locales_base, lang, 'LC_MESSAGES', 'django.po')
    mo_file = os.path.join(locales_base, lang, 'LC_MESSAGES', 'django.mo')
    
    if os.path.exists(po_file):
        try:
            # 尝试使用 msgfmt 命令
            subprocess.run(['msgfmt', po_file, '-o', mo_file], check=True)
            print(f"Compiled {lang} successfully")
        except FileNotFoundError:
            # 如果没有 msgfmt，使用 polib 库
            import polib
            po = polib.pofile(po_file)
            po.save_as_mofile(mo_file)
            print(f"Compiled {lang} using polib")
