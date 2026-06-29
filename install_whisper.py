#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Автоматическая установка Whisper на Windows.
Устанавливает WinGet, если отсутствует, затем через него ставит Python, FFmpeg, Git,
далее Whisper через pip и опционально PyTorch с CUDA.
Запускать от имени администратора!
Вывод всех команд показывается в реальном времени.
"""

import sys
import os
import subprocess
import shutil
import time
import ctypes
import winreg

# ----------------------------------------------------------------------
# Проверка прав администратора
# ----------------------------------------------------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("❌ Скрипт должен быть запущен от имени администратора.")
    print("   Перезапустите командную строку или PowerShell от имени администратора и выполните:")
    print(f"   python {sys.argv[0]}")
    sys.exit(1)

# ----------------------------------------------------------------------
# Функция запуска команд с прямым выводом в консоль
# ----------------------------------------------------------------------
def run_cmd_live(cmd, check=True):
    """Запускает команду, передавая stdout/stderr в консоль в реальном времени."""
    print(f"\n▶ {cmd}")
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    # Читаем построчно и выводим
    for line in process.stdout:
        print(line, end='')
    process.wait()
    if check and process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)
    return process.returncode

def is_tool_available(name):
    return shutil.which(name) is not None

def update_env_path():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 0, winreg.KEY_READ)
        system_path = winreg.QueryValueEx(key, 'Path')[0]
        winreg.CloseKey(key)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_READ)
        user_path = winreg.QueryValueEx(key, 'Path')[0]
        winreg.CloseKey(key)
        os.environ['PATH'] = system_path + ';' + user_path + ';' + os.environ.get('PATH', '')
    except Exception as e:
        print(f"⚠️  Не удалось обновить PATH: {e}")

# ----------------------------------------------------------------------
# Установка WinGet, если отсутствует
# ----------------------------------------------------------------------
def install_winget():
    print("⬇️  WinGet не найден. Установка через PowerShell...")
    ps_script = """
$progressPreference = 'silentlyContinue'
Write-Host "Installing WinGet PowerShell module from PSGallery..."
Install-PackageProvider -Name NuGet -Force | Out-Null
Install-Module -Name Microsoft.WinGet.Client -Force -Repository PSGallery | Out-Null
Write-Host "Using Repair-WinGetPackageManager cmdlet to bootstrap WinGet..."
Repair-WinGetPackageManager -AllUsers
Write-Host "Done."
"""
    try:
        cmd = f'powershell -Command "{ps_script}"'
        run_cmd_live(cmd, check=False)
        update_env_path()
        time.sleep(2)
        if is_tool_available('winget'):
            print("✅ WinGet успешно установлен.")
            return True
        else:
            print("❌ Winget не обнаружен после установки. Возможно, требуется перезагрузка.")
            return False
    except Exception as e:
        print(f"❌ Ошибка при установке WinGet: {e}")
        return False

# ----------------------------------------------------------------------
# 1. Проверка WinGet
# ----------------------------------------------------------------------
print("\n🔍 Проверка WinGet...")
if not is_tool_available('winget'):
    if not install_winget():
        print("❌ Не удалось установить WinGet. Установите вручную через Microsoft Store (App Installer).")
        sys.exit(1)
else:
    print(f"✅ WinGet найден: {shutil.which('winget')}")

# ----------------------------------------------------------------------
# 2. Проверка / установка Python
# ----------------------------------------------------------------------
print("\n🔍 Проверка Python...")
if is_tool_available('python'):
    print(f"✅ Python найден: {shutil.which('python')}")
else:
    print("⬇️  Python не найден. Установка через winget...")
    try:
        run_cmd_live('winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements')
        update_env_path()
        time.sleep(2)
        if is_tool_available('python'):
            print("✅ Python успешно установлен.")
        else:
            print("❌ Python установлен, но не обнаружен в PATH. Перезагрузите систему и запустите скрипт снова.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка установки Python: {e}")
        print("   Установите Python вручную с https://www.python.org/downloads/windows/ (не забудьте галочку 'Add Python to PATH').")
        sys.exit(1)

# ----------------------------------------------------------------------
# 3. Проверка / установка FFmpeg
# ----------------------------------------------------------------------
print("\n🔍 Проверка FFmpeg...")
if is_tool_available('ffmpeg'):
    print(f"✅ FFmpeg найден: {shutil.which('ffmpeg')}")
else:
    print("⬇️  FFmpeg не найден. Установка через winget...")
    try:
        run_cmd_live('winget install ffmpeg --silent --accept-package-agreements --accept-source-agreements')
        update_env_path()
        time.sleep(2)
        if is_tool_available('ffmpeg'):
            print("✅ FFmpeg успешно установлен.")
        else:
            print("❌ FFmpeg установлен, но не обнаружен в PATH. Перезагрузите систему.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка установки FFmpeg: {e}")
        print("   Установите FFmpeg вручную с https://www.gyan.dev/ffmpeg/builds/ и добавьте папку bin в PATH.")
        sys.exit(1)

# ----------------------------------------------------------------------
# 4. Проверка / установка Git
# ----------------------------------------------------------------------
print("\n🔍 Проверка Git...")
if is_tool_available('git'):
    print(f"✅ Git найден: {shutil.which('git')}")
else:
    print("⬇️  Git не найден. Установка через winget...")
    try:
        run_cmd_live('winget install Git.Git --silent --accept-package-agreements --accept-source-agreements')
        update_env_path()
        time.sleep(2)
        if is_tool_available('git'):
            print("✅ Git успешно установлен.")
        else:
            print("❌ Git установлен, но не обнаружен в PATH. Перезагрузите систему.")
            sys.exit(1)
    except Exception as e:
        print(f"⚠️  Не удалось установить Git: {e}")
        print("   Установите Git вручную с https://git-scm.com/download/win")
        # Не выходим, но предупреждаем

# ----------------------------------------------------------------------
# 5. Установка Whisper через pip
# ----------------------------------------------------------------------
print("\n📦 Установка Whisper через pip...")
try:
    run_cmd_live('python -m pip install --upgrade pip', check=False)
    run_cmd_live('pip install git+https://github.com/openai/whisper.git')
    print("✅ Whisper успешно установлен.")
except Exception as e:
    print(f"❌ Ошибка при установке Whisper: {e}")
    print("   Проверьте интернет-соединение и наличие Git.")
    sys.exit(1)

# ----------------------------------------------------------------------
# 6. Опционально: PyTorch с CUDA
# ----------------------------------------------------------------------
print("\n💡 Хотите установить PyTorch с поддержкой GPU (CUDA 11.8) для ускорения? (y/n)")
choice = input().strip().lower()
if choice == 'y':
    print("⬇️  Установка PyTorch с CUDA...")
    try:
        run_cmd_live('pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118')
        print("✅ PyTorch с CUDA успешно установлен.")
    except Exception as e:
        print(f"❌ Ошибка при установке PyTorch: {e}")
        print("   Возможно, ваша видеокарта не поддерживает CUDA 11.8 или драйверы устарели.")
else:
    print("⏭️  Установка PyTorch с GPU пропущена.")

print("\n✅ Установка завершена! Перезапустите командную строку или PowerShell, чтобы изменения PATH вступили в силу.")
print("   Проверьте работу Whisper: whisper --help")