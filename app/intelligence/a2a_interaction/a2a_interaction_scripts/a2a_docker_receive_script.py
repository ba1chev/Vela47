A2A_DOCKER_RECEIVE_SCRIPT = """
import sys, socket
server = socket.create_server((sys.argv[1], int(sys.argv[2])))
server.settimeout(float(sys.argv[3]))
connection, _ = server.accept()
connection.settimeout(float(sys.argv[3]))
chunks = []
while chunk := connection.recv(65536):
    chunks.append(chunk)
sys.stdout.buffer.write(b"".join(chunks))
"""
