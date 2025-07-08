{
  description = "workspace configuration for cns";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:

    let
      systems = [
        "x86_64-linux" # 64-bit linux
        "aarch64-darwin" # 64-bit ARM macOS
        "x86_64-darwin" # 64-bit Intel macOS
      ];

      forAllSystems =
        fn:
        nixpkgs.lib.genAttrs systems (
          system:
          fn {
            pkgs = import nixpkgs {
              inherit system;

              config.allowUnfreePredicate =
                pkg:
                builtins.elem (nixpkgs.lib.getName pkg) [
                  "vault-bin"
                ];

              overlays = [ ];
            };
          }
        );

    in
    {
      packages = forAllSystems ({ pkgs, ... }: { });

      devShells = forAllSystems (
        { pkgs, ... }:
        let
        in
        {
          default = pkgs.mkShell {
            buildInputs = with pkgs; [

              # Python development tools
              uv

              tilt # Local development orchestration
              kubernetes-helm # Kubernetes package manager

              # Container and Kubernetes Tools
              k3d # Lightweight Kubernetes for local dev
              kubectl # Kubernetes CLI
              ctlptl # Multi-cluster management

              # Secret management
              sops
              age

            ];
            shellHook = ''
              # PATH Configuration
              export PATH="$HOME/.local/bin:$PATH"

            '';
          };
        }
      );
    };
}
