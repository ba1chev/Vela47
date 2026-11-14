A2A_DOCKER_SEND_SCRIPT = """
import sys, time, socket
payload = sys.stdin.buffer.read()
deadline = time.monotonic() + float(sys.argv[3])
while True:
    try:
        connection = socket.create_connection((sys.argv[1], int(sys.argv[2])), timeout = 2)
        break
    except OSError:
        if time.monotonic() > deadline:
            raise
        time.sleep(0.1)
connection.sendall(payload)
connection.close()
"""
