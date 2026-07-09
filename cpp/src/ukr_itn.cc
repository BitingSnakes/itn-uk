#include "ukr_itn/ukr_itn.h"

#include <cstdint>
#include <regex>
#include <sstream>
#include <utility>
#include <vector>

namespace ukr_itn {
namespace {

using fst::StdArc;
using fst::StdConstFst;
using fst::StdVectorFst;

void ReplaceAll(std::string* s, const std::string& from,
                const std::string& to);

bool IsPythonWhitespace(uint32_t codepoint) {
  // This is the set recognized by CPython's str.isspace(), and therefore by
  // str.strip()/str.split() in ukr.utils.separate_punctuation.
  return (codepoint >= 0x09 && codepoint <= 0x0D) ||
         (codepoint >= 0x1C && codepoint <= 0x20) || codepoint == 0x85 ||
         codepoint == 0xA0 || codepoint == 0x1680 ||
         (codepoint >= 0x2000 && codepoint <= 0x200A) ||
         codepoint == 0x2028 || codepoint == 0x2029 || codepoint == 0x202F ||
         codepoint == 0x205F || codepoint == 0x3000;
}

// Validates UTF-8 while replacing Python whitespace with one ASCII space,
// collapsing runs and trimming the ends. Non-whitespace bytes are preserved.
bool NormalizeWhitespace(const std::string& text, std::string* output,
                         std::string* error) {
  std::string normalized;
  normalized.reserve(text.size());
  bool pending_space = false;

  for (size_t i = 0; i < text.size();) {
    const size_t start = i;
    const auto lead = static_cast<unsigned char>(text[i++]);
    uint32_t codepoint = 0;
    size_t continuation_count = 0;
    uint32_t minimum = 0;
    if (lead <= 0x7F) {
      codepoint = lead;
    } else if (lead >= 0xC2 && lead <= 0xDF) {
      codepoint = lead & 0x1F;
      continuation_count = 1;
      minimum = 0x80;
    } else if (lead >= 0xE0 && lead <= 0xEF) {
      codepoint = lead & 0x0F;
      continuation_count = 2;
      minimum = 0x800;
    } else if (lead >= 0xF0 && lead <= 0xF4) {
      codepoint = lead & 0x07;
      continuation_count = 3;
      minimum = 0x10000;
    } else {
      if (error) *error = "invalid UTF-8 at byte " + std::to_string(start);
      return false;
    }

    if (continuation_count > text.size() - i) {
      if (error) *error = "truncated UTF-8 at byte " + std::to_string(start);
      return false;
    }
    for (size_t n = 0; n < continuation_count; ++n) {
      const auto byte = static_cast<unsigned char>(text[i++]);
      if ((byte & 0xC0) != 0x80) {
        if (error) *error = "invalid UTF-8 at byte " + std::to_string(i - 1);
        return false;
      }
      codepoint = (codepoint << 6) | (byte & 0x3F);
    }
    if ((continuation_count != 0 && codepoint < minimum) ||
        (codepoint >= 0xD800 && codepoint <= 0xDFFF) ||
        codepoint > 0x10FFFF) {
      if (error) *error = "invalid UTF-8 at byte " + std::to_string(start);
      return false;
    }

    if (IsPythonWhitespace(codepoint)) {
      pending_space = !normalized.empty();
      continue;
    }
    if (pending_space) {
      normalized.push_back(' ');
      pending_space = false;
    }
    normalized.append(text, start, i - start);
  }

  *output = std::move(normalized);
  return true;
}

using OrthographyRestorations =
    std::vector<std::pair<std::string, std::string>>;

void AppendUtf8(uint32_t codepoint, std::string* output) {
  if (codepoint <= 0x7F) {
    output->push_back(static_cast<char>(codepoint));
  } else if (codepoint <= 0x7FF) {
    output->push_back(static_cast<char>(0xC0 | (codepoint >> 6)));
    output->push_back(static_cast<char>(0x80 | (codepoint & 0x3F)));
  } else if (codepoint <= 0xFFFF) {
    output->push_back(static_cast<char>(0xE0 | (codepoint >> 12)));
    output->push_back(static_cast<char>(0x80 | ((codepoint >> 6) & 0x3F)));
    output->push_back(static_cast<char>(0x80 | (codepoint & 0x3F)));
  } else {
    output->push_back(static_cast<char>(0xF0 | (codepoint >> 18)));
    output->push_back(static_cast<char>(0x80 | ((codepoint >> 12) & 0x3F)));
    output->push_back(static_cast<char>(0x80 | ((codepoint >> 6) & 0x3F)));
    output->push_back(static_cast<char>(0x80 | (codepoint & 0x3F)));
  }
}

uint32_t LowercaseForUkrainian(uint32_t codepoint) {
  // The exported lexical grammars use ASCII and Ukrainian Cyrillic. Original
  // spelling is restored for pass-through words after classification.
  if (codepoint >= 'A' && codepoint <= 'Z') return codepoint + 0x20;
  if (codepoint >= 0x0410 && codepoint <= 0x042F) return codepoint + 0x20;
  if (codepoint >= 0x0400 && codepoint <= 0x040F) return codepoint + 0x50;
  if (codepoint == 0x0490) return 0x0491;  // Ґ -> ґ
  return codepoint;
}

std::string LowercaseForClassification(const std::string& token) {
  std::string lower;
  lower.reserve(token.size());
  for (size_t i = 0; i < token.size();) {
    const auto lead = static_cast<unsigned char>(token[i++]);
    uint32_t codepoint = lead;
    size_t continuation_count = 0;
    if (lead >= 0xC2 && lead <= 0xDF) {
      codepoint = lead & 0x1F;
      continuation_count = 1;
    } else if (lead >= 0xE0 && lead <= 0xEF) {
      codepoint = lead & 0x0F;
      continuation_count = 2;
    } else if (lead >= 0xF0) {
      codepoint = lead & 0x07;
      continuation_count = 3;
    }
    for (size_t n = 0; n < continuation_count; ++n) {
      const auto byte = static_cast<unsigned char>(token[i++]);
      codepoint = (codepoint << 6) | (byte & 0x3F);
    }
    AppendUtf8(LowercaseForUkrainian(codepoint), &lower);
  }
  return lower;
}

std::string CanonicalizeOrthography(
    const std::string& text, OrthographyRestorations* restorations) {
  const std::string right_single_quote = "\xE2\x80\x99";  // U+2019
  const std::string modifier_apostrophe = "\xCA\xBC";      // U+02BC
  std::string result;
  size_t start = 0;
  while (start <= text.size()) {
    const size_t end = text.find(' ', start);
    const size_t length =
        end == std::string::npos ? text.size() - start : end - start;
    const std::string original = text.substr(start, length);
    std::string canonical = original;
    ReplaceAll(&canonical, right_single_quote, "'");
    ReplaceAll(&canonical, modifier_apostrophe, "'");
    canonical = LowercaseForClassification(canonical);
    if (canonical != original) restorations->emplace_back(canonical, original);
    if (!result.empty()) result.push_back(' ');
    result += canonical;
    if (end == std::string::npos) break;
    start = end + 1;
  }
  return result;
}

void RestoreWordOrthography(const OrthographyRestorations& restorations,
                            std::string* tagged) {
  for (const auto& restoration : restorations) {
    const std::string canonical =
        "word { name: \"" + restoration.first + "\" }";
    const std::string original =
        "word { name: \"" + restoration.second + "\" }";
    const size_t position = tagged->find(canonical);
    if (position != std::string::npos) {
      tagged->replace(position, canonical.size(), original);
    }
  }
}

// Builds a linear byte acceptor for a UTF-8 string (grammars are byte-arc
// FSTs, the pynini default).
StdVectorFst MakeByteAcceptor(const std::string& text) {
  StdVectorFst acceptor;
  auto state = acceptor.AddState();
  acceptor.SetStart(state);
  for (unsigned char byte : text) {
    auto next = acceptor.AddState();
    acceptor.AddArc(state, StdArc(byte, byte, StdArc::Weight::One(), next));
    state = next;
  }
  acceptor.SetFinal(state, StdArc::Weight::One());
  return acceptor;
}

// Applies `rule` to `input` and returns the shortest-path output string,
// mirroring pynini's `shortestpath(text @ rule).string()`.
bool RewriteShortestPath(const fst::Fst<StdArc>& rule,
                         const std::string& input, std::string* output,
                         std::string* error) {
  StdVectorFst lattice;
  fst::Compose(MakeByteAcceptor(input), rule, &lattice);
  if (lattice.Start() == fst::kNoStateId) return false;

  StdVectorFst best;
  fst::ShortestPath(lattice, &best, 1, true);
  if (best.Start() == fst::kNoStateId) return false;

  std::string result;
  auto state = best.Start();
  size_t traversed = 0;
  const size_t state_count = static_cast<size_t>(best.NumStates());
  while (state != fst::kNoStateId) {
    fst::ArcIterator<StdVectorFst> aiter(best, state);
    if (aiter.Done()) {
      if (best.Final(state) == StdArc::Weight::Zero()) {
        if (error) *error = "shortest path does not end in a final state";
        return false;
      }
      *output = std::move(result);
      return true;
    }
    const auto& arc = aiter.Value();
    aiter.Next();
    if (!aiter.Done()) {
      if (error) *error = "shortest-path result is not linear";
      return false;
    }
    if (arc.olabel < 0 || arc.olabel > 255) {
      if (error) {
        *error = "output label is outside the byte range: " +
                 std::to_string(arc.olabel);
      }
      return false;
    }
    if (arc.olabel != 0) {
      result.push_back(static_cast<char>(arc.olabel));
    }
    state = arc.nextstate;
    if (++traversed > state_count) {
      if (error) *error = "shortest-path result contains a cycle";
      return false;
    }
  }
  if (error) *error = "shortest path ended at an invalid state";
  return false;
}

// Punctuation split off into standalone tokens before tagging and
// re-attached after verbalization (mirrors ukr.utils.separate_punctuation /
// attach_punctuation). Hyphens and apostrophes are word-internal in
// Ukrainian and must not be split. UTF-8 sequences: « = C2 AB, » = C2 BB,
// … = E2 80 A6.
const std::vector<std::string>& PunctMarks() {
  static const std::vector<std::string> kMarks = {
      ",", ".", "!", "?", ";", ":", "(", ")", "\xC2\xAB", "\xC2\xBB",
      "\xE2\x80\xA6"};
  return kMarks;
}

std::string SeparatePunctuation(const std::string& text) {
  std::string spaced;
  spaced.reserve(text.size() + 16);
  for (size_t i = 0; i < text.size();) {
    bool matched = false;
    for (const auto& mark : PunctMarks()) {
      if (text.compare(i, mark.size(), mark) == 0) {
        spaced += ' ';
        spaced += mark;
        spaced += ' ';
        i += mark.size();
        matched = true;
        break;
      }
    }
    if (!matched) spaced += text[i++];
  }
  // collapse runs of whitespace and trim
  std::string out;
  out.reserve(spaced.size());
  for (char c : spaced) {
    if (c == ' ' || c == '\t') {
      if (!out.empty() && out.back() != ' ') out += ' ';
    } else {
      out += c;
    }
  }
  if (!out.empty() && out.back() == ' ') out.pop_back();
  return out;
}

void ReplaceAll(std::string* s, const std::string& from,
                const std::string& to) {
  for (size_t pos = 0; (pos = s->find(from, pos)) != std::string::npos;
       pos += to.size()) {
    s->replace(pos, from.size(), to);
  }
}

std::string AttachPunctuation(std::string text) {
  for (const char* close : {",", ".", "!", "?", ";", ":", ")", "\xC2\xBB",
                            "\xE2\x80\xA6"}) {
    ReplaceAll(&text, std::string(" ") + close, close);
  }
  for (const char* open : {"(", "\xC2\xAB"}) {
    ReplaceAll(&text, std::string(open) + " ", open);
  }
  return text;
}

// Reproduces ukr.utils.reorder: within each `tokens ` chunk, a tagger may
// emit fields in reverse order marked with ">>" (e.g. time minutes before
// hours); swap them back into canonical order.
std::string Reorder(const std::string& tagged) {
  static const std::regex kPattern("(\\w+: \".*?\")>> (\\w+: \".*\")");

  // Split on the literal "tokens " separator, transform each chunk.
  const std::string sep = "tokens ";
  std::vector<std::string> chunks;
  size_t pos = 0;
  while (true) {
    size_t next = tagged.find(sep, pos);
    if (next == std::string::npos) {
      chunks.push_back(tagged.substr(pos));
      break;
    }
    chunks.push_back(tagged.substr(pos, next - pos));
    pos = next + sep.size();
  }

  std::ostringstream joined;
  for (size_t i = 0; i < chunks.size(); ++i) {
    if (i > 0) joined << sep;
    std::smatch match;
    if (std::regex_search(chunks[i], match, kPattern)) {
      const std::string original = match[1].str() + ">> " + match[2].str();
      const std::string reordered = match[2].str() + " " + match[1].str();
      std::string chunk = chunks[i];
      chunk.replace(chunk.find(original), original.size(), reordered);
      joined << chunk;
    } else {
      joined << chunks[i];
    }
  }
  return joined.str();
}

std::unique_ptr<StdConstFst> LoadFst(const std::string& path,
                                    std::string* error) {
  std::unique_ptr<StdVectorFst> f(StdVectorFst::Read(path));
  if (!f) {
    if (error) *error = "failed to load FST from " + path;
    return nullptr;
  }
  if (f->Start() == fst::kNoStateId) {
    if (error) *error = "FST has no start state: " + path;
    return nullptr;
  }
  for (fst::StateIterator<StdVectorFst> states(*f); !states.Done();
       states.Next()) {
    const auto state = states.Value();
    for (fst::ArcIterator<StdVectorFst> arcs(*f, state); !arcs.Done();
         arcs.Next()) {
      const auto& arc = arcs.Value();
      if (arc.ilabel < 0 || arc.ilabel > 255 || arc.olabel < 0 ||
          arc.olabel > 255) {
        if (error) {
          *error = "FST contains a non-byte label at state " +
                   std::to_string(state) + ": " + path;
        }
        return nullptr;
      }
    }
  }
  // Compose() needs one side arc-sorted; sort the rule on input labels once.
  if ((f->Properties(fst::kILabelSorted, true) & fst::kILabelSorted) == 0) {
    fst::ArcSort(f.get(), fst::ILabelCompare<StdArc>());
  }
  return std::make_unique<StdConstFst>(*f);
}

}  // namespace

InverseNormalizer::InverseNormalizer(
    std::unique_ptr<StdConstFst> tagger,
    std::unique_ptr<StdConstFst> verbalizer)
    : tagger_(std::move(tagger)), verbalizer_(std::move(verbalizer)) {}

std::unique_ptr<InverseNormalizer> InverseNormalizer::FromFiles(
    const std::string& tagger_path, const std::string& verbalizer_path,
    std::string* error) {
  // Copy paths before writing `error`, so even unusual aliased arguments are
  // handled deterministically.
  const std::string tagger_file = tagger_path;
  const std::string verbalizer_file = verbalizer_path;
  std::string load_error;
  auto tagger = LoadFst(tagger_file, &load_error);
  if (!tagger) {
    if (error) *error = std::move(load_error);
    return nullptr;
  }
  auto verbalizer = LoadFst(verbalizer_file, &load_error);
  if (!verbalizer) {
    if (error) *error = std::move(load_error);
    return nullptr;
  }
  auto normalizer = std::unique_ptr<InverseNormalizer>(
      new InverseNormalizer(std::move(tagger), std::move(verbalizer)));
  if (error) error->clear();
  return normalizer;
}

bool InverseNormalizer::Normalize(const std::string& text, std::string* output,
                                  std::string* error) const {
  if (!output) {
    if (error) *error = "output must not be null";
    return false;
  }

  std::string whitespace_normalized;
  std::string detail;
  if (!NormalizeWhitespace(text, &whitespace_normalized, &detail)) {
    if (error) *error = std::move(detail);
    return false;
  }
  const std::string prepared = SeparatePunctuation(whitespace_normalized);
  OrthographyRestorations orthography_restorations;
  const std::string canonical =
      CanonicalizeOrthography(prepared, &orthography_restorations);
  std::string tagged;
  if (!RewriteShortestPath(*tagger_, canonical, &tagged, &detail)) {
    if (error) {
      *error = detail.empty() ? "tagger grammar does not accept the input"
                              : "tagger rewrite failed: " + detail;
    }
    return false;
  }
  tagged = Reorder(tagged);
  RestoreWordOrthography(orthography_restorations, &tagged);
  std::string verbalized;
  detail.clear();
  if (!RewriteShortestPath(*verbalizer_, tagged, &verbalized, &detail)) {
    if (error) {
      *error = detail.empty() ? "verbalizer grammar does not accept the input"
                              : "verbalizer rewrite failed: " + detail;
    }
    return false;
  }
  *output = AttachPunctuation(std::move(verbalized));
  if (error && error != output) error->clear();
  return true;
}

std::string InverseNormalizer::NormalizeOrPassthrough(
    const std::string& text) const {
  std::string output;
  return Normalize(text, &output) ? output : text;
}

}  // namespace ukr_itn
