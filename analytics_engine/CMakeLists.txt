cmake_minimum_required(VERSION 3.14)
project(AnalyticsEngine VERSION 1.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# We will need threads
find_package(Threads REQUIRED)

# Manual includes for GCC 6.3 stability
include_directories(include)
include_directories(external) # for httplib.h
include_directories(external/json/include)

# Win32 socket libs
if(WIN32)
    set(EXTRA_LIBS ws2_32 mswsock iphlpapi)
endif()

add_executable(analytics_engine
    src/main.cpp
    src/ThreadPool.cpp
    src/KVStore.cpp
    src/WAL.cpp
    src/Inference.cpp
)

target_link_libraries(analytics_engine PRIVATE
    Threads::Threads
    ${EXTRA_LIBS}
)
