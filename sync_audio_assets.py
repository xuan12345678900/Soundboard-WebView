import os
import re
import shutil

SRC_DIR = r"C:\Users\ASUS\Desktop\音频及文件夹分类"
ASSETS_DIR = r"C:\Users\ASUS\Desktop\SoundPlayerAndroid\app\src\main\assets"
AUDIO_DIR = os.path.join(ASSETS_DIR, "audio")
HTML_PATH = os.path.join(ASSETS_DIR, "index.html")

AUDIO_EXTS = ('.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac')

CAT_ORDER = [
    ("otto", "cat_otto"),
    ("其他", "cat_other"),
    ("咕咕嘎嘎", "cat_gugu"),
    ("大狗", "cat_dog"),
    ("无畏契约", "cat_valorant"),
    ("终末地", "cat_zmd"),
    ("老牧师", "cat_priest"),
    ("饿", "cat_e"),
]

def js_str(s):
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'") + "'"

def main():
    if not os.path.isdir(SRC_DIR):
        print("SOURCE DIR NOT FOUND: " + SRC_DIR)
        return

    if os.path.isdir(AUDIO_DIR):
        shutil.rmtree(AUDIO_DIR)
    os.makedirs(AUDIO_DIR)

    sounds_js = []
    cats_js = []
    idx = 0
    total_size = 0

    for order, (folder, cat_id) in enumerate(CAT_ORDER):
        folder_path = os.path.join(SRC_DIR, folder)
        if not os.path.isdir(folder_path):
            print("SKIP MISSING FOLDER: " + folder)
            continue
        cats_js.append("        { id: '%s', name: %s, order: %d }" % (cat_id, js_str(folder), order))

        files = sorted(os.listdir(folder_path))
        files = [f for f in files if os.path.splitext(f)[1].lower() in AUDIO_EXTS]
        for f in files:
            src = os.path.join(folder_path, f)
            ext = os.path.splitext(f)[1].lower()
            name = os.path.splitext(f)[0]
            dst_name = "audio_%03d%s" % (idx, ext)
            dst = os.path.join(AUDIO_DIR, dst_name)
            shutil.copy2(src, dst)
            size = os.path.getsize(dst)
            total_size += size
            sounds_js.append(
                "        { id: 'builtin_%03d', name: %s, cat: '%s', file: 'audio/%s', size: %d, builtin: true }"
                % (idx, js_str(name), cat_id, dst_name, size)
            )
            idx += 1

    print("Copied %d audio files, total %.2f MB" % (idx, total_size / 1024 / 1024))

    with open(HTML_PATH, "r", encoding="utf-8") as fp:
        html = fp.read()

    new_builtin = "    var BUILTIN_SOUNDS = [\n" + ",\n".join(sounds_js) + "\n    ];"
    new_cats = "    var DEFAULT_CATEGORIES = [\n" + ",\n".join(cats_js) + "\n    ];"

    html, n1 = re.subn(
        r"    var BUILTIN_SOUNDS = \[.*?\];",
        lambda m: new_builtin,
        html,
        count=1,
        flags=re.S,
    )
    html, n2 = re.subn(
        r"    var DEFAULT_CATEGORIES = \[.*?\];",
        lambda m: new_cats,
        html,
        count=1,
        flags=re.S,
    )

    if n1 != 1 or n2 != 1:
        print("PATCH FAILED: BUILTIN=%d CATS=%d" % (n1, n2))
        return

    with open(HTML_PATH, "w", encoding="utf-8") as fp:
        fp.write(html)

    print("index.html updated: BUILTIN_SOUNDS(%d entries) DEFAULT_CATEGORIES(%d entries)" % (len(sounds_js), len(cats_js)))

if __name__ == "__main__":
    main()
