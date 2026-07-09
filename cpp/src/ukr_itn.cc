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
  std::string tagged;
  if (!RewriteShortestPath(*tagger_, text, &tagged)) {
    if (error) *error = "tagger grammar does not accept the input";
    return false;
  }
  tagged = Reorder(tagged);
  if (!RewriteShortestPath(*verbalizer_, tagged, output)) {
    if (error) *error = "verbalizer grammar does not accept: " + tagged;
    return false;
  }
  return true;
}

std::string InverseNormalizer::NormalizeOrPassthrough(
    const std::string& text) const {
  std::string output;
  return Normalize(text, &output) ? output : text;
}

}  // namespace ukr_itn
