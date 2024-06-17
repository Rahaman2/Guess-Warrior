from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import join_room, leave_room, send, SocketIO
import random
import requests
import json
from string import ascii_uppercase
from controllers import *
import models.questions as questionObj




app = Flask(__name__, template_folder='views/templates', static_url_path="/static")
app.config['SECRET_KEY'] = "zukkiii"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(Length):
    while True:
        code = ""
        for _ in range(Length):
            code += random.choice(ascii_uppercase)
            
        if code not in rooms:
            break
    return code

@app.route("/", methods=["POST", "GET"])              
def home():
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name: 
            return render_template("home.html", error="Please enter a name.", code=code, name=name)
        
        elif join != False and not code:
            return render_template("home.html", error="Please enter a room code.", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
    return render_template("home.html")


@app.route("/game", methods=["POST", "GET"])
def game():        
    return render_template("game.html")



# the questions api

@app.route("/question", methods=["POST", "GET"])
def questions():
    if request.method =="GET":
        questionObject = questionObj.Questions()
        current_question = questionObject.generate_question()
        answers = questionObject.question_dict()
        # sorted_values = sorted(answers.items(), key=lambda item:item[1])
        # sorted_keys = [item[0] for item in sorted_]
        # sorted_values = sorted([ int(answers[key]) for i,key in enumerate(sorted_keys)], reverse=True)
         
        question_json_data = {
            "question": current_question,
            "answers": answers,
            "sorted_answer_list": [key for (key,val) in answers.items()],
            # "sorted_points": sorted_values
        }
        print(question_json_data)
        return jsonify(question_json_data)
    elif request.method == "POST":
        
        requestData = request.get_json()
        user_answer = requestData["userAnswer"]
        valid_answers = requestData["questionData"]["answers"]
        question = requestData["questionData"]["question"]
        print(user_answer)
        # evaluating the answer if the answser is valid it will return the correct answer else wrong answer
        
        answer_evaluation = questionObj.Questions().eval_user_answer(user_answer, valid_answers, question)
        requestData["userAnswer"] = answer_evaluation
        
        return jsonify(requestData)


    
    


# sessions 
@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    session_id = session.get('session_id')
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return 
    if room not in rooms:
        leave_room(room)
        return 
    
    join_room(room)
    send({"name": name, "message": "has entered the room."}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]

    send({"name": name, "message": "has left the room."}, to=room)
    print(f"{name} has left the room {room}")
    print("Disconnect event fired.")
# Import your controllers

if __name__ == '__main__':
    socketio.run(app, debug=True)