cmake_minimum_required(VERSION 3.16)
project(bhl_op4_speedrun LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(sr_core STATIC src/speedrun/sr_core.cpp)
target_include_directories(sr_core PUBLIC src/speedrun)
target_compile_options(sr_core PRIVATE -Wall -Wextra -Wpedantic)

add_executable(speedrun_test tests/cpp/test_speedrun.cpp)
target_link_libraries(speedrun_test PRIVATE sr_core)
target_compile_options(speedrun_test PRIVATE -Wall -Wextra -Wpedantic)

enable_testing()
add_test(NAME speedrun_core COMMAND speedrun_test)
