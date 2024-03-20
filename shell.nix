{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    cargo
    clang
    git
    rustc
    protobuf
    python3

    # Firedancer transitive build dependencies
    automake
    bison
    gettext
    perl
  ];

  shellHook = ''
    if test ! -d env; then
      python -m venv env
    fi
    source env/bin/activate
  '';
}
