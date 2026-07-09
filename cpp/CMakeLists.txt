cmake_minimum_required(VERSION 3.16)
project(ukr_itn VERSION 0.1.9 LANGUAGES CXX)

include(CTest)
include(CMakePackageConfigHelpers)
include(GNUInstallDirs)

option(UKR_ITN_BUILD_CLI "Build the ukr_itn command-line tool" ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
find_package(OpenFST REQUIRED)

add_library(ukr_itn src/ukr_itn.cc)
add_library(ukr_itn::ukr_itn ALIAS ukr_itn)
target_compile_features(ukr_itn PUBLIC cxx_std_17)
set_target_properties(ukr_itn PROPERTIES
  CXX_EXTENSIONS OFF
  POSITION_INDEPENDENT_CODE ON
  VERSION ${PROJECT_VERSION}
  SOVERSION ${PROJECT_VERSION_MAJOR})
target_include_directories(ukr_itn PUBLIC
  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
  $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>)
target_link_libraries(ukr_itn PUBLIC OpenFST::fst)

if(UKR_ITN_BUILD_CLI)
  add_executable(ukr_itn_cli tools/ukr_itn_main.cc)
  target_compile_features(ukr_itn_cli PRIVATE cxx_std_17)
  set_target_properties(ukr_itn_cli PROPERTIES CXX_EXTENSIONS OFF)
  target_link_libraries(ukr_itn_cli PRIVATE ukr_itn::ukr_itn)
endif()

if(BUILD_TESTING)
  add_executable(ukr_itn_test tests/ukr_itn_test.cc)
  target_compile_features(ukr_itn_test PRIVATE cxx_std_17)
  set_target_properties(ukr_itn_test PROPERTIES CXX_EXTENSIONS OFF)
  target_link_libraries(ukr_itn_test PRIVATE ukr_itn::ukr_itn)
  add_test(NAME ukr_itn_test COMMAND ukr_itn_test)
endif()

install(TARGETS ukr_itn
  EXPORT ukr_itnTargets
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
if(UKR_ITN_BUILD_CLI)
  install(TARGETS ukr_itn_cli RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR})
endif()
install(DIRECTORY include/ DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})

configure_package_config_file(
  cmake/ukr_itnConfig.cmake.in
  "${CMAKE_CURRENT_BINARY_DIR}/ukr_itnConfig.cmake"
  INSTALL_DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/ukr_itn")
write_basic_package_version_file(
  "${CMAKE_CURRENT_BINARY_DIR}/ukr_itnConfigVersion.cmake"
  VERSION ${PROJECT_VERSION}
  COMPATIBILITY SameMajorVersion)

install(EXPORT ukr_itnTargets
  FILE ukr_itnTargets.cmake
  NAMESPACE ukr_itn::
  DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/ukr_itn")
install(FILES
  "${CMAKE_CURRENT_BINARY_DIR}/ukr_itnConfig.cmake"
  "${CMAKE_CURRENT_BINARY_DIR}/ukr_itnConfigVersion.cmake"
  cmake/FindOpenFST.cmake
  DESTINATION "${CMAKE_INSTALL_LIBDIR}/cmake/ukr_itn")
