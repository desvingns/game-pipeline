#!/usr/bin/env bash
# Generator-side archive location. Source only: no output on its own.
# Superseded files go to $PET_ARCHIVE_ROOT/<project>/<YYYY-MM-DD>/<sub> when the
# shared archive is configured (first creation per day is logged in its INDEX.md),
# else to <project>/archive/<sub>. Prints the directory; never deletes anything.
# Mirrors gp_archive_dir in templates/common/scripts/{{PREFIX}}-common.sh.
gp_archive_dir() {
    local project_root shared day base shown_root shown_base
    project_root=$(cd "$1" && pwd -P) || return 1
    shared="${PET_ARCHIVE_ROOT:-}"
    if [ -z "$shared" ]; then printf '%s/archive/%s\n' "$project_root" "$2"; return 0; fi
    if command -v cygpath >/dev/null 2>&1; then shared=$(cygpath -u "$shared"); fi
    day=$(date +%Y-%m-%d)
    base="$shared/$(basename "$project_root")/$day/$2"
    if [ ! -d "$base" ]; then
        mkdir -p "$base" || return 1
        shown_root="$project_root"; shown_base="$base"
        if command -v cygpath >/dev/null 2>&1; then
            shown_root=$(cygpath -m "$project_root"); shown_base=$(cygpath -m "$base")
        fi
        printf '%s | %s (%s) | %s | auto backup (gp)\n' "$day" "$shown_root" "$2" "$shown_base" \
            >> "$shared/INDEX.md"
    fi
    printf '%s\n' "$base"
}
