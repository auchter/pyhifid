with import <nixpkgs> {};
mkShell {
  nativeBuildInputs = [
    alsa-lib
    bluez
    glib.dev
    pkg-config
  ];
}
