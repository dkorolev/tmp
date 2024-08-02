#!/usr/bin/env python3

# REMAINS FOR v0.0.1 to be "complete":
# * Generate the `CMakeLists.txt` if not exists.
# * Provide the `pls.h` file by this tool.
# * Wrap each dependency into a singleton.
# * Basic tests, and a Github action running them.
# * During the call to `pls clean` it should not `git clone` anything; need to use some state/cache file!

# TODO(dkorolev): Test `--dotpls` for real.
# TODO(dkorolev): Should `.debug` and `.release` be symlinks to `.pls/.debug` and `.pls/.release`?
# TODO(dkorolev): CMAKE_BUILD_TYPE, NDEBUG, and test for these.
# TODO(dkorolev): Add `pls runwithcoredump` ?
# TODO(dkorolev): Check for broken symlinks, they need to be re-cloned.
# TODO(dkorolev): Figure out bash/zsh completion.

import os
import sys
import subprocess
import argparse
import json
from collections import deque
from collections import defaultdict

parser = argparse.ArgumentParser(description="PLS: The trivial build system for C++ and beyond, v0.01")
parser.add_argument("--verbose", "-v", action="store_true", help="Increase output verbosity")
parser.add_argument('--dotpls', type=str, default=".pls", help="The directory to use for output if not `./.pls`.")
flags, cmd = parser.parse_known_args()

cc_instrument_sh = f"{flags.dotpls}/cc_instrument.sh"
cc_instrument_sh_contents = """#!/bin/bash
g++ -D PLS_INSTRUMENTATION -E "$1" 2>/dev/null | grep PLS_INSTRUMENTATION_OUTPUT | sed 's/^PLS_INSTRUMENTATION_OUTPUT//g'
"""

git_clone_sh = f"{flags.dotpls}/cc_git_clone.sh"
cc_git_clone_sh_contents = """#!/bin/bash
SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
(cd "$SCRIPT_DIR"; mkdir -p deps)
(cd "$SCRIPT_DIR/deps"; git clone "$1" "$2")
"""

pls_h_dir = f"{flags.dotpls}/pls_h_dir"
pls_h = os.path.join(pls_h_dir, "pls.h")
# TODO(dkorolev): This is the ugly version of this file, gotta clean it up.
pls_h_contents = """#pragma once
#ifndef PLS_INSTRUMENTATION
#define PLS_JOIN_HELPER(a,b) a##b
#define PLS_JOIN(a,b) PLS_JOIN_HELPER(a,b)
#define PLS_IMPORT(lib,repo) \
constexpr static char const* const PLS_JOIN(kPlsImportLib,__COUNTER__) = lib; \
constexpr static char const* const PLS_JOIN(kPlsImportRepo,__COUNTER__) = repo;
#else
#define PLS_IMPORT(lib,repo) PLS_INSTRUMENTATION_OUTPUT{"pls_import":{"lib":lib,"repo":repo}}
#endif
"""

def pls_fail(msg):
  # TODO(dkorolev): Write the failure message to an env-provided file, for "unit"-testing `pls`.
  print(msg)
  sys.exit(1)

if os.path.isfile("pls.py") or os.path.isfile("pls"):
  pls_fail("PLS: You are probably running `pls` from the wrong directory. Navigate to your project directory first.")

modules = {}
executables = {}

# Support both projects with source files in `src/` and in the main project directory.
default_src_dirs = [".", "src"]

add_to_gitignores = defaultdict(list)

add_to_gitignores["."].append(flags.dotpls)
add_to_gitignores["."].append(".debug")
add_to_gitignores["."].append(".release")

def create_symlink_with_cmakelists_txt(src_dir, lib_name, lib_full_dir):
  # TODO(dkorolev): Creating the symlink should involve the `.gitignore` magic.
  desired_symlink_dir = os.path.join(src_dir, lib_name)
  if not os.path.isdir(desired_symlink_dir):
    os.symlink(lib_full_dir, desired_symlink_dir, target_is_directory=True)

already_traversed_src_dirs = set()
def traverse_source_tree(src_dirs=default_src_dirs):
  # TODO(dkorolev): Traverse recursively.
  # TODO(dkorolev): `libraries`? And a command to `run` them, if only with `objdump -s`?
  queue_list = deque()
  queue_set = set()
  for src_dir in src_dirs:
    queue_list.append(src_dir)
    queue_set.add(src_dir)
  while queue_list:
    src_dir = queue_list.popleft()
    if src_dir not in already_traversed_src_dirs and (src_dir == "." or os.path.isdir(src_dir)):
      libs_to_import = set()
      already_traversed_src_dirs.add(src_dir)
      pls_json_path = os.path.join(src_dir, "pls.json")
      if os.path.isfile(pls_json_path):
        pls_json = None
        with open(pls_json_path, "r") as file:
          try:
            pls_json = json.loads(file.read())
          except json.decoder.JSONDecodeError as e:
            pls_fail(f"PLS: Failed to parse `{pls_json_path}`: {e}.")
        if "import" in pls_json:
          for lib, repo in pls_json["import"].items():
            # TODO(dkorolev): Fail on branch mismatch.
            modules[lib] = repo
            libs_to_import.add(lib)
      for src_name in os.listdir(src_dir):
        if src_name.endswith(".cc"):
          executable_name = src_name.rstrip(".cc")
          executables[executable_name] = executable_name  # TODO(dkorolev): Support `module::example_binary` names.
          pls_commands = []
          full_src_name = os.path.join(src_dir, src_name)
          result = subprocess.run(["bash", cc_instrument_sh, full_src_name], capture_output=True, text=True)
          for line in result.stdout.split("\n"):
            stripped_line = line.rstrip(";").strip()
            if stripped_line:
              try:
                pls_commands.append(json.loads(stripped_line))
              except json.decoder.JSONDecodeError as e:
                pls_fail(f"PLS internal error: Can not parse `{stripped_line}` while processing `{full_src_name}`.")
          for pls_cmd in pls_commands:
            if "pls_import" in pls_cmd:
              pls_import = pls_cmd["pls_import"]
              if "lib" in pls_import and "repo" in pls_import:
                # TODO(dkorolev): Add branches. Fail if they do not match while installing the dependencies recursively.
                # TODO(dkorolev): Maybe create and add to `#include`-s path the `pls.h` file from this tool?
                # TODO(dkorolev): Variadic macro templates for branches.
                lib, repo = pls_import["lib"], pls_import["repo"]
                modules[lib] = repo
                libs_to_import.add(lib)
      for lib in libs_to_import:
        if lib not in queue_set:
          queue_list.append(lib)
          queue_set.add(lib)
          repo = modules[lib]
          lib_dir = f"{flags.dotpls}/deps/{lib}"
          if os.path.isdir(lib):
            if flags.verbose:
              print(f"PLS: Has symlink to `{lib}`, will use it.")
          else:
            if not os.path.isdir(lib_dir):
              if flags.verbose:
                print(f"PLS: Need to clone `{lib}` from `{repo}`.")
              result = subprocess.run(["bash", git_clone_sh, repo, lib])
              if result.returncode != 0:
                pls_fail(f"PLS: Clone of {repo} failed.")
              add_to_gitignores["."].append(lib)
            else:
              if flags.verbose:
                print(f"PLS: Has module `{lib}`, will use it.")
            if not os.path.isdir(lib_dir):
              pls_fail(f"PLS internal error: repl {repo} cloned into {lib}, but can not be located.")
            create_symlink_with_cmakelists_txt(".", lib, os.path.abspath(lib_dir))
            create_symlink_with_cmakelists_txt(src_dir, lib, os.path.abspath(lib_dir))

def update_dependencies():
  if os.path.isfile("CMakeLists.txt"):
    if flags.verbose:
      print("PLS: Has `CMakeLists.txt`, will use it.")
  else:
    if flags.verbose:
      print("PLS: No `CMakeLists.txt`, will generate it, and will add it to `.gitignore`.")
    add_to_gitignores["."].append("CMakeLists.txt")

  def apply_gitignore_changes():
    for gitignore_file_path, gitignore_lines in add_to_gitignores.items():
      gitignore_file = f"{gitignore_file_path}/.gitignore"
      skip_this_gitignore = False
      need_newline_in_gitignore = False
      all_lines = set(gitignore_lines)
      present = set()
      if os.path.isfile(gitignore_file):
        need_newline_in_gitignore = True
        with open(gitignore_file, "r") as file:
          for line in file:
            s = line.strip().rstrip("/")
            if s in all_lines:
              present.add(s)
        if len(all_lines) == len(present):
          if flags.verbose:
            print(f"PLS: Everything is as it should be in `{gitignore_file}`.")
          skip_this_gitignore = True
        else:
          if flags.verbose:
            print(f"PLS: Adding missing lines to `{gitignore_file}`.")
      else:
        if flags.verbose:
          print(f"PLS: Creating `{gitignore_file}`.")
      if not skip_this_gitignore:
        lines = []
        if need_newline_in_gitignore:
          lines.append("\n")
        lines.append("# Added automatically by `pls`. Okay to push to git.\n")
        for line in gitignore_lines:
          if line not in present:
            lines.append(f"{line}\n")
        with open(gitignore_file, "a") as file:
          file.writelines(lines)

  os.makedirs(flags.dotpls, exist_ok=True)

  if not os.path.isfile(cc_instrument_sh):
    with open(cc_instrument_sh, "w") as file:
      file.write(cc_instrument_sh_contents)
    os.chmod(cc_instrument_sh, 0o755)

  if not os.path.isfile(git_clone_sh):
    with open(git_clone_sh, "w") as file:
      file.write(cc_git_clone_sh_contents)
    os.chmod(git_clone_sh, 0o755)

  if not os.path.isdir(pls_h_dir):
    os.mkdir(pls_h_dir)
  if not os.path.isfile(pls_h):
    with open(pls_h, "w") as file:
      file.write(pls_h_contents)

  traverse_source_tree()

  apply_gitignore_changes()

if not cmd:
  # TODO(dkorolev): Differentiate between debug and release?
  # TODO(dkorolev): The "selfupdate" command, in case `pls` is `alias`-ed into a cloned repo?
  # TODO(dkorolev): `test` to run the tests, and also `release_test`.
  print("PLS: Requires a command, the most common ones are `build`, `run`, `clean`, and `version`.")
  sys.exit(0)

def cmd_version(unused_args):
  print(f"PLS v0.0.1 NOT READY YET")

def cmd_clean(args):
  traverse_source_tree()
  previously_broken_symlinks = set()
  for lib, _ in modules.items():
    if not os.path.exists(os.readlink(lib)):
      previously_broken_symlinks.add(lib)
  result = subprocess.run(["rm", "-rf", ".pls"])
  for lib, _ in modules.items():
    if not os.path.exists(os.readlink(lib)) and not lib in previously_broken_symlinks:
      if flags.verbose:
        print(f"PLS: Unlinking the now-broken link to `{lib}`.")
      os.unlink(lib)
  if result.returncode != 0:
    pls_fail("PLS: Could not clean the build.")
  if flags.verbose:
    print("PLS: Clean successful.")

def cmd_install(args):
  update_dependencies()
  if flags.verbose:
    print("PLS: Dependencies cloned successfully.")

def cmd_build(args):
  update_dependencies()
  # TODO(dkorolev): Debug/release.
  result = subprocess.run(["cmake", "-B", ".debug", f"-DCMAKE_CXX_FLAGS=-I{os.path.abspath(pls_h_dir)}"])
  if result.returncode != 0:
    pls_fail("PLS: cmake configuration failed.")
  result = subprocess.run(["cmake", "--build", ".debug"])
  if result.returncode != 0:
    pls_fail("PLS: cmake build failed.")
  if flags.verbose:
    print("PLS: Build successful.")

def cmd_run(args):
  cmd_build([])
  # TODO(dkorolev): Forward the command line? And test it?
  if not args:
    if len(executables) == 1:
      result = subprocess.run([f"./.debug/{next(iter(executables.keys()))}"])
    else:
      pls_fail(f"PLS: Has more than one executable, specify the name direcly, one of {json.dumps(list(executables.keys()))}.")
  else:
    if args[0] in executables:
      result = subprocess.run([f"./.debug/{args[0]}"])
    else:
      pls_fail(f"PLS: Executable `{args[0]}` is not in {json.dumps(list(executables.keys()))}.")

cmds = {}
cmds["version"] = cmd_version
cmds["v"] = cmd_version
cmds["clean"] = cmd_clean
cmds["c"] = cmd_clean
cmds["install"] = cmd_install
cmds["i"] = cmd_install
cmds["build"] = cmd_build
cmds["b"] = cmd_build
cmds["run"] = cmd_run
cmds["r"] = cmd_run

cmd0 = cmd[0].strip().lower()
if cmd0 in cmds:
  cmds[cmd0](cmd[1:])
else:
  print(f"PLS: The command `{cmd0}` is not recognized, try `pls help`.")
  sys.exit(0)
