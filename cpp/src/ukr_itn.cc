#include "ukr_itn/ukr_itn.h"

#include <regex>
#include <sstream>
#include <vector>

namespace ukr_itn {
namespace {

using fst::StdArc;
using fst::StdVectorFst;

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
bool RewriteShortestPath(const StdVectorFst& rule, const std::string& input,
                         std::string* output) {
  StdVectorFst lattice;
  fst::Compose(MakeByteAcceptor(input), rule, &lattice);
  if (lattice.Start() == fst::kNoStateId) return false;

  StdVectorFst best;
  fst::ShortestPath(lattice, &best);
  if (best.Start() == fst::kNoStateId) return false;

  output->clear();
  for (auto state = best.Start(); state != fst::kNoStateId;) {
    fst::ArcIterator<StdVectorFst> aiter(best, state);
    if (aiter.Done()) break;  // reached the final state
    const auto& arc = aiter.Value();
    if (arc.olabel != 0) output->push_back(static_cast<char>(arc.olabel));
    state = arc.nextstate;
  }
  return true;
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

std::unique_ptr<StdVectorFst> LoadFst(const std::string& path,
                                      std::string* error) {
  std::unique_ptr<StdVectorFst> f(StdVectorFst::Read(path));
  if (!f) {
    if (error) *error = "failed to load FST from " + path;
    return nullptr;
  }
  // Compose() needs one side arc-sorted; sort the rule on input labels once.
  fst::ArcSort(f.get(), fst::ILabelCompare<StdArc>());
  return f;
}

}  // namespace

InverseNormalizer::InverseNormalizer(
    std::unique_ptr<StdVectorFst> tagger,
    std::unique_ptr<StdVectorFst> verbalizer)
    : tagger_(std::move(tagger)), verbalizer_(std::move(verbalizer)) {}

std::unique_ptr<InverseNormalizer> InverseNormalizer::FromFiles(
    const std::string& tagger_path, const std::string& verbalizer_path,
    std::string* error) {
  auto tagger = LoadFst(tagger_path, error);
  if (!tagger) return nullptr;
  auto verbalizer = LoadFst(verbalizer_path, error);
  if (!verbalizer) return nullptr;
  return std::unique_ptr<InverseNormalizer>(
      new InverseNormalizer(std::move(tagger), std::move(verbalizer)));
}

bool InverseNormalizer::Normalize(const std::string& text, std::string* output,
                                  std::string* error) const {
  const std::string prepared = SeparatePunctuation(text);
  std::string tagged;
  if (!RewriteShortestPath(*tagger_, prepared, &tagged)) {
    if (error) *error = "tagger grammar does not accept the input";
    return false;
  }
  tagged = Reorder(tagged);
  if (!RewriteShortestPath(*verbalizer_, tagged, output)) {
    if (error) *error = "verbalizer grammar does not accept: " + tagged;
    return false;
  }
  *output = AttachPunctuation(*output);
  return true;
}

std::string InverseNormalizer::NormalizeOrPassthrough(
    const std::string& text) const {
  std::string output;
  return Normalize(text, &output) ? output : text;
}

}  // namespace ukr_itn
