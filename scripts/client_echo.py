import zmq
import json

def main():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5557")  # connects through the tunnel

    msg = {"from": "local_machine", "test": "hello GPU!"}
    print(f"📤 Sending: {msg}")
    socket.send_string(json.dumps(msg))

    reply = socket.recv_json()
    print(f"📥 Received reply: {reply}")

if __name__ == "__main__":
    main()

