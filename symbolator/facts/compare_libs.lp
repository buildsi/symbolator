%=============================================================================
% This logic program shows what symbols are missing or changed
%=============================================================================

% Corpus B is missing the symbol
symbol_is_missing(CorpusA, CorpusB, Symbol) :-
    symbol(Symbol),
    is_libA(CorpusA),
    is_libB(CorpusB),
    has_symbol(CorpusA, Symbol),
    not has_symbol(CorpusB, Symbol).        

% Corpus A is missing the symbol
symbol_is_missing(CorpusA, CorpusB, Symbol) :-
    symbol(Symbol),
    is_libA(CorpusA),
    is_libB(CorpusB),
    has_symbol(CorpusB, Symbol),
    not has_symbol(CorpusA, Symbol).        

% The symbol definition has changed
symbol_definition_changed(CorpusA, CorpusB, Symbol, DefinitionA, DefinitionB) :-
    symbol(Symbol),
    is_libA(CorpusA),
    is_libB(CorpusB),
    has_symbol(CorpusB, Symbol),
    has_symbol(CorpusA, Symbol),
    symbol_definition(CorpusA, Symbol, DefinitionA),
    symbol_definition(CorpusB, Symbol, DefinitionB),
    DefinitionA != DefinitionB.

% The symbol type has changed
symbol_type_changed(CorpusA, CorpusB, Symbol, TypeA, TypeB) :-
    symbol(Symbol),
    is_libA(CorpusA),
    is_libB(CorpusB),
    has_symbol(CorpusB, Symbol),
    has_symbol(CorpusA, Symbol),
    symbol_type(CorpusA, Symbol, TypeA),
    symbol_type(CorpusB, Symbol, TypeB),
    TypeA != TypeB.

% The symbol visibility has changed
symbol_visibility_changed(CorpusA, CorpusB, Symbol, VisA, VisB) :-
    symbol(Symbol),
    is_libA(CorpusA),
    is_libB(CorpusB),
    has_symbol(CorpusB, Symbol),
    has_symbol(CorpusA, Symbol),
    symbol_visibility(CorpusA, Symbol, VisA),
    symbol_visibility(CorpusB, Symbol, VisB),
    VisA != VisB.

% The symbol binding has changed
symbol_binding_changed(CorpusA, CorpusB, Symbol, BindA, BindB) :-
    symbol(Symbol),
    is_libA(CorpusA),
    is_libB(CorpusB),
    has_symbol(CorpusB, Symbol),
    has_symbol(CorpusA, Symbol),
    symbol_binding(CorpusA, Symbol, BindA),
    symbol_binding(CorpusB, Symbol, BindB),
    BindA != BindB.

% The symbol version has changed
symbol_version_changed(CorpusA, CorpusB, Symbol, VerA, VerB) :-
    symbol(Symbol),
    is_libA(CorpusA),
    is_libB(CorpusB),
    has_symbol(CorpusB, Symbol),
    has_symbol(CorpusA, Symbol),
    symbol_version(CorpusA, Symbol, VerA),
    symbol_version(CorpusB, Symbol, VerB),
    VerA != VerB.

% Compare corpora metadata
elf_class_changed(CorpusA, CorpusB, ClassA, ClassB) :-
    is_libA(CorpusA),
    is_libB(CorpusB),
    corpus_elf_class(CorpusA, ClassA),
    corpus_elf_class(CorpusB, ClassB),
    ClassA != ClassB.

elf_data_encoding_changed(CorpusA, CorpusB, A, B) :-
    is_libA(CorpusA),
    is_libB(CorpusB),
    corpus_data_encoding(CorpusA, A),
    corpus_data_encoding(CorpusB, B),
    A != B.

corpus_name_changed(CorpusA, CorpusB, NameA, NameB) :-
    is_libA(CorpusA),
    is_libB(CorpusB),
    corpus_name(CorpusA, NameA),
    corpus_name(CorpusB, NameB),
    NameA != NameB.

corpus_file_version_changed(CorpusA, CorpusB, A, B) :-
    is_libA(CorpusA),
    is_libB(CorpusB),
    corpus_file_version(CorpusA, A),
    corpus_file_version(CorpusB, B),
    A != B.

corpus_elf_osabi_changed(CorpusA, CorpusB, A, B) :-
    is_libA(CorpusA),
    is_libB(CorpusB),
    corpus_elf_osabi(CorpusA, A),
    corpus_elf_osabi(CorpusB, B),
    A != B.

corpus_abiversion_changed(CorpusA, CorpusB, A, B) :-
    is_libA(CorpusA),
    is_libB(CorpusB),
    corpus_abiversion(CorpusA, A),
    corpus_abiversion(CorpusB, B),
    A != B.

corpus_elf_type_changed(CorpusA, CorpusB, A, B) :-
    is_libA(CorpusA),
    is_libB(CorpusB),
    corpus_elf_type(CorpusA, A),
    corpus_elf_type(CorpusB, B),
    A != B.

corpus_elf_machine_changed(CorpusA, CorpusB, A, B) :-
    is_libA(CorpusA),
    is_libB(CorpusB),
    corpus_elf_machine(CorpusA, A),
    corpus_elf_machine(CorpusB, B),
    A != B.

corpus_elf_version_changed(CorpusA, CorpusB, A, B) :-
    is_libA(CorpusA),
    is_libB(CorpusB),
    corpus_elf_version(CorpusA, A),
    corpus_elf_version(CorpusB, B),
    A != B.
  
  
#show is_libA/1.
#show is_libB/1.
#show symbol_is_missing/3.
#show symbol_version_changed/5.
#show symbol_visibility_changed/5.
#show symbol_binding_changed/5.
#show symbol_definition_changed/5.
#show symbol_type_changed/5.
#show elf_class_changed/4.
#show corpus_name_changed/4.
#show elf_data_encoding_changed/4.
#show corpus_file_version_changed/4.
#show corpus_elf_osabi_changed/4.
#show corpus_abiversion_changed/4.
#show corpus_elf_type_changed/4.
#show corpus_elf_machine_changed/4.
#show corpus_elf_version_changed/4.
