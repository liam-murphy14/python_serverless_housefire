{
  description = "Nix flake for the python build inputs to housefire";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs { inherit system; };
      });
    in
    {
      packages = forEachSupportedSystem ({ pkgs }: {
        default = pkgs.python3Packages.callPackage ./default.nix { };
      });
      devShells = forEachSupportedSystem ({ pkgs }: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            (
              python3.withPackages (
                ps: with ps; [
                  (callPackage ./default.nix { })
                  # extra dev dependencies
                  black
                ]
              )
            )
            # extra non-darwin dependencies
            (if (!pkgs.stdenv.isDarwin) then pkgs.chromium else null)
            (if (!pkgs.stdenv.isDarwin) then pkgs.xvfb-run else null)
          ];

          shellHook = (pkgs.lib.optionalString (!pkgs.stdenv.isDarwin) ''
            export CHROME_PATH=${pkgs.chromium}/bin/chromium
          '');
        };
      });
      formatter = forEachSupportedSystem ({ pkgs }: pkgs.nixpkgs-fmt
      );
    };
}
