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
        pyproject = fromTOML (builtins.readFile ./pyproject.toml);
      in {
        packages.default = python.pkgs.buildPythonApplication {
          pname = "ansible-aom";
          version = pyproject.project.version;
          src = ./.;
          format = "pyproject";

          nativeBuildInputs = [ python.pkgs.hatchling ];

          propagatedBuildInputs = with python.pkgs; [
            textual
            rich
            pyyaml
            pydantic
            pydantic-settings
            pexpect
            psutil
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
            stdenv.cc
          ] ++ (with python.pkgs; [
            pytest
            pytest-asyncio
            pytest-cov
            textual-dev
            ansible-core
          ]);

          shellHook = ''
            # PYTHONPATH intentionally not set - uv manages the environment
            # and installs the package in editable mode via .venv

            # Install ansible.posix collection if not present
            if ! ansible-galaxy collection list ansible.posix 2>/dev/null | grep -q "ansible.posix"; then
                ansible-galaxy collection install ansible.posix --quiet
            fi

            # Auto-install pre-commit git hooks (idempotent: only when missing).
            # Respects global core.hooksPath — if set, drops a wrapper script
            # into that directory that calls `pre-commit run`. pre-commit itself
            # cannot target a custom hooks path, so the wrapper bridges the gap.
            if [ -f .pre-commit-config.yaml ] && [ -d .git ] && command -v pre-commit >/dev/null 2>&1; then
              HOOKS_PATH="$(git config --get core.hooksPath 2>/dev/null || echo .git/hooks)"
              if [ ! -f "$HOOKS_PATH/pre-commit" ]; then
                echo "Installing pre-commit git hooks to $HOOKS_PATH..."
                mkdir -p "$HOOKS_PATH"
                cp .agent/hooks/pre-commit-wrapper.sh "$HOOKS_PATH/pre-commit"
                chmod +x "$HOOKS_PATH/pre-commit"
              fi
            fi
          '';
        };

        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/aom";
        };
      });
}
