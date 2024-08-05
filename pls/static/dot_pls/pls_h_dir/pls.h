#pragma once

#ifndef PLS_INSTRUMENTATION

#define PLS_JOIN_HELPER(a,b) a##b
#define PLS_JOIN(a,b) PLS_JOIN_HELPER(a,b)

#define PLS_PROJECT(name) \
  constexpr static char const* const PLS_JOIN(kPlsString,__COUNTER__) = name;

#define PLS_IMPORT(lib,repo) \
  constexpr static char const* const PLS_JOIN(kPlsString,__COUNTER__) = lib; \
  constexpr static char const* const PLS_JOIN(kPlsString,__COUNTER__) = repo;

#else  // PLS_INSTRUMENTATION

#define PLS_PROJECT(name) PLS_INSTRUMENTATION_OUTPUT{"pls_project":name}
#define PLS_IMPORT(lib,repo) PLS_INSTRUMENTATION_OUTPUT{"pls_import":{"lib":lib,"repo":repo}}

#endif  // PLS_INSTRUMENTATION
