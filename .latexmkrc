# --- docs/latex/.latexmkrc (IEEE article style) ---

# 1. Output directory
$out_dir = 'build';

# 2. PDF engine (xelatex)
$pdf_mode = 5;

# 3. Compile command
$xelatex = 'mkdir -p build && xelatex -synctex=1 -interaction=nonstopmode -file-line-error -shell-escape %O %S';

# 4. Search paths for styles, bibliography, and assets
ensure_path('TEXINPUTS', './latex-ieee-template//:./assets//');
ensure_path('BIBINPUTS', './latex-ieee-template//');
ensure_path('BSTINPUTS', './latex-ieee-template//');

if ( !defined &ensure_path ) {
    sub ensure_path {
        my ($var, $path) = @_;
        my $sep = ($^O eq 'MSWin32') ? ';' : ':';
        if ($ENV{$var}) { $ENV{$var} = $path . $sep . $ENV{$var}; }
        else { $ENV{$var} = $path . $sep; }
    }
}

# 5. Cleanup
$cleanup_mode = 1;
$clean_ext = "bbl nav out snm xdv";
