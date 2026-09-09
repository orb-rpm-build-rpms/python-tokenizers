#!/bin/sh
# rust-sources.sh - assemble the Rust "vendor" tarball for an offline build.
#
# rpm-build-assist runs every *sources.sh in the checked-out package directory
# after spectool has downloaded the online sources (here the PyPI sdist). This
# project has no lookaside cache, so rather than have a maintainer run
# `cargo vendor` by hand and upload the result, we regenerate the vendor
# tarball on demand at build time.
#
# The maturin/Cargo project lives under bindings/python (with a path dependency
# on the bundled ../../tokenizers crate), but the sdist's pyproject.toml is at
# the archive ROOT (maturin manifest-path = bindings/python/Cargo.toml). The
# Python wheel build therefore runs from the root, and cargo discovers its
# config from the current dir upward -- so the vendor dir and .cargo/config.toml
# must live at the root, NOT under bindings/python (unlike python-safetensors,
# whose pyproject.toml is inside bindings/python). Hence vendor/ is packed at the
# archive root and the spec runs `%cargo_prep -v vendor` there; %cargo_test in
# bindings/python still finds that config by walking up to the root.
#
# The sdist DOES ship bindings/python/Cargo.lock, so we vendor with --locked
# (reproducible) and the spec keeps that shipped lock in the tree. The path
# dependency (../../tokenizers) is left untouched by cargo vendor: the spec keeps
# the bundled crate, so no rust-tokenizers Fedora crate is required.
set -eu

# The PyPI sdist spectool just fetched, e.g. "tokenizers-0.23.1.tar.gz". Exclude
# a previously generated "*-vendor.tar.*" so re-runs don't pick it up.
sdist=$(ls -1 ./*.tar.gz 2>/dev/null | grep -v -- '-vendor\.tar\.' | head -n1)
[ -n "$sdist" ] || { echo "rust-sources.sh: no sdist tarball found" >&2; exit 1; }

# "tokenizers-0.23.1.tar.gz" -> "tokenizers-0.23.1": the dir the sdist unpacks
# to and the stem for the vendor tarball name the spec's Source1 expects.
stem=$(basename "$sdist" .tar.gz)
vendor_tarball="${stem}-vendor.tar.xz"

# Idempotent: nothing to do if a previous run already produced the tarball.
[ -e "$vendor_tarball" ] && { echo "rust-sources.sh: $vendor_tarball already present"; exit 0; }

# Work under the checkout dir (mounted, ample space) rather than /tmp; the
# vendor tree is large (tens of MB uncompressed).
workdir=$(mktemp -d "$PWD/.rust-vendor.XXXXXX")
trap 'rm -rf "$workdir"' EXIT

tar xzf "$sdist" -C "$workdir"
# cargo vendor must run where the binding crate's Cargo.toml/Cargo.lock live, but
# the vendor tree is written to the ARCHIVE ROOT (../../vendor) so cargo finds it
# from the root build dir. --locked pins the exact versions the sdist shipped,
# keeping builds reproducible.
( cd "$workdir/$stem/bindings/python" && cargo vendor --locked ../../vendor >/dev/null )

# Pack vendor/ at the archive root; %prep unpacks it there and %cargo_prep
# -v vendor (run at the root) points cargo at ./vendor, using the sdist's own
# bindings/python/Cargo.lock (kept in the tree by the spec).
tar -C "$workdir/$stem" -cf - vendor \
    | xz -T0 -3 > "$vendor_tarball"
echo "rust-sources.sh: wrote $vendor_tarball"
