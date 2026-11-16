cmake_minimum_required(VERSION 3.24)
project(GT4TraditionalChineseRunner LANGUAGES CXX)

set(GT4_DONOR "" CACHE PATH "Path to the pinned ps2-web-recomp checkout")
set(PS2_GENERATED "" CACHE PATH "Path to the translated SCAJ-30007 units")
if(NOT WIN32 OR NOT EXISTS "${PS2_GENERATED}/table.cpp")
    message(FATAL_ERROR "This runner requires Windows and translated SCAJ-30007 units")
endif()

find_package(Python3 REQUIRED COMPONENTS Interpreter)
find_package(SDL2 CONFIG REQUIRED)
add_subdirectory("${GT4_DONOR}" donor)

set(window_sources "${CMAKE_CURRENT_BINARY_DIR}/host")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS
    prepare_host.py "${GT4_DONOR}/host/main.cpp" "${GT4_DONOR}/host/window.cpp"
    "${GT4_DONOR}/host/window.hpp")
execute_process(
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/prepare_host.py"
        "${GT4_DONOR}" "${window_sources}"
    COMMAND_ERROR_IS_FATAL ANY)

add_executable(gt4-cht "${window_sources}/main.cpp" "${window_sources}/window.cpp")
target_compile_features(gt4-cht PRIVATE cxx_std_20)
target_compile_definitions(gt4-cht PRIVATE PS2_WINDOW SDL_MAIN_HANDLED)
target_link_libraries(gt4-cht PRIVATE ps2game SDL2::SDL2 psapi)
add_custom_command(TARGET gt4-cht POST_BUILD
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
        "$<TARGET_FILE:SDL2::SDL2>" "$<TARGET_FILE_DIR:gt4-cht>")
