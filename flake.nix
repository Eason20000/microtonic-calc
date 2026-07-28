{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs = { self, nixpkgs }: 
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      packages.${system}.default = pkgs.callPackage ./package.nix { inherit self; };
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          python3
        ];
      };
    };

}
