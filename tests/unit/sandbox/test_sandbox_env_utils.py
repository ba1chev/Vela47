import io
import pathlib
import tarfile
import tempfile

from app.intelligence.sandbox import cap_sandbox_output
from app.intelligence.sandbox import SANDBOX_OUTPUT_MAX_CHARS
from app.intelligence.sandbox import SANDBOX_OUTPUT_HEAD_CHARS
from app.intelligence.sandbox import archive_sandbox_directory


class TestSandboxEnvUtils:
    def test_short_output_is_kept_whole(self):
        assert cap_sandbox_output("  1 passed \n") == "1 passed"

    def test_no_output_says_so(self):
        assert cap_sandbox_output("") == "(no output)"

    def test_long_output_keeps_the_head_and_the_tail(self):
        output = "h" * SANDBOX_OUTPUT_HEAD_CHARS + "m" * 50_000 + "t" * 100
        capped = cap_sandbox_output(output)
        assert capped.startswith("h" * SANDBOX_OUTPUT_HEAD_CHARS) and capped.endswith("t" * 100)
        assert "characters of output cut" in capped and len(capped) < SANDBOX_OUTPUT_MAX_CHARS + 100

    def test_an_archive_holds_the_directory_compressed_or_not(self):
        root = pathlib.Path(tempfile.mkdtemp())
        (root / "a.py").write_text("x = 1\n")
        for compress, mode in ((False, "r:"), (True, "r:gz")):
            with tarfile.open(fileobj = io.BytesIO(archive_sandbox_directory(root, compress)), mode = mode) as archive:
                assert archive.extractfile("./a.py").read() == b"x = 1\n"
