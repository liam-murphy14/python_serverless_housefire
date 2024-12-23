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
      packages = forEachSupportedSystem ({ pkgs }:
        let
          chromeExecutablePath = if pkgs.stdenv.isDarwin then "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" else "${pkgs.chromium}/bin/chromium";
          wrappedHousefire = pkgs.callPackage ./default.nix {
            chromeExecutablePath = chromeExecutablePath;
          };
        in
        {
          default = pkgs.python3Packages.callPackage wrappedHousefire { };
        });
      devShells = forEachSupportedSystem ({ pkgs }: {
        default = pkgs.mkShell {
          packages = with pkgs; [
            (
              python3.withPackages (
                ps: with ps; [
                  # dev dependencies
                  pandas
                  requests
                  nodriver
                  googlemaps
                  click
                  black
                ]
              )
            )
            # extra dev non-darwin dependencies
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
