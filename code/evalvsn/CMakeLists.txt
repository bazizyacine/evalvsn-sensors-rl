cmake_minimum_required(VERSION 3.5)
project(evalvsn CXX)

# Debug unless asked otherwise: the encodings of the article were produced by
# a Debug build, and a different optimisation level may round the DCT
# differently.
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Debug CACHE STRING "Build type" FORCE)
endif()

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -std=gnu++0x")

find_package(OpenCV REQUIRED)

add_executable(evalvsn
    src/evalvsn.cc
    src/params.cc
    src/video.cc
    src/frame.cc
    src/dct.cc
    src/quantification.cc
    src/zigzag.cc
    src/priority.cc
    src/rle.cc
    src/golomb.cc
    src/bits.cc
    src/packet.cc
    src/trace.cc
    src/evaluate.cc)
set_target_properties(evalvsn PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
target_link_libraries(evalvsn ${OpenCV_LIBS})
