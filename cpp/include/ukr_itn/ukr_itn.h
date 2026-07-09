// C++ Inverse Text Normalization for Ukrainian using OpenFST.
//
// Consumes the grammars exported from the Python package with
// `python -m ukr.export` and reproduces the same pipeline:
// tag -> reorder -> verbalize, taking the shortest path at each step.

#ifndef UKR_ITN_UKR_ITN_H_
#define UKR_ITN_UKR_ITN_H_

#include <memory>
#include <string>

#include <fst/fstlib.h>

namespace ukr_itn {

class InverseNormalizer {
 public:
  // Loads the tagger and verbalizer grammars from OpenFST binary files
  // (ukr_itn_tagger.fst / ukr_itn_verbalizer.fst). Returns nullptr and
  // fills *error on failure.
  static std::unique_ptr<InverseNormalizer> FromFiles(
      const std::string& tagger_path, const std::string& verbalizer_path,
      std::string* error = nullptr);

  // Normalizes a UTF-8 sentence, e.g.
  //   "двадцять дві тисячі сто один" -> "22101".
  // Returns false (and fills *error) if the input is not valid UTF-8 or the
  // grammar cannot parse it. `output` must not be null.
  bool Normalize(const std::string& text, std::string* output,
                 std::string* error = nullptr) const;

  // Convenience wrapper: returns the input unchanged if it cannot be parsed.
  std::string NormalizeOrPassthrough(const std::string& text) const;

 private:
  InverseNormalizer(std::unique_ptr<fst::StdConstFst> tagger,
                    std::unique_ptr<fst::StdConstFst> verbalizer);

  // ConstFst is immutable and documented by OpenFST as thread-safe.
  std::unique_ptr<fst::StdConstFst> tagger_;
  std::unique_ptr<fst::StdConstFst> verbalizer_;
};

}  // namespace ukr_itn

#endif  // UKR_ITN_UKR_ITN_H_
