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

or from pypi:

```bash
$ pip install symbolator-python
```

### Generate Symbols

If you just want to generate ELF symbols (pyelftools) for a library, you can do:

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

Currently the default output is in ASP for [clingo](https://potassco.org/clingo/) because this is what we need.
If you want json output:

```bash
$ symbolator generate --json libtcl8.6.so
```

### Compare Libraries (compare)

If you have two libraries of different versions, a simple comparison will just determine
if any symbols or arguments have changed. Again we will use pyelftools for the symbol
extraction. To do this, we just need the "same" library
of two different versions. Let's first make the examples:

```bash
$ cd examples/cpp
$ make
```

to generate:

 - libmath-v1.so: an original library
 - libmath-v2.so: a changed library

Now let's run compare:

```bash
$ symbolator compare libmath-v1.so libmath-v2.so
```
```
...
{
    "is_libA": [
        "/home/vanessa/Desktop/Code/symbolator/examples/cpp/libmath-v1.so"
    ],
    "is_libB": [
        "/home/vanessa/Desktop/Code/symbolator/examples/cpp/libmath-v2.so"
    ],
    "symbol_is_missing": [
        "/home/vanessa/Desktop/Code/symbolator/examples/cpp/libmath-v1.so",
        "/home/vanessa/Desktop/Code/symbolator/examples/cpp/libmath-v2.so",
        "MathLibrary.cpp"
    ],
    "corpus_name_changed": [
        "/home/vanessa/Desktop/Code/symbolator/examples/cpp/libmath-v1.so",
        "/home/vanessa/Desktop/Code/symbolator/examples/cpp/libmath-v2.so",
        "libmath-v1.so",
        "libmath-v2.so"
    ]
}
```

Or again just the json:

```
$ symbolator compare libmath-v1.so libmath-v2.so --json
```

### Assess Compatibility (compat)

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
$ symbolator compat math-client libmath-v1.so libmath-v2.so
% binary           : math-client
% working library  : libmath-v1.so
% contender library: libmath-v2.so
Missing Symbol Count: 1
Missing Symbols:
['math-client', 'libmath-v2.so', '_ZN11MathLibrary10Arithmetic3AddEdd']
```

Note that this is the right answer for the example - we are missing that symbol!
By default this uses [is_compatible.lp](symbolator/facts/is_compatible.lp)
If you just want to dump symbols to use with some other logic program you
can do:

```bash
$ symbolator compat --dump math-client libmath-v1.so libmath-v2.so
```

Or to get json of just the answer:

```bash
$ symbolator compat --json math-client libmath-v1.so libmath-v2.so 
{
    "binary": "/home/vanessa/Desktop/Code/symbolator/examples/cpp/math-client",
    "library_working": "/home/vanessa/Desktop/Code/symbolator/examples/cpp/libmath-v1.so",
    "library_contender": "/home/vanessa/Desktop/Code/symbolator/examples/cpp/libmath-v2.so",
    "missing_symbols": [
        "/home/vanessa/Desktop/Code/symbolator/examples/cpp/math-client",
        "/home/vanessa/Desktop/Code/symbolator/examples/cpp/libmath-v2.so",
        "_ZN11MathLibrary10Arithmetic3AddEdd"
    ],
    "count_missing_symbols": "1"
}
```

Again, this is just using pyelftools to get the symbols directly from elf.

### Smeagle Stability Model

As of version 0.0.15, we have support to read in json output from [Smeagle](https://github.com/buildsi/Smeagle) or [gosmeagle](https://github.com/vsoch/gosmeagle) and then to to a more detailed stability model. Let's say we have two output files from smeagle,
such as in [examples/smeagle](examples/smeagle) generated with gosmeagle doing the following:

```bash
$ cd examples/cpp
$ make
$ cd ../smeagle
$ gosmeagle parse ../cpp/libmath-v1.so --pretty > libmath-v1.so.json
$ gosmeagle parse ../cpp/libmath-v2.so --pretty > libmath-v2.so.json
```

We can then run symbolator to use the json to do a stability test.

```bash
$ symbolator stability-test examples/smeagle/libmath-v1.so.json examples/smeagle/libmath-v2.so.json --detail
Libraries are not stable: 0 missing exports, 2 missing_imports

Missing Imports
---------------
 _ZN11MathLibrary10Arithmetic3AddEdd Basic %rdi 0
 _ZN11MathLibrary10Arithmetic3AddEdd Basic %rsi 0
```

This can be used programatically to get json output as well.

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
$ symbolator compat math-client libmath-v1.so libmath-v2.so 
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
