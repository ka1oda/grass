import os
import math
import shutil
import multiprocessing
from concurrent.futures import ThreadPoolExecutor

# === Настройки ===
ROOT_FOLDER = os.getcwd()  # Используем текущую папку, откуда запускается скрипт
TEMPLATE_FOLDER = r"J:\Grasss\grass-mining v3\grass-mining"  # Папка с файлами grass-mining
NUM_THREADS = multiprocessing.cpu_count()  # Автоматическое определение максимального количества потоков
MAX_ACCOUNTS_PER_FOLDER = 5_000  # Максимум аккаунтов в одной папке на данный момент рекомендовано 5к
PROXY_MULTIPLIER = 3  # Множитель количества прокси

# Тиры (имя тира: (кол-во аккаунтов, кол-во прокси на акк))
tiers = {
    "Tier_1_47": (500, 50),
    "Tier_2_31": (300, 10),
    "Tier_3_11": (250, 1),
}


# Функция для чтения файлов
def read_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f.readlines()]


accounts = read_file("accounts.txt")
proxies = read_file("proxies.txt")

# Проверка наличия достаточного количества данных
total_needed_accounts = sum(tier[0] for tier in tiers.values())
if len(accounts) < total_needed_accounts:
    raise ValueError("Недостаточно аккаунтов для распределения.")

# Подсчет необходимого количества прокси
total_needed_proxies = sum(tier[0] * tier[1] * PROXY_MULTIPLIER for tier in tiers.values())
if len(proxies) < total_needed_proxies:
    print(f"\nВнимание! Недостаточно прокси. На последний тир в списке не хватает Требуется: {total_needed_proxies}, доступно: {len(proxies)}\n")
    input("Нажмите Enter для продолжения...")

account_index, proxy_index = 0, 0
created_folders = []


def copy_folder_multithread(src_folder, dest_folder):
    if not os.path.exists(src_folder):
        return
    os.makedirs(dest_folder, exist_ok=True)
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        for item in os.listdir(src_folder):
            src_path = os.path.join(src_folder, item)
            dest_path = os.path.join(dest_folder, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dest_path, dirs_exist_ok=True)
            else:
                executor.submit(shutil.copy2, src_path, dest_path)


# Запрос выбора действия
print("Выберите действие:")
print("1 - Просто распределить аккаунты и прокси")
print("2 - Создать структуру и скопировать файлы")
choice = input("Введите номер действия: ")

# Основной цикл распределения
for tier_name, (total_accounts, repeats) in tiers.items():
    tier_folder = os.path.join(ROOT_FOLDER, tier_name)
    os.makedirs(tier_folder, exist_ok=True)

    total_connections = total_accounts * repeats
    parts_needed = math.ceil(total_connections / MAX_ACCOUNTS_PER_FOLDER)
    accounts_per_part = math.ceil(total_accounts / parts_needed)

    for part in range(parts_needed):
        folder_name = os.path.join(tier_folder, f"Part_{part + 1}")
        os.makedirs(folder_name, exist_ok=True)
        created_folders.append(folder_name)

        if choice == "2":
            copy_folder_multithread(TEMPLATE_FOLDER, folder_name)

        acc_chunk = accounts[account_index:account_index + accounts_per_part]
        expanded_accounts = [acc for acc in acc_chunk for _ in range(repeats)]
        proxies_needed = len(expanded_accounts) * PROXY_MULTIPLIER
        proxy_chunk = proxies[proxy_index:proxy_index + proxies_needed]

        with open(os.path.join(folder_name, "accounts.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(expanded_accounts))
        with open(os.path.join(folder_name, "proxies.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(proxy_chunk))

        account_index += accounts_per_part
        proxy_index += proxies_needed

# Генерация RUN_ALL.bat
if choice == "2":
    run_all_content = "@echo off\n"
    run_all_content += "echo Запуск всех START.bat...\n"
    run_all_content += "echo =======================\n\n"

    for folder in created_folders:
        run_all_content += f'cd /d "{folder}"\n'
        run_all_content += f'start START.bat\n'
        run_all_content += f'timeout /t 5 /nobreak >nul\n\n'

    run_all_content += "echo =======================\n"
    run_all_content += "echo Готово! Все процессы запущены.\n"
    run_all_content += "pause\n"

    with open(os.path.join(ROOT_FOLDER, "RUN_ALL.bat"), "w", encoding="utf-8") as f:
        f.write(run_all_content)

print(f"Готово! Все файлы созданы в {ROOT_FOLDER}.")
