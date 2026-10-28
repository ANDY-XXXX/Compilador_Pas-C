import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from PERSISTENCE.text_files import read_tsv


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = (
    Path(__file__).resolve().parent / "flex" / "analizador_lexico.l"
)


class FlexError(RuntimeError):
    # Raised when Flex or GCC fail, or when the lexer cannot run.
    pass


@dataclass
class FlexResult:
    tokens: list
    symbols: list
    errors: list
    log: str


class FlexRunner:
    def __init__(self, source=DEFAULT_SOURCE, build_dir=None):
        self.source = Path(source).resolve()
        self.build_dir = Path(
            build_dir or ROOT / "BUILD" / "flex"
        ).resolve()
        self.executable = self.build_dir / (
            "analizador.exe" if os.name == "nt" else "analizador"
        )
        self.ready = False
        self.compiled_source = None   # filled in by compile()

    # Internal helpers
    def _run(self, command, cwd, timeout=30):
        try:
            result = subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise FlexError(
                f"Timeout ({timeout} s): {command[0]}"
            ) from error
        except OSError as error:
            raise FlexError(
                f"Could not run {command[0]}: {error}"
            ) from error

        if result.returncode:
            raise FlexError(
                result.stdout + result.stderr
                or f"Exit code: {result.returncode}"
            )

        return result.stdout + result.stderr

    # Public API
    def compile(self):
        self.ready = False

        for name in ("flex", "gcc"):
            if not shutil.which(name):
                raise FlexError(
                    f"'{name}' not found in PATH. See README.md. "
                    "The other tabs can still be used."
                )

        self.build_dir.mkdir(parents=True, exist_ok=True)
        c_file = self.build_dir / "lex.yy.c"

        log = self._run(
            ["flex", "-o", str(c_file), str(self.source)],
            self.build_dir,
        )

        # The .l source uses %option noyywrap, so no -lfl is needed.
        log += self._run(
            [
                "gcc",
                "-Wall",
                "-Wextra",
                str(c_file),
                "-o",
                str(self.executable),
            ],
            self.build_dir,
        )

        self.ready = True
        self.compiled_source = self.source.read_bytes()
        return log or "Compilation successful."

    def analyze(self, code):
        if not self.ready or not self.executable.exists():
            raise FlexError("Compile the Flex analyzer first.")

        if self.source.read_bytes() != self.compiled_source:
            self.ready = False
            raise FlexError("The .l file changed. Recompile before analyzing.")

        with tempfile.TemporaryDirectory(
            prefix="run_", dir=self.build_dir
        ) as folder:
            path = Path(folder)
            source = path / "entrada.pas"
            source.write_text(code, encoding="utf-8")

            log = self._run(
                [str(self.executable), str(source)],
                path,
            )

            return FlexResult(
                read_tsv(path / "tiraTokens.tsv"),
                read_tsv(path / "simbolos.tsv"),
                read_tsv(path / "errores.tsv"),
                log,
            )