#!/usr/bin/env bash
set -euo pipefail

: "${RELEASE_TAG:?RELEASE_TAG is required}"
: "${RELEASE_SHA:?RELEASE_SHA is required}"
: "${GITHUB_REPOSITORY:?GITHUB_REPOSITORY is required}"
: "${RUNNER_TEMP:?RUNNER_TEMP is required}"
[[ "$RELEASE_TAG" =~ ^www-v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$ ]]
[[ "$GITHUB_REPOSITORY" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]
repo_url="https://github.com/${GITHUB_REPOSITORY}.git"
config_file="$RUNNER_TEMP/git-local-config"
set +e
git config --local --no-includes --name-only --get-regexp \
	'^(include|includeif|url\..*\.(insteadof|pushinsteadof)|credential(\..*)?|http(\..*)?|remote\..*\.(proxy|uploadpack|receivepack|pushurl)|core\.(sshcommand|gitproxy)|ssh\..*)$' >"$config_file"
config_status="$?"
set -e
if test "$config_status" != 0 -a "$config_status" != 1; then cat "$config_file"; exit "$config_status"; fi
if test "$config_status" = 0; then
	sort -u -- "$config_file" >"$config_file.unique"
	while IFS= read -r key; do
		if test -n "$key"; then
			git config --local --no-includes --unset-all "$key"
		fi
	done <"$config_file.unique"
elif test "$config_status" != 1; then
	exit "$config_status"
fi
rm -f -- "$config_file" "$config_file.unique"
git remote set-url origin "$repo_url"
test "$(git remote get-url origin)" = "$repo_url"

timeout --signal=TERM --kill-after=5s 60s \
	git -c protocol.file.allow=never -c protocol.ext.allow=never -c protocol.ssh.allow=never \
		-c credential.helper= -c core.askPass=/bin/false -c http.proxy= -c https.proxy= \
		-c http.sslVerify=true fetch --force --no-tags "$repo_url" \
		"refs/tags/$RELEASE_TAG:refs/remotes/origin/release-tag" refs/heads/main:refs/remotes/origin/main
test "$(git cat-file -t refs/remotes/origin/release-tag)" = tag
release_commit="$(git rev-parse 'refs/remotes/origin/release-tag^{commit}')"
test "$release_commit" = "$RELEASE_SHA"
test "$(git rev-parse HEAD)" = "$RELEASE_SHA"
test "$release_commit" = "$(git rev-parse refs/remotes/origin/main)"
