#!/bin/zsh
set -eu
cd "${0:A:h}/browser"
exec node tools/serve.mjs --open
