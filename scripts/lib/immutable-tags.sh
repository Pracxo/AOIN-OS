#!/usr/bin/env bash

AION_IMMUTABLE_V01_TAG="aion-v0.1.0"
AION_IMMUTABLE_V01_SHA="105fe29348160a2218ac095cfffadcb6f234421f"

aion_git_ref_exists() {
  git rev-parse --verify --quiet "$1" >/dev/null 2>&1
}

aion_fetch_immutable_v01_tag() {
  git fetch --quiet --no-tags origin \
    "refs/tags/${AION_IMMUTABLE_V01_TAG}:refs/tags/${AION_IMMUTABLE_V01_TAG}"
}

aion_ensure_immutable_v01_tag() {
  local tag_ref

  if ! aion_git_ref_exists "${AION_IMMUTABLE_V01_TAG}^{commit}"; then
    if ! aion_fetch_immutable_v01_tag; then
      echo "${AION_IMMUTABLE_V01_TAG} tag is missing and exact fetch from origin failed" >&2
      return 1
    fi
  fi

  if ! aion_git_ref_exists "${AION_IMMUTABLE_V01_TAG}^{commit}"; then
    echo "${AION_IMMUTABLE_V01_TAG} tag is missing after exact fetch from origin" >&2
    return 1
  fi

  tag_ref="$(git rev-list -n 1 "$AION_IMMUTABLE_V01_TAG" 2>/dev/null || true)"
  if [[ -z "$tag_ref" ]]; then
    echo "${AION_IMMUTABLE_V01_TAG} tag cannot be resolved to a commit" >&2
    return 1
  fi

  if [[ "$tag_ref" != "$AION_IMMUTABLE_V01_SHA" ]]; then
    echo "${AION_IMMUTABLE_V01_TAG} must remain at $AION_IMMUTABLE_V01_SHA (found $tag_ref)" >&2
    return 1
  fi

  printf '%s\n' "$tag_ref"
}

aion_confirm_immutable_v01_tag_history() {
  local tag_ref
  tag_ref="$(aion_ensure_immutable_v01_tag)" || return 1

  if aion_git_ref_exists origin/main; then
    if git merge-base --is-ancestor "$AION_IMMUTABLE_V01_TAG" origin/main; then
      echo "${AION_IMMUTABLE_V01_TAG} is in origin/main history" >&2
    else
      echo "WARN: ${AION_IMMUTABLE_V01_TAG} ancestry could not be confirmed against origin/main" >&2
    fi
  elif aion_git_ref_exists main; then
    if git merge-base --is-ancestor "$AION_IMMUTABLE_V01_TAG" main; then
      echo "${AION_IMMUTABLE_V01_TAG} is in main history" >&2
    else
      echo "WARN: ${AION_IMMUTABLE_V01_TAG} ancestry could not be confirmed against main" >&2
    fi
  else
    echo "WARN: origin/main unavailable in this checkout; skipping non-release tag ancestry confirmation" >&2
  fi

  printf '%s\n' "$tag_ref"
}
