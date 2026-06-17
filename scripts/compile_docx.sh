#!/bin/bash
# compile_docx.sh - Автоматическая сборка документа DOCX из LaTeX с помощью pandoc

# Определяем корень проекта относительно расположения самого скрипта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCS_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Устанавливаем режим завершения при ошибках
set -e

# Константы путей относительно корня проекта
MAIN_TEX="$DOCS_ROOT/main.tex"
FLAT_TEX="$DOCS_ROOT/flat-main.tex"
BIB_FILE="$DOCS_ROOT/chapters/biblio.bib"
REFERENCE_DOC="$DOCS_ROOT/scripts/docx/references/nir-reference.docx"
CSL_FILE="$DOCS_ROOT/scripts/docx/references/gost.csl"
LUA_FILTER="$DOCS_ROOT/scripts/docx/plugins/equations.lua"
POSTPROCESS_PY="$DOCS_ROOT/scripts/docx/plugins/postprocess_docx.py"
OUTPUT_DOC="$DOCS_ROOT/out/result.docx"

echo "=== Шаг 1: Разворачивание (flattening) LaTeX документа ==="
if [ -f "$MAIN_TEX" ]; then
    # Запускаем latexpand из директории корня проекта, чтобы пути к файлам инклудов
    # разрешались корректно относительно корня.
    (
        cd "$DOCS_ROOT"
        latexpand main.tex -o "$FLAT_TEX"
        # Добавляем определение \where для корректного парсинга pandoc
        echo '\newcommand{\where}[1]{где \begin{tabular}{c c} #1 \end{tabular}}' > tmp-flat.tex
        cat "$FLAT_TEX" >> tmp-flat.tex
        mv tmp-flat.tex "$FLAT_TEX"
    )
    echo "Создан объединенный файл: $FLAT_TEX"
else
    echo "Ошибка: Файл $MAIN_TEX не найден!" >&2
    exit 1
fi

echo "=== Шаг 2: Конвертация в DOCX через pandoc с цитированием ==="
mkdir -p "$DOCS_ROOT/out"

PANDOC_FLAGS=(
    "$FLAT_TEX"
    -f latex
    -t docx
    --citeproc
    --bibliography="$BIB_FILE"
    --lua-filter="$LUA_FILTER"
    --resource-path="$DOCS_ROOT"
)

# Подключаем стиль ГОСТ для цитирования, если он присутствует
if [ -f "$CSL_FILE" ]; then
    PANDOC_FLAGS+=(--csl="$CSL_FILE")
    echo "Используется стиль цитирования: $CSL_FILE"
fi

# Подключаем шаблон оформления Word, если он существует
if [ -f "$REFERENCE_DOC" ]; then
    PANDOC_FLAGS+=(--reference-doc="$REFERENCE_DOC")
    echo "Используется файл стиля: $REFERENCE_DOC"
else
    echo "Предупреждение: Файл стиля $REFERENCE_DOC не найден!" >&2
    echo "Сборка будет выполнена со стандартными стилями Word..." >&2
fi

pandoc "${PANDOC_FLAGS[@]}" -o "$OUTPUT_DOC"

echo "=== Шаг 3: Пост-обработка документа ==="
python3 "$POSTPROCESS_PY" "$OUTPUT_DOC"

# Очистка временного плоского файла
if [ -f "$FLAT_TEX" ]; then
    rm -f "$FLAT_TEX"
fi

echo "=== Успешно завершено! Файл сохранен в: $OUTPUT_DOC ==="
