class RecordingConnection:
    """Records every statement executed on it, with its parameters, into a list the
    test reads back. Lets a test see what a database runs on a connection without any
    database server being there."""

    def __init__(self) -> None:
        self.statements: list[tuple[str, dict]] = []

    def execute(self, statement, parameters = None) -> None:
        self.statements.append((str(statement), parameters))
