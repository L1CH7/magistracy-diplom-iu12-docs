# --- docs/latex/.latexmkrc ---

# 1. Куда складывать мусор и PDF
$out_dir = 'build';

# 2. Движок xelatex
$pdf_mode = 5;

# 3. Команда компиляции
# ВАЖНО: Мы убрали -output-directory=%D, так как он уже есть внутри %O
# Добавили создание папки build/chapters перед запуском
$xelatex = 'mkdir -p build/chapters && xelatex -synctex=1 -interaction=nonstopmode -file-line-error -shell-escape %O %S';

# 4. Пути к стилям (шаблон + локальные ассеты)
ensure_path('TEXINPUTS', './latex-iu1-template/lib//:./assets//');

sub ensure_path {
    my ($var, $path) = @_;
    my $sep = ($^O eq 'MSWin32') ? ';' : ':';
    if ($ENV{$var}) { $ENV{$var} = $path . $sep . $ENV{$var}; }
    else { $ENV{$var} = $path . $sep; }
}

# 5. Очистка
$cleanup_mode = 1;
$clean_ext = "bbl nav out snm xdv";