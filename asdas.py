import os
import shutil
import subprocess
import re

# Пути
ISO_DIR = "iso"
OUTPUT_DIR = "custom_iso"
DIST_NAME = "1.7_x86-64"
PACKAGES_LIST = "packages.txt"

# Функция логирования
def log(message):
    print(f"[INFO] {message}")

# Функция для получения всех зависимостей пакета
def get_all_dependencies(package, visited=None):
    if visited is None:
        visited = set()

    if package in visited:
        return set()

    visited.add(package)
    dependencies = set()

    try:
        log(f"Получение зависимостей для пакета: {package}")
        result = subprocess.run(
            ["apt-cache", "depends", package],
            capture_output=True, text=True, check=True
        )
        for line in result.stdout.splitlines():
            if line.strip().startswith(("Depends:", "PreDepends:")):
                dep = line.split(":", 1)[1].strip()
                # Убираем версии из названия пакета (если есть)
                dep = re.split(r" \([^)]+\)", dep)[0].strip()
                dependencies.add(dep)
                # Рекурсивно получаем зависимости для каждой зависимости
                dependencies.update(get_all_dependencies(dep, visited))
        if dependencies:
            log(f"Найденные зависимости для {package}: {', '.join(dependencies)}")
    except subprocess.CalledProcessError:
        log(f"[ERROR] Не удалось получить зависимости для {package}")
    return dependencies

# Функция для поиска пакетов по имени
def find_package_files(package):
    package_files = []
    for root, _, files in os.walk(os.path.join(ISO_DIR, "pool")):
        for file in files:
            if re.match(f"{package}_[^_]+\.deb", file):
                package_files.append((root, file))
    return package_files

# Собираем список пакетов (включая зависимости)
all_packages = set()
if os.path.exists(PACKAGES_LIST):
    log(f"Чтение списка пакетов из {PACKAGES_LIST}")
    with open(PACKAGES_LIST, "r") as f:
        for line in f:
            pkg = line.strip()
            if pkg:
                all_packages.add(pkg)
                all_packages.update(get_all_dependencies(pkg))

# Копируем пакеты, сохраняя структуру
log("Копируем пакеты...")
for package in all_packages:
    package_files = find_package_files(package)
    if package_files:
        for root, file in package_files:
            src_path = os.path.join(root, file)
            relative_path = os.path.relpath(root, ISO_DIR)
            dest_dir = os.path.join(OUTPUT_DIR, relative_path)

            os.makedirs(dest_dir, exist_ok=True)
            shutil.copy2(src_path, dest_dir)
            log(f"Скопирован {file} -> {dest_dir}")
    else:
        log(f"[WARNING] Пакет {package} не найден в ISO!")

# Создаем структуру репозитория
dist_path = os.path.join(OUTPUT_DIR, "dists", DIST_NAME, "main/binary-amd64")
os.makedirs(dist_path, exist_ok=True)

# Генерируем индекс пакетов
log("Создаем индекс пакетов (Packages.gz)...")
subprocess.run(
    f"dpkg-scanpackages {OUTPUT_DIR}/pool/ | gzip -9 > {dist_path}/Packages.gz",
    shell=True
)

# Генерируем `Release`-файл
release_content = f"""\
Origin: CustomRepo
Label: CustomRepo
Suite: stable
Codename: {DIST_NAME}
Architectures: amd64
Components: main
Description: Custom Debian Repository
MD5Sum:
"""

release_path = os.path.join(OUTPUT_DIR, "dists", DIST_NAME, "Release")
with open(release_path, "w") as f:
    f.write(release_content)

# 🔐 Подписываем `Release` GPG-ключом
GPG_KEY_ID = "your-key-id"  # 🔴 Укажите свой GPG-ключ!
if GPG_KEY_ID:
    log("Подписываем `Release.gpg` и `InRelease`...")
    subprocess.run(
        f"gpg --default-key {GPG_KEY_ID} --output {release_path}.gpg --detach-sign {release_path}",
        shell=True
    )
    subprocess.run(
        f"gpg --default-key {GPG_KEY_ID} --clearsign --output {release_path.replace('Release', 'InRelease')} {release_path}",
        shell=True
    )
else:
    log("[WARNING] GPG-ключ не указан! Подпись не будет создана.")

log("✅ Репозиторий готов! Можно выполнять `apt update`")