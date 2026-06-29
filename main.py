import whisper
import argparse
import os
import sys
from pathlib import Path

def print_banner():
    """Выводит ASCII-баннер"""
    banner = [
        r" __        ___     _                    _____                              _ _               ",
        r" \ \      / / |__ (_)___ _ __   ___ _ _|_   _| __ __ _ _ __  ___  ___ _ __(_) |__   ___ _ __ ",
        r"  \ \ /\ / /| '_ \| / __| '_ \ / _ \ '__|| || '__/ _` | '_ \/ __|/ __| '__| | '_ \ / _ \ '__|",
        r"   \ V  V / | | | | \__ \ |_) |  __/ |   | || | | (_| | | | \__ \ (__| |  | | |_) |  __/ |   ",
        r"    \_/\_/  |_| |_|_|___/ .__/ \___|_|   |_||_|  \__,_|_| |_|___/\___|_|  |_|_.__/ \___|_|   ",
        r"                        |_|                                                                  ",
        "                                                                                              ",
        "                                                                                              ",
        "                    АУДИО/ВИДЕО ТРАНСКРИБАТОР",
        "                       На основе Whisper",
        "                          𝑩𝒚 𝒙𝟎𝒅𝒆𝒙\n",
    ]
    for line in banner:
        print(line)

def transcribe_audio(input_path, model_size="small", language="Russian", output_format="txt"):
    """
    Транскрибирует аудиофайл с помощью Whisper
    
    Args:
        input_path (str): Путь к аудиофайлу
        model_size (str): Размер модели (tiny, base, small, medium, large)
        language (str): Язык распознавания
        output_format (str): Формат вывода (txt, srt, vtt, tsv, json)
    """
    
    # Проверяем существование файла
    if not os.path.exists(input_path):
        print(f"❌ Ошибка: Файл '{input_path}' не найден!")
        return False
    
    # Проверяем поддерживаемые форматы
    supported_formats = ['.mp3', '.wav', '.m4a', '.mp4', '.avi', '.mov', '.mkv', '.flac', '.ogg']
    file_ext = Path(input_path).suffix.lower()
    if file_ext not in supported_formats:
        print(f"⚠️  Предупреждение: Формат {file_ext} может не поддерживаться. Попробуйте конвертировать в MP3 или WAV.")
    
    try:
        print(f"🔧 Загружаем модель '{model_size}'...")
        model = whisper.load_model(model_size)
        
        print(f"🎙️  Транскрибируем '{input_path}' на языке {language}...")
        
        # Определяем язык для Whisper
        lang_code = "ru" if language.lower() in ["russian", "russkiy", "русский", "ru"] else language.lower()
        
        # Транскрибация
        result = model.transcribe(
            input_path,
            language=lang_code,
            verbose=True  # Показывает прогресс
        )
        
        # Создаем имя выходного файла
        base_name = Path(input_path).stem
        output_filename = f"{base_name}.{output_format}"
        
        # Сохраняем в нужном формате
        if output_format == "txt":
            with open(output_filename, "w", encoding="utf-8") as f:
                f.write(result["text"])
            print(f"✅ Текст сохранен в: {output_filename}")
            
        elif output_format == "srt":
            save_srt(result, output_filename)
            
        elif output_format == "vtt":
            save_vtt(result, output_filename)
            
        elif output_format == "tsv":
            save_tsv(result, output_filename)
            
        elif output_format == "json":
            import json
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✅ JSON сохранен в: {output_filename}")
        
        # Выводим текст в консоль
        print("\n" + "="*60)
        print("🎯 РАСПОЗНАННЫЙ ТЕКСТ:")
        print("="*60)
        print(result["text"])
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при транскрибации: {e}")
        return False

def save_srt(result, filename):
    """Сохраняет результат в формате SRT"""
    with open(filename, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"]):
            start = format_time(segment["start"])
            end = format_time(segment["end"])
            f.write(f"{i+1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{segment['text'].strip()}\n\n")
    print(f"✅ Субтитры SRT сохранены в: {filename}")

def save_vtt(result, filename):
    """Сохраняет результат в формате VTT"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("WEBVTT\n\n")
        for i, segment in enumerate(result["segments"]):
            start = format_time(segment["start"])
            end = format_time(segment["end"])
            f.write(f"{i+1}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{segment['text'].strip()}\n\n")
    print(f"✅ Субтитры VTT сохранены в: {filename}")

def save_tsv(result, filename):
    """Сохраняет результат в формате TSV"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write("start\tend\ttext\n")
        for segment in result["segments"]:
            f.write(f"{segment['start']:.2f}\t{segment['end']:.2f}\t{segment['text'].strip()}\n")
    print(f"✅ TSV файл сохранен в: {filename}")

def format_time(seconds):
    """Форматирует время в формат SRT/VTT"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')

def main():
    parser = argparse.ArgumentParser(description='Транскрибация аудио с помощью Whisper')
    parser.add_argument('input_path', help='Путь к аудио/видео файлу')
    parser.add_argument('--model', default='small', 
                       choices=['tiny', 'base', 'small', 'medium', 'large'],
                       help='Модель Whisper (по умолчанию: small)')
    parser.add_argument('--language', default='Russian',
                       help='Язык распознавания (по умолчанию: Russian)')
    parser.add_argument('--output_format', default='txt',
                       choices=['txt', 'srt', 'vtt', 'tsv', 'json'],
                       help='Формат вывода (по умолчанию: txt)')
    
    args = parser.parse_args()
    
    # Показываем баннер
    print_banner()
    
    transcribe_audio(
        args.input_path,
        args.model,
        args.language,
        args.output_format
    )

if __name__ == "__main__":
    # Если аргументы не переданы, используем интерактивный режим
    if len(sys.argv) == 1:
        print_banner()
        print("🎮 ИНТЕРАКТИВНЫЙ РЕЖИМ")
        print("-" * 40)
        
        input_path = input("📁 Введите путь к аудио/видео файлу: ").strip('"')
        
        print("\n🔧 Доступные модели:")
        print("   tiny   - быстрая, низкая точность")
        print("   base   - баланс скорости и точности")
        print("   small  - хорошая точность")
        print("   medium - высокая точность")
        print("   large  - наилучшая точность")
        
        model = input("🎯 Выберите модель (по умолчанию small): ").strip() or "small"
        language = input("🌍 Язык (по умолчанию Russian): ").strip() or "Russian"
        
        print("\n📄 Доступные форматы вывода:")
        print("   txt  - простой текст")
        print("   srt  - субтитры SRT")
        print("   vtt  - субтитры VTT")
        print("   tsv  - таблица с временными метками")
        print("   json - полный результат")
        
        output_format = input("💾 Формат вывода (по умолчанию txt): ").strip() or "txt"
        
        print("\n" + "="*50)
        transcribe_audio(input_path, model, language, output_format)
    else:
        main()