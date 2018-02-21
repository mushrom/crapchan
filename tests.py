#!/usr/bin/python
import requests

env = "http://127.0.0.1:5000/"
board = "test"
thread = "test"
post = "test"

print("Testing board creation")
requests.post(env +"create-board", data = {"name":board, "description":"testboard"})
print("testing thread creation")
requests.post(env+"post-thread/"+board , data = {"subject":thread,"content":"test"})
print("testing post creation - COMING SOON!")

