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

% A symbol is defined if some corpus has a value not UND
symbol_is_defined(Corpus, Symbol, Definition) 
    :- symbol_definition(Corpus, Symbol, Definition),
       Definition != "UND".

% A symbol is considered gloabally missing if: 
missing_symbols(Corpus, Symbol)

      % is it undefined for a corpus
      :- symbol_is_undefined(Corpus, Symbol),
      
      % And there is NO OTHER CORPUS that defines it
      not symbol_is_defined(_, Symbol, _).

#show missing_symbols/2.
