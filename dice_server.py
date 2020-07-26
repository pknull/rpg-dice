#!/usr/bin/env python3

# Standard libraries
from _thread import *
import threading
import socket
import sys
import json

# Third-party Libraries
from dice_roller.DiceThrower import DiceThrower

# Define global lock
lock = threading.Lock()

# Threading class
class ClientThread(threading.Thread):
    def __init__(self,clientAddress,clientsocket):
        threading.Thread.__init__(self)
        self.csocket = clientsocket
        self.clientAddress = clientAddress
        print(f"[+] New connection added {self.clientAddress}")
    def run(self):
        dice = DiceThrower()
        while True:
            # send prompt
            self.csocket.send(b"DiceRoller > ")
            # Grab message
            msg = self.csocket.recv(1024)
            if not msg:
                print("[-] Kill connection")
                break
            if b"quit" in msg or b"exit" in msg:
                self.csocket.send(b"========DISCONNECTED=========")
                print(f"[-] {self.clientAddress} disconnected")
                break
            try:
                msg = msg.decode("utf-8")
                # Process message
                response = dice.throw(msg[:-1])
                for resp in response:
                    response[resp] = str(response[resp])
                # Send 
                self.csocket.send(json.dumps(response, indent=2).encode('utf-8') + b"\n");
            except Exception as e:
                print("Fail:", e)
                pass
        self.csocket.close()

# Initialize socket object
def init(addr, port):
    # Log
    print(f"[+] Setting up server on {addr}:{port}...")
    # Define socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((addr,int(port,10)))
    # Return object 
    return s

# Setup server and start accepting threads
def serve(sock):
    # Server start
    print("[+} Server started.")
    # Begin while loop
    while True:
        # listen
        sock.listen(1)
        # Establish conection with client
        c, addr = sock.accept()
        
        print(f"[+] Connection received from {addr[0]}:{addr[1]}")
        newthread = ClientThread(addr,c)
        newthread.start()

# Our main to take in port and ip info
def main():
    # Init server
    addr = sys.argv[1]
    port = sys.argv[2]
    server = init(addr,port)
    
    # Begin server
    serve(server)

# Run the main file
main()
