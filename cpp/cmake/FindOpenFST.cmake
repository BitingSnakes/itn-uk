find_path(OpenFST_INCLUDE_DIR
  NAMES fst/fstlib.h
  HINTS /opt/homebrew/include /usr/local/include /usr/include)
find_library(OpenFST_LIBRARY
  NAMES fst
  HINTS /opt/homebrew/lib /usr/local/lib /usr/lib)

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(OpenFST
  REQUIRED_VARS OpenFST_LIBRARY OpenFST_INCLUDE_DIR)

if(OpenFST_FOUND AND NOT TARGET OpenFST::fst)
  add_library(OpenFST::fst UNKNOWN IMPORTED)
  set_target_properties(OpenFST::fst PROPERTIES
    IMPORTED_LOCATION "${OpenFST_LIBRARY}"
    INTERFACE_INCLUDE_DIRECTORIES "${OpenFST_INCLUDE_DIR}")
endif()

mark_as_advanced(OpenFST_INCLUDE_DIR OpenFST_LIBRARY)
