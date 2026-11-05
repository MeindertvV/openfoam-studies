#!/bin/bash
# Bron dit bestand: laadt .env, de OpenFOAM-omgeving en .venv, plus gedeelde helpers.
# Met --no-foam alleen .env en helpers (voor scripts die geen OpenFOAM nodig hebben).

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
export REPO_ROOT

die() { echo "FOUT: $*" >&2; exit 1; }

# .azjob bevat de gegevens van de actieve VM en wordt door az_up.sh geschreven
for file in "$REPO_ROOT/.env" "$REPO_ROOT/.azjob"; do
    if [ -f "$file" ]; then
        set -a
        source "$file"
        set +a
    fi
done

[ -d "$HOME/.local/bin" ] && export PATH="$HOME/.local/bin:$PATH"

if [ "${1:-}" != "--no-foam" ]; then
    OPENFOAM_BASHRC=${OPENFOAM_BASHRC:-/opt/openfoam11/etc/bashrc}
    [ -f "$OPENFOAM_BASHRC" ] || die "OpenFOAM niet gevonden: $OPENFOAM_BASHRC"
    # OpenFOAM's bashrc verdraagt set -eu niet
    _opts=$-
    set +eu
    source "$OPENFOAM_BASHRC"
    case $_opts in *e*) set -e ;; esac
    case $_opts in *u*) set -u ;; esac
    unset _opts
    # De d3d12-driver van WSL laat pvbatch crashen; software-rendering werkt wel
    [ -e /dev/dxg ] && export LIBGL_ALWAYS_SOFTWARE=1
fi

[ -d "$REPO_ROOT/.venv/bin" ] && export PATH="$REPO_ROOT/.venv/bin:$PATH"

# Zet STUDY_DIR en CASE_DIR uit een studienaam, studiemap of casemap
resolve_study() {
    local arg=${1:?geef een studie op}
    local dir
    if [ -d "$arg" ]; then
        dir=$(cd "$arg" && pwd)
    elif [ -d "$REPO_ROOT/studies/$arg" ]; then
        dir=$REPO_ROOT/studies/$arg
    else
        die "studie niet gevonden: $arg"
    fi
    [ "$(basename "$dir")" = case ] && dir=$(dirname "$dir")
    [ -f "$dir/case.yaml" ] || die "geen case.yaml in $dir"
    [ -d "$dir/case" ] || die "geen case/ in $dir"
    STUDY_DIR=$dir
    CASE_DIR=$dir/case
}

# Controleert of de Azure-variabelen gevuld zijn en zet AZ_TARGET
require_azure() {
    local var
    for var in AZ_SSH_HOST AZ_REMOTE_ROOT "$@"; do
        [ -n "${!var:-}" ] || die "$var is leeg; vul .env in of start een VM met az_up.sh"
    done
    AZ_TARGET=${AZ_SSH_USER:+$AZ_SSH_USER@}$AZ_SSH_HOST
}
