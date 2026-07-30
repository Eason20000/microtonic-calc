{ self, lib, python3Packages }:

python3Packages.buildPythonApplication rec {
  pname = (lib.importTOML (src + "/pyproject.toml")).project.name;
  version = (lib.importTOML (src + "/pyproject.toml")).project.version;

  src = self;

  pyproject = true;

  dependencies = with python3Packages; [
    tabulate
  ];

  nativeBuildInputs = [ python3Packages.setuptools ];

  meta.mainProgram = "mtcalc";

}
