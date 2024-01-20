{
  description = "Awdur";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils }:

    utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system ; overlays = [ self.overlays.default ];};

      in {

        packages.default = pkgs.python3Packages.awdur;

      }) // {
        overlays.default = import ./lib/awdur/nix/overlay.nix;
      };
}
