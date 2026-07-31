{ pkgs, ... }:
{
  projectRootFile = "flake.nix";
  programs.nixfmt = {
    enable = true;
    width = 80;
  };
  programs.ruff-format = {
    enable = true;
    lineLength = 80;
  };
  programs.taplo.enable = true;
  programs.mdformat = {
    enable = true;
    settings.wrap = 80;
    plugins = ps: [ ps.mdformat-gfm ];
  };
}
