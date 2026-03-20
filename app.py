from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# QUESTIONS
questions = [
    {"q": "What is phishing?",
     "options": ["📧 Fake email attack", "🔥 Firewall", "🎮 Game", "🔌 Cable"],
     "answer": 0},

    {"q": "What is malware?",
     "options": ["💀 Virus software", "✅ Safe app", "⌨ Keyboard", "🖥 Monitor"],
     "answer": 0}
]

players = {}
current_q = -1
game_started = False


# 🎮 PLAYER PAGE (KAHOOT STYLE)
PLAYER_HTML = """
<body style="background:black;color:lime;text-align:center;font-family:monospace;">

<h1>🎮 Cyber Challenge</h1>

<input id="name" placeholder="Enter name">
<button onclick="join()">🚀 Join</button>

<h3 id="status"></h3>

<div id="game" style="display:none;">
    <h2 id="countdown"></h2>
    <h2 id="timer"></h2>
    <h3 id="question"></h3>
    <div id="options"></div>
    <h2 id="result"></h2>
</div>

<script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
<script>
var socket = io();
var player="";

function join(){
    player = document.getElementById("name").value;

    if(player==""){
        alert("Enter name");
        return;
    }

    socket.emit("join", player);
}

socket.on("join_success", function(){
    document.getElementById("status").innerHTML = "✅ Joined! Waiting for host...";
    document.getElementById("game").style.display="block";
});

socket.on("join_error", function(msg){
    alert(msg);
});

socket.on("countdown", function(t){
    document.getElementById("countdown").innerHTML = "⏳ Starting in " + t;
});

socket.on("question", function(data){
    document.getElementById("countdown").innerHTML="";
    document.getElementById("result").innerHTML="";
    document.getElementById("question").innerHTML = data.q;

    let html="";
    data.options.forEach((o,i)=>{
        html += `<button onclick="send(${i})">${o}</button><br><br>`;
    });
    document.getElementById("options").innerHTML = html;
});

socket.on("timer", function(t){
    document.getElementById("timer").innerHTML = "⏱ Time: "+t;
});

socket.on("correct", function(ans){
    document.getElementById("result").innerHTML = "✅ Correct: "+ans;
});

function send(i){
    socket.emit("answer", {name:player, ans:i});
}
</script>
</body>
"""


# 🧠 HOST PANEL (LIVE PLAYERS + START)
HOST_HTML = """
<body style="background:black;color:lime;text-align:center;font-family:monospace;">

<h1>🧠 HOST PANEL</h1>

<button onclick="start()">🚀 Start Game</button>

<h2>👥 Players</h2>
<div id="players"></div>

<script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
<script>
var socket = io();

function start(){
    socket.emit("start");
}

socket.on("players", function(data){
    let html="";
    for(let p in data){
        html += "👤 " + p + " : " + data[p] + "<br>";
    }
    document.getElementById("players").innerHTML = html;
});
</script>
</body>
"""


@app.route("/")
def player():
    return render_template_string(PLAYER_HTML)


@app.route("/host")
def host():
    return render_template_string(HOST_HTML)


# 🎯 SOCKET EVENTS

@socketio.on("join")
def join(name):

    if name in players:
        emit("join_error", "❌ Name already taken!")
        return

    players[name] = 0
    emit("join_success")
    socketio.emit("players", players)


@socketio.on("start")
def start_game():
    global current_q, game_started

    if len(players) == 0:
        return

    game_started = True
    current_q = 0
    socketio.start_background_task(run_quiz)


def run_quiz():
    global current_q

    # ⏳ COUNTDOWN BEFORE START
    for t in range(5, 0, -1):
        socketio.emit("countdown", t)
        eventlet.sleep(1)

    while current_q < len(questions):

        q = questions[current_q]
        socketio.emit("question", q)

        # ⏱ TIMER
        for t in range(10, 0, -1):
            socketio.emit("timer", t)
            eventlet.sleep(1)

        # ✅ CORRECT ANSWER
        correct = q["options"][q["answer"]]
        socketio.emit("correct", correct)

        eventlet.sleep(3)
        current_q += 1

    socketio.emit("players", players)


@socketio.on("answer")
def answer(data):
    name = data["name"]
    ans = data["ans"]

    if 0 <= current_q < len(questions):
        if questions[current_q]["answer"] == ans:
            players[name] += 1

    socketio.emit("players", players)


# RUN
import os
port = int(os.environ.get("PORT", 5000))
socketio.run(app, host="0.0.0.0", port=port)