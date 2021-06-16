# Symbolator

Symbolator is a small library that will allow you to assess if symbols are
compatible between a library and binary of interest. The goal is to create
a tester for [build-abi-containers](https://github.com/buildsi/build-abi-containers).

## Usage

### Install

You can install locally

```bash
$ git clone git@github.com:buildsi/symbolator.git
$ cd symbolator
$ pip install -e .
```

or from Pypi:

```bash
$ pip install symbolator-python
```

### Generate Symbols

If you just want to generate symbols for a library, you can do:

```bash
$ symbolator generate <library>
```

For example:

```bash
$ symbolator generate libtcl8.6.so 
...
symbol("socket@@GLIBC_2.2.5").
symbol_type("/home/vanessa/Desktop/Code/symbolator/libtcl8.6.so","socket@@GLIBC_2.2.5","FUNC").
symbol_version("/home/vanessa/Desktop/Code/symbolator/libtcl8.6.so","socket@@GLIBC_2.2.5","").
symbol_binding("/home/vanessa/Desktop/Code/symbolator/libtcl8.6.so","socket@@GLIBC_2.2.5","GLOBAL").
symbol_visibility("/home/vanessa/Desktop/Code/symbolator/libtcl8.6.so","socket@@GLIBC_2.2.5","DEFAULT").
symbol_definition("/home/vanessa/Desktop/Code/symbolator/libtcl8.6.so","socket@@GLIBC_2.2.5","UND").
has_symbol("/home/vanessa/Desktop/Code/symbolator/libtcl8.6.so","socket@@GLIBC_2.2.5").
has_symbol("/home/vanessa/Desktop/Code/symbolator/libtcl8.6.so","socket@@GLIBC_2.2.5").
```

If you want to include system symbols (libraries that are linked to this library of interest):

```bash
$ symbolator generate --system-libs libtcl8.6.so 
```

Currently the output is in ASP for [clingo](https://potassco.org/clingo/) because this is what we need.
Other output formats could be added if desired.

### Assess Compatibility

To assess compatibility, we will need:

1. a primary binary of interest
2. a library known to be working with this binary
3. a contender library we want to test

There are examples for different compilers in [examples](examples). For example,
let's build the example files for cpp.

```bash
$ cd examples/cpp
$ make
```

This will generate:

 - math-client: our main binary of interest
 - libmath-v1.so: a known working library
 - libmath-v2.so: a contender library

If you look at the example, the contender library should not be compatible
because there is a change in a parameter type. We might not see this for C
but we should see a different symbol (mangled string) for C++. To run
the test:

```bash
$ symbolator compare math-client libmath-v1.so libmath-v2.so
% binary           : math-client
% working library  : libmath-v1.so
% contender library: libmath-v2.so
Missing Symbol Count: 1
Missing Symbols:
['/home/vanessa/Desktop/Code/symbolator/examples/cpp/math-client', '/home/vanessa/Desktop/Code/symbolator/examples/cpp/libmath-v2.so', '_ZN11MathLibrary10Arithmetic3AddEdd']
```

Note that this is the right answer for the example - we are missing that symbol!
By default this uses [is_compatible.lp](symbolator/facts/is_compatible.lp)
If you just want to dump symbols to use with some other logic program you
can do:

```bash
$ symbolator compare --dump math-client libmath-v1.so libmath-v2.so
```

### Container Install

You can also build symbolator into a container!

```bash
$ docker build -t symbolator .
```

And then interact with symbolator either via the entrypoint or a shell.

```
# shell
$ docker run --entrypoint bash -it symbolator

# entrypoint
$ docker run -it symbolator
```

The examples are built into the container for easy testing.

```bash
$ cd examples/cpp
$ symbolator compare math-client libmath-v1.so libmath-v2.so 
% binary           : math-client
% working library  : libmath-v1.so
% contender library: libmath-v2.so
Compatible
```

### Examples

The [examples](examples) folder has code for several different compilers
you can test.

 - **g++**
 - **gcc**
 - **gcc-10**
 - **icc**
 - **icpc**
 - **clang**
 - **clang-10**
 - **clang++**  
 
 
### License

This project is part of Spack. Spack is distributed under the terms of both the MIT license and the Apache License (Version 2.0). Users may choose either license, at their option.

All new contributions must be made under both the MIT and Apache-2.0 licenses.

See LICENSE-MIT, LICENSE-APACHE, COPYRIGHT, and NOTICE for details.

SPDX-License-Identifier: (Apache-2.0 OR MIT)

LLNL-CODE-811652
