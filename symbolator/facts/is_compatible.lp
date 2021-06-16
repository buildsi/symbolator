%=============================================================================
% This logic program shows what symbols are compatible. Eventually we
% can move different rules into different files (symbols, variables, etc.)
%=============================================================================

%=============================================================================
% Matching function and variable symbols
% symbols are missing if they are needed (present in the working library),
% not undefined in the working library (indicating they come from elsewhere)
% and undefined in both the potential library and binary.
%=============================================================================

% A symbol is undefined in this case.
symbol_is_undefined(Corpus, Symbol) :- symbol_definition(Corpus, Symbol, "UND").

% A symbol is hidden in this case (is this useful?)
% This rule is not in use yet
% symbol_is_hidden(Corpus, Symbol) :- symbol_visibility(Corpus, Symbol, "HIDDEN").

% we can ignore a symbol in the library that is known to work (the subset of 
% "needed symbols" if it is undefined). The logic here is that if the main app
% linking with this library works, even if both are undefined, then the symbol
% must be provided by another library

% a symbol is known to be needed if
known_needed_symbol(Symbol)

    % it's present in a linked library that we know towork
    :- needed_symbol(Symbol),

    % and it's not undefined. If a symbol is undefined and still works,
    % we arguably don't care.
    not needed_symbol_definition(_, Symbol, "UND").

% Shared rule for both cases of missing symbol. We have two to express an OR
known_needed_symbol_undefined(CorpusA, CorpusB, Symbol)

   % set CorpusA to be main, CorpusB to be linked library
   :- is_main(CorpusA),
      is_library(CorpusB),

      % it's a known needed symbol
      known_needed_symbol(Symbol),

      % it is undefined in the main binary
      symbol_is_undefined(CorpusA, Symbol).


% A symbol is considered missing for main if: 
missing_symbols(CorpusA, CorpusB, Symbol)

      % a known needed symbol is undefined
      :- known_needed_symbol_undefined(CorpusA, CorpusB, Symbol),

      % it is undefined in the second lib we want to link
      symbol_is_undefined(CorpusB, Symbol).

% OR

% A symbol is considered missing for main if: 
missing_symbols(CorpusA, CorpusB, Symbol)

   % a known needed symbol is undefined
   :- known_needed_symbol_undefined(CorpusA, CorpusB, Symbol),

      % it is not present in the second library
      not has_symbol(CorpusB, Symbol).


% TODO how to enforce unique?
get_missing_symbols(S) :- missing_symbols(_, _, S).
count_missing_symbols(N) :- #count{X:get_missing_symbols(X)} = K, K=N.

%=============================================================================
% Matching soname and architecture
% libraries must have matching soname and architecture
%=============================================================================

% libabigail just compares the libs, but why not compare to the binary too?
%shared_architecture(CorpusA, CorpusB)
%  :- corpus_elf_machine(CorpusA, _, A)
get_architecture(A) :- corpus_elf_machine(_, A).
architecture_count(N) :- #count{X:get_architecture(X)} = K, K=N.


% Check for the number of parameters the same 
% First write a general rule to find formal parameters
% We want to find shared parameters (via symbols) between main and library
% the library can have extra symbols main doesn't use, and we don't care.
shared_symbols(CorpusA, CorpusB, Symbol)

    % set main and the library
    :- is_main(CorpusA),
       is_library(CorpusB),
       
       % ensure the symbol is present in both
       has_symbol(CorpusA, Symbol),    
       has_symbol(CorpusB, Symbol).

% Now that we have the shared symbols, just reduce to the names
is_shared_symbol(Symbol) :- shared_symbols(_,_,Symbol).

% Are the two compatible?
are_compatible()

  % there are no missing symbols
  :- count_missing_symbols(N) == 0.

  % there is only one architecture
  :- architecture_count(N) == 1.
  
#show is_main/1.
#show is_library/1.
#show is_needed/1.
#show missing_symbols/3.
#show get_architecture/1.
#show architecture_count/1.
#show count_missing_symbols/1.
