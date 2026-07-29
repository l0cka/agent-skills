#!/usr/bin/env bash
set -Eeuo pipefail

repo_url="https://github.com/QuantEcon/lecture-python.myst"
pinned_commit="dba5555ac22c4127d46bb9fcd209fc6f449d2662"

if [[ -n "${QUANTITATIVE_TRADING_QUANTECON_ROOT:-}" ]]; then
  default_target="${QUANTITATIVE_TRADING_QUANTECON_ROOT}"
else
  cache_base="${XDG_CACHE_HOME:-${HOME}/.cache}"
  default_target="${cache_base}/quantitative-trading/lecture-python.myst"
fi
target_dir="${1:-${default_target}}"

if ! command -v git >/dev/null 2>&1; then
  printf 'git is required but was not found\n' >&2
  exit 1
fi

if [[ -e "${target_dir}" && ! -d "${target_dir}/.git" ]]; then
  printf 'target exists but is not a Git checkout: %s\n' "${target_dir}" >&2
  exit 1
fi

if [[ -d "${target_dir}/.git" ]]; then
  remote_url="$(git -C "${target_dir}" remote get-url origin)"
  if [[ "${remote_url}" != "${repo_url}" && "${remote_url}" != "${repo_url}.git" ]]; then
    printf 'unexpected origin for %s: %s\n' "${target_dir}" "${remote_url}" >&2
    exit 1
  fi
  if [[ -n "$(git -C "${target_dir}" status --porcelain)" ]]; then
    printf 'refusing to replace a dirty checkout: %s\n' "${target_dir}" >&2
    exit 1
  fi
  git -C "${target_dir}" fetch --depth 1 origin "${pinned_commit}"
else
  mkdir -p "$(dirname -- "${target_dir}")"
  git clone --filter=blob:none --no-checkout "${repo_url}" "${target_dir}"
  git -C "${target_dir}" fetch --depth 1 origin "${pinned_commit}"
fi

git -C "${target_dir}" checkout --detach "${pinned_commit}"
resolved="$(git -C "${target_dir}" rev-parse HEAD)"
if [[ "${resolved}" != "${pinned_commit}" ]]; then
  printf 'commit verification failed: expected %s, got %s\n' "${pinned_commit}" "${resolved}" >&2
  exit 1
fi
printf 'synced %s at %s\n' "${target_dir}" "${resolved}"
