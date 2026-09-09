%bcond check 1
# Recent versions of python-datasets require a recent libarrow, so it was not
# branched to all releases.
%bcond datasets %{undefined fc43}

Name:           python-tokenizers
Version:        0.23.1
Release:        %autorelease
Summary:        Implementation of today's most used tokenizers

# pyarrow and pandas are not available on i686
# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch:    %{ix86}

# Generated license info from Rust dependencies
### BEGIN LICENSE SUMMARY ###
# 
# (MIT OR Apache-2.0) AND Unicode-DFS-2016
# Apache-2.0
# Apache-2.0 AND MIT
# Apache-2.0 OR BSL-1.0
# Apache-2.0 OR MIT
# Apache-2.0 OR MIT OR Zlib
# BSD-2-Clause
# BSD-2-Clause OR Apache-2.0 OR MIT
# MIT
# MIT OR Apache-2.0
# Unlicense OR MIT
###  END LICENSE SUMMARY  ###

# License expression simplified by the special rule for OR expressions:
# https://docs.fedoraproject.org/en-US/legal/license-field/#_special_rules_for_or_expressions
%global license_expression %{shrink:
Unicode-DFS-2016 AND
Apache-2.0 AND
(Apache-2.0 AND MIT) AND
(Apache-2.0 OR BSL-1.0) AND
(Apache-2.0 OR MIT OR Zlib) AND
BSD-2-Clause AND
MIT AND
(Unlicense OR MIT)
}

SourceLicense:  Apache-2.0
License:        %{license_expression}
URL:            https://github.com/huggingface/tokenizers
Source:         %{pypi_source tokenizers}
# Vendored Rust crate graph (./vendor at the archive root), regenerated at build
# time by rust-sources.sh. F44 does not package the crate versions this release
# needs (starting with rust-tokenizers 0.23.1 itself), so instead of the cargo
# buildrequires generator we build the whole graph offline from this tarball.
# See rust-sources.sh for how it is assembled.
Source1:        tokenizers-%{version}-vendor.tar.xz

BuildRequires:  python3-devel
BuildRequires:  cargo-rpm-macros >= 24
# The vendored esaxx-rs crate compiles bundled C++ via cc-rs. Without the cargo
# buildrequires generator (dropped for the offline vendor build) the compiler is
# not pulled in automatically, so require it explicitly.
BuildRequires:  gcc
BuildRequires:  gcc-c++
# For tests
%if %{with datasets}
BuildRequires:  python3dist(datasets)
%endif
BuildRequires:  python3dist(numpy)
BuildRequires:  python3dist(pytest)
BuildRequires:  python3dist(pytest-asyncio)
BuildRequires:  python3dist(pytest-datadir)
BuildRequires:  python3dist(pytest-xdist)


%global _description %{expand:
Provides an implementation of today's most used tokenizers,
with a focus on performance and versatility.
Bindings over the rust-tokenizers implementation.}

%description %_description

%package -n     python3-tokenizers
Summary:        %{summary}

%description -n python3-tokenizers %_description


%prep
# -a1 unpacks the vendor tarball (Source1) into the tree as ./vendor.
%autosetup -p1 -n tokenizers-%{version} -a1
# Copy out LICENSE
cp -a tokenizers/LICENSE LICENSE
# The bundled ../../tokenizers crate is kept: the binding crate depends on it by
# path, and cargo vendor leaves path deps in place, so no rust-tokenizers Fedora
# crate is needed. The sdist's bindings/python/Cargo.lock is kept too, so the
# vendored build (against that lock) is reproducible.
# cargo_prep runs at the archive root (where pyproject.toml lives and the wheel
# build runs). -v vendor builds the crate graph from ./vendor fully offline,
# replacing the cargo buildrequires generator; cargo discovers this root config
# from bindings/python too, so the Rust test suite in check finds it.
%cargo_prep -v vendor


%generate_buildrequires
# The Rust deps come from the vendor tree, so the cargo buildrequires generator
# is intentionally absent; only the Python build backend requirements remain.
%pyproject_buildrequires


%build
export RUSTFLAGS='%{build_rustflags}'
%pyproject_wheel


%install
%pyproject_install
# When saving the files, assert that a license file was found
%pyproject_save_files -l tokenizers


%check
%pyproject_check_import
cd bindings/python
# Per the Makefile, this option is required for tests to pass
%cargo_test -- --no-default-features
# only run the tests, not the benches
# the deselected tests are:
# - test_datasets fails with: "TypeError: Pickler._batch_setitems() takes 2 positional arguments but 3 were given"
# - test_gzip fails with: "FileNotFoundError: [Errno 2] No such file or directory: 'data/my-file.0.gz'"
# - the rest of the deselects are network accesses
%pytest -s -v ./tests/ \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_char_to_token" \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_char_to_word" \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_invalid_truncate_direction" \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_n_sequences" \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_sequence_ids" \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_token_to_chars" \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_token_to_sequence" \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_token_to_word" \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_truncation" \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_word_to_chars" \
        --deselect="tests/bindings/test_encoding.py::TestEncoding::test_word_to_tokens" \
        --deselect="tests/bindings/test_models.py::TestBPE::test_instantiate" \
        --deselect="tests/bindings/test_models.py::TestWordLevel::test_instantiate" \
        --deselect="tests/bindings/test_models.py::TestWordPiece::test_instantiate" \
        --deselect="tests/bindings/test_processors.py::TestByteLevelProcessing::test_processing" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_async_methods_existence" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_basic_encoding" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_concurrency" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_decode" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_encode" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_error_handling" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_large_batch" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_numpy_inputs" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_performance_comparison" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_various_input_formats" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_with_special_tokens" \
        --deselect="tests/bindings/test_tokenizer.py::TestAsyncTokenizer::test_with_truncation_padding" \
        --deselect="tests/bindings/test_tokenizer.py::TestTokenizer::test_decode_skip_special_tokens" \
        --deselect="tests/bindings/test_tokenizer.py::TestTokenizer::test_decode_stream_fallback" \
        --deselect="tests/bindings/test_tokenizer.py::TestTokenizer::test_encode_add_special_tokens" \
        --deselect="tests/bindings/test_tokenizer.py::TestTokenizer::test_encode_formats" \
        --deselect="tests/bindings/test_tokenizer.py::TestTokenizer::test_encode_special_tokens" \
        --deselect="tests/bindings/test_tokenizer.py::TestTokenizer::test_from_pretrained" \
        --deselect="tests/bindings/test_tokenizer.py::TestTokenizer::test_from_pretrained_revision" \
        --deselect="tests/bindings/test_tokenizer.py::TestTokenizer::test_multiprocessing_with_parallelism" \
        --deselect="tests/bindings/test_tokenizer.py::TestTokenizer::test_splitting" \
        --deselect="tests/bindings/test_trainers.py::TestUnigram::test_continuing_prefix_trainer_mismatch" \
        --deselect="tests/bindings/test_trainers.py::TestUnigram::test_train" \
        --deselect="tests/bindings/test_trainers.py::TestUnigram::test_train_parallelism_with_custom_pretokenizer" \
        --deselect="tests/documentation/test_pipeline.py::TestPipeline::test_bert_example" \
        --deselect="tests/documentation/test_pipeline.py::TestPipeline::test_pipeline" \
        --deselect="tests/documentation/test_quicktour.py::TestQuicktour::test_quicktour" \
%if %{with datasets}
        --deselect="tests/documentation/test_tutorial_train_from_iterators.py::TestTrainFromIterators::test_datasets" \
        --deselect="tests/documentation/test_tutorial_train_from_iterators.py::TestTrainFromIterators::test_gzip" \
%else
        --ignore="tests/documentation/test_tutorial_train_from_iterators.py" \
%endif
        --deselect="tests/implementations/test_bert_wordpiece.py::TestBertWordPieceTokenizer::test_basic_encode" \
        --deselect="tests/implementations/test_bert_wordpiece.py::TestBertWordPieceTokenizer::test_multiprocessing_with_parallelism" \
        --deselect="tests/implementations/test_byte_level_bpe.py::TestByteLevelBPE::test_add_prefix_space" \
        --deselect="tests/implementations/test_byte_level_bpe.py::TestByteLevelBPE::test_basic_encode" \
        --deselect="tests/implementations/test_byte_level_bpe.py::TestByteLevelBPE::test_lowerspace" \
        --deselect="tests/implementations/test_byte_level_bpe.py::TestByteLevelBPE::test_multiprocessing_with_parallelism" \
        --deselect="tests/implementations/test_char_bpe.py::TestCharBPETokenizer::test_basic_encode" \
        --deselect="tests/implementations/test_char_bpe.py::TestCharBPETokenizer::test_decoding" \
        --deselect="tests/implementations/test_char_bpe.py::TestCharBPETokenizer::test_lowercase" \
        --deselect="tests/implementations/test_char_bpe.py::TestCharBPETokenizer::test_multiprocessing_with_parallelism" \
        --deselect="tests/test_serialization.py::TestSerialization::test_full_serialization_albert" \
        --deselect="tests/test_serialization.py::TestSerialization::test_str_big"

cd ../../


%files -n python3-tokenizers -f %{pyproject_files}
%doc bindings/python/README.md bindings/python/CHANGELOG.md
%license LICENSE


%changelog
%autochangelog
