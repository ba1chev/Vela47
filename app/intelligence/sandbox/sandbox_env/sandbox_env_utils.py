import io
import pathlib
import tarfile

SANDBOX_OUTPUT_MAX_CHARS = 8_000
SANDBOX_OUTPUT_HEAD_CHARS = 2_000


def cap_sandbox_output(output: str) -> str:
    if len(output) > SANDBOX_OUTPUT_MAX_CHARS:
        kept_tail = SANDBOX_OUTPUT_MAX_CHARS - SANDBOX_OUTPUT_HEAD_CHARS
        output = (
            output[:SANDBOX_OUTPUT_HEAD_CHARS]
            + f"\n… {len(output) - SANDBOX_OUTPUT_MAX_CHARS} characters of output cut …\n"
            + output[-kept_tail:]
        )
    return output.strip() or "(no output)"


def archive_sandbox_directory(root: pathlib.Path, compress: bool = False) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj = buffer, mode = "w:gz" if compress else "w") as archive:
        archive.add(root, arcname = ".")
    return buffer.getvalue()
