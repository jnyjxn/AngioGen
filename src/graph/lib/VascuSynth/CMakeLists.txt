PROJECT( VascuSynth )
cmake_minimum_required(VERSION 2.8)

set(vascusynth_files
	lib/VascuSynth.cpp lib/SupplyMap.cpp lib/OxygenationMap.cpp lib/NodeTable.cpp lib/VascularTree.cpp lib/Complicator.cpp
	lib/SupplyMap.h lib/OxygenationMap.h lib/NodeTable.h lib/VascularTree.h lib/Complicator.h
)
set(CMAKE_BUILD_TYPE Debug)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS}")

ADD_EXECUTABLE(${PROJECT_NAME} ${vascusynth_files})
TARGET_LINK_LIBRARIES( VascuSynth )
