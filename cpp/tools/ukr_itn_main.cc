// Command-line ITN: reads sentences from stdin, one per line.
//
//   ukr_itn_cli <grammar_dir>
//   ukr_itn_cli <tagger.fst> <verbalizer.fst>

#include <iostream>
#include <string>

#include "ukr_itn/ukr_itn.h"

int main(int argc, char** argv) {
  std::string tagger_path, verbalizer_path;
  if (argc == 2) {
    tagger_path = std::string(argv[1]) + "/ukr_itn_tagger.fst";
    verbalizer_path = std::string(argv[1]) + "/ukr_itn_verbalizer.fst";
  } else if (argc == 3) {
    tagger_path = argv[1];
    verbalizer_path = argv[2];
  } else {
    std::cerr << "usage: " << argv[0]
              << " <grammar_dir> | <tagger.fst> <verbalizer.fst>\n"
              << "Grammars are produced by `python -m ukr.export`.\n";
    return 2;
  }

  std::string error;
  auto normalizer =
      ukr_itn::InverseNormalizer::FromFiles(tagger_path, verbalizer_path, &error);
  if (!normalizer) {
    std::cerr << "error: " << error << "\n";
    return 1;
  }

  int status = 0;
  std::string line;
  while (std::getline(std::cin, line)) {
    if (line.empty()) continue;
    std::string output;
    if (normalizer->Normalize(line, &output, &error)) {
      std::cout << output << "\n";
    } else {
      std::cerr << "error: could not normalize \"" << line << "\": " << error
                << "\n";
      status = 1;
    }
  }
  return status;
}
