#include "ukr_itn/ukr_itn.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <filesystem>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

#include <fst/fstlib.h>

namespace {

int failures = 0;

void Check(bool condition, const std::string& message) {
  if (!condition) {
    std::cerr << "FAILED: " << message << '\n';
    ++failures;
  }
}

fst::StdVectorFst ByteIdentityFst() {
  fst::StdVectorFst fst;
  const auto state = fst.AddState();
  fst.SetStart(state);
  fst.SetFinal(state, fst::StdArc::Weight::One());
  for (int label = 1; label <= 255; ++label) {
    fst.AddArc(state, fst::StdArc(label, label, fst::StdArc::Weight::One(),
                                 state));
  }
  return fst;
}

fst::StdVectorFst NonByteFst() {
  fst::StdVectorFst fst;
  const auto start = fst.AddState();
  const auto final = fst.AddState();
  fst.SetStart(start);
  fst.SetFinal(final, fst::StdArc::Weight::One());
  fst.AddArc(start,
             fst::StdArc('x', 300, fst::StdArc::Weight::One(), final));
  return fst;
}

fst::StdVectorFst StringTransducer(const std::string& input,
                                   const std::string& output) {
  fst::StdVectorFst fst;
  auto state = fst.AddState();
  fst.SetStart(state);
  const size_t length = std::max(input.size(), output.size());
  for (size_t i = 0; i < length; ++i) {
    const auto next = fst.AddState();
    const int input_label =
        i < input.size() ? static_cast<unsigned char>(input[i]) : 0;
    const int output_label =
        i < output.size() ? static_cast<unsigned char>(output[i]) : 0;
    fst.AddArc(state, fst::StdArc(input_label, output_label,
                                 fst::StdArc::Weight::One(), next));
    state = next;
  }
  fst.SetFinal(state, fst::StdArc::Weight::One());
  return fst;
}

class TemporaryDirectory {
 public:
  TemporaryDirectory() {
    const auto suffix = std::chrono::steady_clock::now()
                            .time_since_epoch()
                            .count();
    path_ = std::filesystem::temp_directory_path() /
            ("ukr_itn_test_" + std::to_string(suffix));
    std::filesystem::create_directories(path_);
  }

  ~TemporaryDirectory() {
    std::error_code ignored;
    std::filesystem::remove_all(path_, ignored);
  }

  std::filesystem::path File(const std::string& name) const {
    return path_ / name;
  }

 private:
  std::filesystem::path path_;
};

}  // namespace

int main() {
  TemporaryDirectory temporary;
  const auto tagger_path = temporary.File("tagger.fst");
  const auto verbalizer_path = temporary.File("verbalizer.fst");
  Check(ByteIdentityFst().Write(tagger_path.string()), "write tagger FST");
  Check(ByteIdentityFst().Write(verbalizer_path.string()),
        "write verbalizer FST");

  std::string error = "stale error";
  auto normalizer = ukr_itn::InverseNormalizer::FromFiles(
      tagger_path.string(), verbalizer_path.string(), &error);
  Check(normalizer != nullptr, "load valid byte grammars");
  Check(error.empty(), "FromFiles clears stale errors on success");
  if (!normalizer) return 1;

  const std::vector<std::string> python_whitespace = {
      "\x09",          "\x0A",          "\x0B",          "\x0C",
      "\x0D",          "\x1C",          "\x1D",          "\x1E",
      "\x1F",          "\x20",          "\xC2\x85",      "\xC2\xA0",
      "\xE1\x9A\x80", "\xE2\x80\x80", "\xE2\x80\x81", "\xE2\x80\x82",
      "\xE2\x80\x83", "\xE2\x80\x84", "\xE2\x80\x85", "\xE2\x80\x86",
      "\xE2\x80\x87", "\xE2\x80\x88", "\xE2\x80\x89", "\xE2\x80\x8A",
      "\xE2\x80\xA8", "\xE2\x80\xA9", "\xE2\x80\xAF", "\xE2\x81\x9F",
      "\xE3\x80\x80",
  };
  for (const auto& whitespace : python_whitespace) {
    std::string output;
    error = "stale error";
    Check(normalizer->Normalize("a" + whitespace + "b", &output, &error),
          "normalize a Python whitespace code point");
    Check(output == "a b", "collapse Python whitespace to one ASCII space");
    Check(error.empty(), "Normalize clears stale errors on success");
  }

  std::string all_whitespace;
  for (const auto& whitespace : python_whitespace) all_whitespace += whitespace;
  std::string output;
  Check(normalizer->Normalize(all_whitespace + "a" + all_whitespace + "b" +
                                  all_whitespace,
                              &output, &error),
        "normalize mixed leading, internal, and trailing whitespace");
  Check(output == "a b", "trim and collapse mixed Unicode whitespace");

  const std::string left_quote = "\xC2\xAB";
  const std::string right_quote = "\xC2\xBB";
  Check(normalizer->Normalize(" " + left_quote + " a " + right_quote + " ",
                              &output, &error),
        "normalize punctuation with surrounding whitespace");
  Check(output == left_quote + "a" + right_quote,
        "reattach Ukrainian quotation marks");

  const std::string canonical_apostrophe = "p'iat";
  const std::string canonical_word =
      "tokens { word { name: \"" + canonical_apostrophe + "\" } }";
  for (const std::string& variant : {std::string("\xE2\x80\x99"),
                                     std::string("\xCA\xBC")}) {
    const std::string original = "p" + variant + "iat";
    const std::string original_word =
        "tokens { word { name: \"" + original + "\" } }";
    Check(StringTransducer(canonical_apostrophe, canonical_word)
              .Write(tagger_path.string()),
          "write apostrophe-canonicalizing tagger");
    Check(StringTransducer(original_word, original)
              .Write(verbalizer_path.string()),
          "write apostrophe-restoring verbalizer");
    auto apostrophe_normalizer = ukr_itn::InverseNormalizer::FromFiles(
        tagger_path.string(), verbalizer_path.string(), &error);
    Check(apostrophe_normalizer != nullptr,
          "load apostrophe restoration grammars");
    if (apostrophe_normalizer) {
      Check(apostrophe_normalizer->Normalize(original, &output, &error),
            "canonicalize an apostrophe variant for classification");
      Check(output == original,
            "restore an apostrophe variant in a pass-through word");
    }
  }

  const std::string uppercase_word = "KYIV";
  const std::string lowercase_word = "kyiv";
  const std::string lowercase_word_tag =
      "tokens { word { name: \"" + lowercase_word + "\" } }";
  const std::string uppercase_word_tag =
      "tokens { word { name: \"" + uppercase_word + "\" } }";
  Check(StringTransducer(lowercase_word, lowercase_word_tag)
            .Write(tagger_path.string()),
        "write case-canonicalizing tagger");
  Check(StringTransducer(uppercase_word_tag, uppercase_word)
            .Write(verbalizer_path.string()),
        "write case-restoring verbalizer");
  auto case_normalizer = ukr_itn::InverseNormalizer::FromFiles(
      tagger_path.string(), verbalizer_path.string(), &error);
  Check(case_normalizer != nullptr, "load case restoration grammars");
  if (case_normalizer) {
    Check(case_normalizer->Normalize(uppercase_word, &output, &error),
          "lowercase a token for classification");
    Check(output == uppercase_word,
          "restore original case in a pass-through word");
  }

  const std::string uppercase_sto = "\xD0\xA1\xD0\xA2\xD0\x9E";
  const std::string lowercase_sto = "\xD1\x81\xD1\x82\xD0\xBE";
  Check(StringTransducer(lowercase_sto, "100").Write(tagger_path.string()),
        "write Ukrainian case-canonicalizing tagger");
  Check(StringTransducer("100", "100").Write(verbalizer_path.string()),
        "write normalized-value verbalizer");
  auto ukrainian_case_normalizer = ukr_itn::InverseNormalizer::FromFiles(
      tagger_path.string(), verbalizer_path.string(), &error);
  Check(ukrainian_case_normalizer != nullptr,
        "load Ukrainian case-insensitive grammars");
  if (ukrainian_case_normalizer) {
    Check(ukrainian_case_normalizer->Normalize(uppercase_sto, &output, &error),
          "lowercase Ukrainian Cyrillic for classification");
    Check(output == "100", "do not restore case in a normalized token");
  }

  // Restore the identity files for the remaining API and concurrency tests.
  Check(ByteIdentityFst().Write(tagger_path.string()),
        "restore identity tagger FST");
  Check(ByteIdentityFst().Write(verbalizer_path.string()),
        "restore identity verbalizer FST");

  output = "unchanged";
  const std::string invalid_utf8("a\xFF", 2);
  Check(!normalizer->Normalize(invalid_utf8, &output, &error),
        "reject invalid UTF-8");
  Check(output == "unchanged", "leave output unchanged on invalid UTF-8");
  Check(error.find("invalid UTF-8") != std::string::npos,
        "report invalid UTF-8 precisely");

  error.clear();
  Check(!normalizer->Normalize("a", nullptr, &error), "reject null output");
  Check(error == "output must not be null", "report null output precisely");

  std::atomic<bool> threads_ok{true};
  std::vector<std::thread> threads;
  for (int thread = 0; thread < 8; ++thread) {
    threads.emplace_back([&] {
      for (int call = 0; call < 100; ++call) {
        std::string thread_output;
        if (!normalizer->Normalize(std::string(" a\xC2\xA0") + "b ",
                                   &thread_output) ||
            thread_output != "a b") {
          threads_ok = false;
          return;
        }
      }
    });
  }
  for (auto& thread : threads) thread.join();
  Check(threads_ok, "normalize concurrently with immutable grammars");

  const auto invalid_path = temporary.File("non_byte.fst");
  Check(NonByteFst().Write(invalid_path.string()), "write non-byte FST");
  error.clear();
  auto invalid = ukr_itn::InverseNormalizer::FromFiles(
      invalid_path.string(), verbalizer_path.string(), &error);
  Check(invalid == nullptr, "reject a grammar with non-byte labels");
  Check(error.find("non-byte label") != std::string::npos,
        "report non-byte grammar labels");

  if (failures != 0) {
    std::cerr << failures << " test assertion(s) failed\n";
    return 1;
  }
  return 0;
}
