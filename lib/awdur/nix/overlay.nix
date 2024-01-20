final: prev:

let
  # Read the package's version from file
  lines = prev.lib.splitString "\n" (builtins.readFile ../awdur/__init__.py);
  matches = builtins.map (builtins.match ''__version__ = "(.+)"'') lines;
  versionStr = prev.lib.concatStrings (prev.lib.flatten (builtins.filter builtins.isList matches));
in {
  pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [(
    python-final: python-prev: {
      awdur = python-prev.buildPythonPackage {
        pname = "awdur";
        version = versionStr;
        format = "pyproject";

        src = ./..;

        nativeBuildInputs = with python-final; [
          hatchling
        ];

        propagatedBuildInputs = with python-final; [
          docutils
          pygments
        ];

        doCheck = false;
        pythonImportsCheck = [ "awdur.cli" ];
      #   nativeCheckInputs = with python-prev; [
      #     pytestCheckHook
      #   ];
      };
    }
  )];
}
