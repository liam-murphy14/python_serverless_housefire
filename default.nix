{ chromeExecutablePath }:

{ buildPythonApplication
, googlemaps
, click
, nodriver
, pythonOlder
, pandas
, requests
, setuptools
}:

buildPythonApplication {
  pname = "housefire";
  version = "1.0.0";
  pyproject = true;

  disabled = pythonOlder "3.9";

  src = ./.;

  postPatch = ''
    substituteInPlace ./housefire/config.py \
      --subst-var-by NIX_TARGET_CHROME_PATH "${chromeExecutablePath}"
  '';

  dependencies = [
    pandas
    requests
    nodriver
    googlemaps
    click
  ];

  build-system = [ setuptools ];

  meta = {
    homepage = "https://github.com/liam-murphy14/housefire";
    description = "A personal project for people to see REITs";
  };
}
