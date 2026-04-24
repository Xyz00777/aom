{
  description = "aom - Ansible Output Monitor";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python314;
      in {
        packages.default = python.pkgs.buildPythonApplication {
          pname = "ansible-aom";
          version = "0.1.0";
          src = ./.;
          format = "pyproject";

          nativeBuildInputs = [ python.pkgs.hatchling ];

          propagatedBuildInputs = with python.pkgs; [
            textual
            rich
            pyyaml
            pydantic
            pydantic-settings
            platformdirs
            pexpect
            psutil
            blessed
          ];

          nativeCheckInputs = with python.pkgs; [
            pytest
            pytest-asyncio
            pytest-cov
          ];
        };

        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.default ];

          buildInputs = with pkgs; [
            python
            uv
            ruff
            mypy
            ansible-core
          ] ++ (with python.pkgs; [
            pytest
            pytest-asyncio
            pytest-textual-snapshot
            pytest-cov
            textual-dev
            inline-snapshot
          ]);

          shellHook = ''
            # PYTHONPATH intentionally not set - uv manages the environment
            # and installs the package in editable mode via .venv

            # Install ansible.posix collection if not present
            if ! ansible-galaxy collection list ansible.posix 2>/dev/null | grep -q "ansible.posix"; then
                ansible-galaxy collection install ansible.posix --quiet
            fi
          '';
        };

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/aom";
        };
      });
}