from pathlib import Path
import shutil


# Сетевой диск ПК аналитики
REMOTE_ROOT = Path(r"B:\\")

# Локальная папка с JSON протоколами на ПК инспекции
LOCAL_JSON_DIR = Path(r"C:\Users\user\Desktop\Protocols\json")


def is_remote_available() -> bool:
    """
    Проверяет, доступен ли сетевой диск ПК аналитики.
    """
    try:
        return REMOTE_ROOT.exists() and REMOTE_ROOT.is_dir()
    except OSError as e:
        print(f"Сетевой диск недоступен: {e}")
        return False


def push_file_to_pc2(local_path: str | Path):
    """
    Копирует только один JSON файл на ПК аналитики.
    """
    local_path = Path(local_path)

    if local_path.suffix.lower() != ".json":
        print(f"⚠Пропускаем не JSON: {local_path.name}")
        return []

    if not local_path.exists():
        print(f"Локальный файл не найден: {local_path}")
        return []

    if not is_remote_available():
        print("ПК аналитики сейчас недоступен. JSON сохранён локально и будет отправлен позже.")
        return []

    try:
        remote_path = REMOTE_ROOT / local_path.name

        # Если файл уже есть на ПК аналитики, повторно он не копируется
        if remote_path.exists():
            print(f"JSON уже есть на ПК аналитики: {remote_path}")
            return [remote_path]

        shutil.copy2(local_path, remote_path)
        print(f"JSON отправлен на ПК аналитики: {remote_path}")
        return [remote_path]

    except OSError as e:
        print(f"Ошибка отправки JSON на ПК аналитики: {e}")
        print("Файл остался локально и будет отправлен позже.")
        return []

    except Exception as e:
        print(f"Неизвестная ошибка отправки JSON: {e}")
        return []


def sync_unsent_json_files():
    """
    Догружает на ПК аналитики все локальные JSON-файлы,
    которых ещё нет в сетевой папке.
    """
    sent_files = []
    skipped_files = []

    if not LOCAL_JSON_DIR.exists():
        print(f"Локальная папка JSON не найдена: {LOCAL_JSON_DIR}")
        return sent_files

    if not is_remote_available():
        print("ПК аналитики недоступен. Догрузка JSON сейчас невозможна.")
        return sent_files

    json_files = sorted(LOCAL_JSON_DIR.glob("*.json"))

    if not json_files:
        print("Локальных JSON-файлов для догрузки нет.")
        return sent_files

    for local_json in json_files:
        remote_json = REMOTE_ROOT / local_json.name

        try:
            if remote_json.exists():
                skipped_files.append(local_json.name)
                continue

            shutil.copy2(local_json, remote_json)
            sent_files.append(remote_json)
            print(f"Догружен JSON на ПК аналитики: {remote_json}")

        except OSError as e:
            print(f"Не удалось догрузить JSON {local_json.name}: {e}")
            break

        except Exception as e:
            print(f"Неизвестная ошибка при догрузке {local_json.name}: {e}")
            break

    if sent_files:
        print(f"Догрузка завершена. Отправлено файлов: {len(sent_files)}")
    else:
        print("Новых JSON-файлов для отправки нет.")

    return sent_files
