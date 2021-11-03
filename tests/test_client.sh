#!/bin/bash

# Include help functions
. helpers.sh

echo
echo "************** START: test_client.sh **********************"

# Create temporary testing directory
echo "Creating temporary directory to work in."
tmpdir=$(mktemp -d)
output=$(mktemp ${tmpdir:-/tmp}/symbolator_test.XXXXXX)

echo "Testing help commands..."

# Test help for all commands
for command in version splice stability-test compare compat generate;
    do
    runTest 0 $output symbolator $command --help 
done

# Compile test libraries
printf "Compiling test libraries."
here=$PWD
cd ../examples/cpp
export LD_LIBRARY_PATH=$PWD
make
cd $here

# set the watchme base, create watcher
echo "#### Testing symbolator generate"
runTest 0 $output symbolator generate ../examples/cpp/libmath-v1.so
runTest 0 $output symbolator generate ../examples/cpp/libmath-v1.so --json
runTest 0 $output symbolator generate --system-libs ../examples/cpp/math-client

echo "#### Testing symbolator compare"
runTest 0 $output symbolator compare ../examples/cpp/libmath-v1.so ../examples/cpp/libmath-v2.so
runTest 0 $output symbolator compare --json ../examples/cpp/libmath-v1.so ../examples/cpp/libmath-v2.so

echo "#### Testing symbolator compat"
runTest 0 $output symbolator compat ../examples/cpp/math-client ../examples/cpp/libmath-v1.so ../examples/cpp/libmath-v2.so
runTest 0 $output symbolator compat --json ../examples/cpp/math-client ../examples/cpp/libmath-v1.so ../examples/cpp/libmath-v2.so
runTest 0 $output symbolator compat --dump ../examples/cpp/math-client ../examples/cpp/libmath-v1.so ../examples/cpp/libmath-v2.so

echo "#### Testing smeagle stability"
runTest 0 $output symbolator stability-test ../examples/smeagle/libmath-v1.so.json ../examples/smeagle/libmath-v2.so.json --detail

echo "#### Testing smeagle splice"
runTest 0 $output symbolator splice ../examples/cpp/math-client
runTest 0 $output symbolator splice --json ../examples/cpp/math-client
runTest 0 $output symbolator splice ../examples/cpp/math-client -s libmath-v1.so=../examples/cpp/libmath-v2.so

echo "#### Testing smeagle jsonsplice"
runTest 0 $output symbolator jsonsplice ../examples/splice/math-client.json
runTest 0 $output symbolator jsonsplice --json ../examples/splice/math-client.json
runTest 0 $output symbolator jsonsplice ../examples/splice/math-client.json -s libmath-v1.so=../examples/splice/libmath-v2.so.json

echo "Finish testing basic client"
rm -rf ${tmpdir}
