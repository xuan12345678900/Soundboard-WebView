import os
import subprocess
import shutil
import sys

# ====== PATHS ======
SDK_DIR = r"C:\Users\ASUS\AppData\Local\Android\Sdk"
JAVA_DIR = r"C:\Program Files\Java\jdk-21\bin"
PROJECT_DIR = r"C:\Users\ASUS\Desktop\SoundPlayerAndroid"
APP_DIR = os.path.join(PROJECT_DIR, "app", "src", "main")
BUILD_DIR = os.path.join(PROJECT_DIR, "build")
OUTPUT_APK = os.path.join(PROJECT_DIR, "音效播放器.apk")

# SDK tools
BUILD_TOOLS_DIR = os.path.join(SDK_DIR, "build-tools", "35.0.0")
PLATFORM_DIR = os.path.join(SDK_DIR, "platforms", "android-34")
AAPT = os.path.join(BUILD_TOOLS_DIR, "aapt.exe")
D8 = os.path.join(BUILD_TOOLS_DIR, "d8.bat")
ZIPALIGN = os.path.join(BUILD_TOOLS_DIR, "zipalign.exe")
APKSIGNER = os.path.join(BUILD_TOOLS_DIR, "apksigner.bat")
ANDROID_JAR = os.path.join(PLATFORM_DIR, "android.jar")

JAVAC = os.path.join(JAVA_DIR, "javac.exe")
JAVA = os.path.join(JAVA_DIR, "java.exe")
KEYTOOL = os.path.join(JAVA_DIR, "keytool.exe")

def run(cmd, **kwargs):
    print(f"\n$ {' '.join(cmd[:3])}{' ...' if len(cmd)>3 else ''}")
    result = subprocess.run(cmd, capture_output=True, **kwargs)
    if result.returncode != 0:
        stdout_str = result.stdout.decode('utf-8', errors='replace') if result.stdout else ''
        stderr_str = result.stderr.decode('utf-8', errors='replace') if result.stderr else ''
        print(f"STDOUT: {stdout_str[-2000:]}")
        print(f"STDERR: {stderr_str[-2000:]}")
        raise Exception(f"Command failed with code {result.returncode}: {cmd[0]}")
    return result

def main():
    # Clean build dir
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(os.path.join(BUILD_DIR, "gen"), exist_ok=True)
    os.makedirs(os.path.join(BUILD_DIR, "obj"), exist_ok=True)
    os.makedirs(os.path.join(BUILD_DIR, "dex"), exist_ok=True)

    # Step 1: Generate R.java with aapt
    print("=" * 60)
    print("Step 1: Generate R.java")
    print("=" * 60)
    run([
        AAPT, "package", "-f", "-m",
        "-J", os.path.join(BUILD_DIR, "gen"),
        "-S", os.path.join(APP_DIR, "res"),
        "-M", os.path.join(APP_DIR, "AndroidManifest.xml"),
        "-I", ANDROID_JAR,
        "--auto-add-overlay"
    ])
    print("OK")

    # Step 2: Compile Java sources
    print("\n" + "=" * 60)
    print("Step 2: Compile Java")
    print("=" * 60)
    
    # Collect all Java files
    java_files = []
    for root, dirs, files in os.walk(os.path.join(APP_DIR, "java")):
        for f in files:
            if f.endswith(".java"):
                java_files.append(os.path.join(root, f))
    for root, dirs, files in os.walk(os.path.join(BUILD_DIR, "gen")):
        for f in files:
            if f.endswith(".java"):
                java_files.append(os.path.join(root, f))
    
    print(f"Compiling {len(java_files)} Java files...")
    
    javac_cmd = [
        JAVAC,
        "-d", os.path.join(BUILD_DIR, "obj"),
        "-classpath", ANDROID_JAR,
        "-sourcepath", os.path.join(APP_DIR, "java"),
        "-source", "11",
        "-target", "11",
        "-encoding", "UTF-8",
    ] + java_files
    
    run(javac_cmd)
    print("OK")

    # Step 3: Convert to DEX with d8
    print("\n" + "=" * 60)
    print("Step 3: Convert to DEX")
    print("=" * 60)
    
    # Collect all .class files
    class_files = []
    obj_dir = os.path.join(BUILD_DIR, "obj")
    for root, dirs, files in os.walk(obj_dir):
        for f in files:
            if f.endswith(".class"):
                class_files.append(os.path.join(root, f))
    
    print(f"Converting {len(class_files)} class files to DEX...")
    
    d8_cmd = [
        D8,
        "--output", os.path.join(BUILD_DIR, "dex"),
        "--lib", ANDROID_JAR,
        "--min-api", "21",
    ] + class_files
    
    run(d8_cmd, cwd=BUILD_DIR)
    print("OK")

    # Step 4: Package APK with aapt (including assets)
    print("\n" + "=" * 60)
    print("Step 4: Package APK")
    print("=" * 60)
    
    unsigned_apk = os.path.join(BUILD_DIR, "app-unsigned.apk")
    
    aapt_cmd = [
        AAPT, "package", "-f",
        "-S", os.path.join(APP_DIR, "res"),
        "-M", os.path.join(APP_DIR, "AndroidManifest.xml"),
        "-I", ANDROID_JAR,
        "-A", os.path.join(APP_DIR, "assets"),
        "-F", unsigned_apk,
        "--auto-add-overlay"
    ]
    
    run(aapt_cmd)
    
    # Add DEX to APK
    print("Adding classes.dex to APK...")
    dex_dir = os.path.join(BUILD_DIR, "dex")
    dex_file = "classes.dex"
    
    # Use aapt add with relative path so the entry name is correct
    run([AAPT, "add", "-f", unsigned_apk, dex_file], cwd=dex_dir)
    print("OK")

    # Step 5: Zipalign
    print("\n" + "=" * 60)
    print("Step 5: Zipalign")
    print("=" * 60)
    
    aligned_apk = os.path.join(BUILD_DIR, "app-aligned.apk")
    if os.path.exists(aligned_apk):
        os.remove(aligned_apk)
    
    run([ZIPALIGN, "-f", "-p", "4", unsigned_apk, aligned_apk])
    print("OK")

    # Step 6: Sign APK
    print("\n" + "=" * 60)
    print("Step 6: Sign APK")
    print("=" * 60)
    
    keystore = os.path.join(BUILD_DIR, "debug.keystore")
    
    # Generate debug keystore if not exists
    if not os.path.exists(keystore):
        print("Generating debug keystore...")
        run([
            KEYTOOL, "-genkey", "-v",
            "-keystore", keystore,
            "-alias", "androiddebugkey",
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", "10000",
            "-storepass", "android",
            "-keypass", "android",
            "-dname", "CN=Android Debug,O=Android,C=US"
        ])
    
    signed_apk = OUTPUT_APK
    if os.path.exists(signed_apk):
        os.remove(signed_apk)
    
    run([
        APKSIGNER, "sign",
        "--ks", keystore,
        "--ks-key-alias", "androiddebugkey",
        "--ks-pass", "pass:android",
        "--key-pass", "pass:android",
        "--out", signed_apk,
        aligned_apk
    ])
    
    # Verify
    result = run([APKSIGNER, "verify", "--verbose", signed_apk])
    print(result.stdout[:500])
    
    file_size = os.path.getsize(signed_apk)
    print(f"\n{'=' * 60}")
    print(f"APK built successfully!")
    print(f"Output: {signed_apk}")
    print(f"Size: {file_size / 1024 / 1024:.2f} MB")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nBUILD FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
