
## 2026-05-08: Licensing Research for ansible-aom

### Decision: License choice for ansible-aom
- **Conclusion**: ansible-aom can safely use MIT or Apache-2.0 because it communicates with ansible-core at arm's length via subprocess (pexpect/pipes), not via linking or importing.
- **Chosen approach**: Declare as MIT (or Apache-2.0) with `ansible-core` as an optional integration dependency, not a hard dependency.
- **Key precedent**: ansible-navigator (Apache-2.0) and ansible-runner (Apache-2.0) are both official Ansible project tools that wrap/shell-out to ansible-core and are licensed Apache-2.0, NOT GPL.
- **Caution**: If ansible-aom ever imports from ansible-core (e.g., `from ansible import ...`), those specific modules would be GPL-3.0-or-later and the importing code would need to be GPL-compatible. Avoid importing ansible-core at runtime.

### Key References
- ansible-core pyproject.toml: `license = "GPL-3.0-or-later"`
- ansible-navigator: `license = {text = "Apache"}` → Apache-2.0
- ansible-runner: `license = "Apache-2.0"`
- ara: GPL-3.0-or-later (but it uses a callback plugin that runs INSIDE ansible's process)
- FSF GPL FAQ on arm's-length communication: https://www.gnu.org/licenses/gpl-faq.en.html
