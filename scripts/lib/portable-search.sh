#!/usr/bin/env bash

# Provide a small ripgrep-compatible fallback for CI images that only have grep.
rg() {
  local rg_bin
  rg_bin="$(type -P rg 2>/dev/null || true)"
  if [[ -n "$rg_bin" ]]; then
    "$rg_bin" "$@"
    return $?
  fi

  local line_numbers=0
  local invert_match=0
  local fixed_strings=0
  while (($#)); do
    case "$1" in
      -n)
        line_numbers=1
        shift
        ;;
      -v)
        invert_match=1
        shift
        ;;
      -F|--fixed-strings)
        fixed_strings=1
        shift
        ;;
      --)
        shift
        break
        ;;
      -*)
        echo "portable rg fallback does not support option: $1" >&2
        return 2
        ;;
      *)
        break
        ;;
    esac
  done

  if (($# == 0)); then
    echo "portable rg fallback requires a pattern" >&2
    return 2
  fi

  local pattern="$1"
  shift
  local grep_opts=(-I)
  if ((line_numbers)); then
    grep_opts+=(-n)
  fi
  if ((invert_match)); then
    grep_opts+=(-v)
  fi
  if ((fixed_strings)); then
    grep_opts+=(-F)
  else
    grep_opts+=(-E)
  fi

  if (($# > 0)); then
    local paths=()
    local path
    for path in "$@"; do
      if [[ -e "$path" ]]; then
        paths+=("$path")
      fi
    done
    if ((${#paths[@]} == 0)); then
      return 1
    fi
    grep -R "${grep_opts[@]}" -- "$pattern" "${paths[@]}"
  else
    grep "${grep_opts[@]}" -- "$pattern"
  fi
}

export -f rg
