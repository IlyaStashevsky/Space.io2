import socket
import threading
import pickle
import time
import random
import math
# сокеты
S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
S.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# постоянные
PORT = 5555

SERVER_IP = '26.198.66.213'

# попытаться подключиться к серверу
try:
    S.bind((SERVER_IP, PORT))
except socket.error as e:
    print(str(e))
    print("[SERVER] Сервер не запущен")
    quit()

S.listen()  # проверка подключений

print(f"[SERVER] Сервер запщуен с адресом: {SERVER_IP}")

# переменные и списки
W, H = 5000, 4000
BALL_RADIUS = 5
START_RADIUS = 20
SPIKE_SIZE = 13
ROUND_TIME = float('inf')

MASS_LOSS_TIME = 10

players = {}
balls = []
black_holes = []
connections = 0
_id = 0
red = (255, 0, 0)
orange = (255, 128, 0)
yellow = (255, 255, 0)
lime = (0, 255, 0)
green = (0, 255, 128)
lightblue = (0, 255, 255)
blue = (0, 128, 255)
darkblue = (0, 0, 255)
purple = (128, 0, 255)
pink = (255, 0, 255)
rose = (255, 0, 128)
gray = (128, 128, 128)
black = (0, 0, 0)
colors = [red, orange, yellow, lime, green, lightblue,
          blue, darkblue, purple, pink, rose, gray,
          black]
start = False
stat_time = 0
game_time = ""
nxt = 1
# Защита общих ресурсов с помощью блокировок
players_lock = threading.Lock()
balls_lock = threading.Lock()
black_holes_lock = threading.Lock()

def get_start_location(players):
    while True:
        stop = True
        x = random.randrange(0, W)
        y = random.randrange(0, H)
        for player in players:
            p = players[player]
            dis = math.sqrt((x - p["x"]) ** 2 + (y - p["y"]) ** 2)
            if dis <= START_RADIUS + p["score"]:
                stop = False
                break
        if stop:
            break
    return (x, y)

def release_mass(players):
    for player in players:
        p = players[player]
        if p["score"] > 15:
            p["score"] = math.floor(p["score"] * 0.97)


# проверяет столкновение игрока с каким-либо шаром
def check_collision(players, balls):
    for player in players:
        p = players[player]
        x = p["x"]
        y = p["y"]
        for ball in balls:
            bx = ball[0]
            by = ball[1]
            dis = math.sqrt((x - bx) ** 2 + (y - by) ** 2)
            if dis <= START_RADIUS + p["score"]:
                p["score"] = p["score"] + 0.5
                balls.remove(ball)


# проверяет столкновения игроков
def player_collision(players):
    sort_players = sorted(players, key=lambda x: players[x]["score"])
    for x, player1 in enumerate(sort_players):
        for player2 in sort_players[x + 1:]:
            p1x = players[player1]["x"]
            p1y = players[player1]["y"]

            p2x = players[player2]["x"]
            p2y = players[player2]["y"]

            dis = math.sqrt((p1x - p2x) ** 2 + (p1y - p2y) ** 2)
            if dis < players[player2]["score"] - players[player1]["score"] * 0.85:
                players[player2]["score"] = math.sqrt(
                    players[player2]["score"] ** 2 + players[player1]["score"] ** 2)
                players[player1]["score"] = 0
                players[player1]["x"], players[player1]["y"] = get_start_location(players)
                print(f"[GAME] " + players[player2]["name"] + " съел " + players[player1]["name"])

#проверка столкновений с колючками
def check_collision_with_black_holes(players, black_holes):
    for player in players:
        p = players[player]
        x = p["x"]
        y = p["y"]
        for black_hole in black_holes:
            sx, sy, ssize = black_hole
            dis = math.sqrt((x - sx) ** 2 + (y - sy) ** 2)
            if dis <= ssize + p["score"]:
                p["score"] = p["score"] / 1.5
                black_holes.remove(black_hole) # Удаляем колючку после столкновения


# создание сфер, шаров и колючек
def create_black_holes(black_holes, n):
    for _ in range(n):
        black_holes.append((random.randrange(0, W), random.randrange(0, H), SPIKE_SIZE))

def create_balls(balls, n):
    for i in range(n):
        while True:
            stop = True
            x = random.randrange(0, W)
            y = random.randrange(0, H)
            for player in players:
                p = players[player]
                dis = math.sqrt((x - p["x"]) ** 2 + (y - p["y"]) ** 2)
                if dis <= START_RADIUS + p["score"]:
                    stop = False
            if stop:
                break

        balls.append((x, y, random.choice(colors)))

# Игровой цикл запускается в отдельном потоке
def game_loop():
    global start, game_time, nxt
    last_mass_release_time = time.time()

    while True:
        if start:
            current_time = time.time()
            game_time = round(current_time - start_time)

            with players_lock, balls_lock, black_holes_lock:
                check_collision(players, balls)
                check_collision_with_black_holes(players, black_holes)

            # останавливаем игру, если время вышло
            if game_time >= ROUND_TIME:
                start = False

            with players_lock:
                # высвобождение массы игрока (убыль массы)
                if current_time - last_mass_release_time >= MASS_LOSS_TIME:
                    release_mass(players)
                    last_mass_release_time = current_time

            # Проверка столкновений


            # Создаем дополнительные объекты, если их мало
            with balls_lock:
                if len(balls) < 600:
                    create_balls(balls, random.randrange(100, 150))
                    print("[GAME] Создание дополнительных частиц")

            with black_holes_lock:
                if len(black_holes) < 20:
                    create_black_holes(black_holes, random.randrange(20, 30))
                    print('[GAME] Создание дополнительных черных дыр')

            time.sleep(0.001)



# Функция клиента отправляет и получает данные
def threaded_client(conn, _id):
    global connections, players, game_time, start, start_time

    current_id = _id
    # получение имени от клиента
    data = conn.recv(2048)
    name, color = pickle.loads(data)
    print("[LOG]", name, "подключился к серверу.")

    with players_lock:
        x, y = get_start_location(players)
        # Создаем нового игрока с его координатами, цветом, счетом и именем
        players[current_id] = {"x": x, "y": y, "color": color, "score": 0, "name": name}

        # Отправляем клиенту его текущий идентификатор
        conn.send(str.encode(str(current_id)))

    while True:
        try:
            # Получаем данные от клиента
            data = conn.recv(2048)

            if not data:
                break

            data = data.decode('utf-8')

            # Обрабатываем команды от клиента
            if data.split(" ")[0] == "move":
                with players_lock:
                    split_data = data.split(" ")
                    x = int(split_data[1])
                    y = int(split_data[2])
                    players[current_id]["x"] = x
                    players[current_id]["y"] = y

            with players_lock, balls_lock, black_holes_lock:
                player_collision(players)

            # Подготавливаем и отправляем данные об игре
            with players_lock, balls_lock, black_holes_lock:
                send_data = pickle.dumps((balls, black_holes, players, game_time))

            conn.send(send_data)

        except socket.error as e:
            print("[ERROR]", e)
            break


    # Удаляем игрока при отсоединении
    with players_lock:
        print("[DISCONNECT] Имя:", name, "Id:", current_id, "отключился")
        connections -= 1
        del players[current_id]
        conn.close()


# Создаем частицы и черные дыры заранее
create_balls(balls, random.randrange(650, 700))
create_black_holes(black_holes, 50)

# Стартуем игровой цикл в отдельном потоке
game_thread = threading.Thread(target=game_loop)
game_thread.start()

print("[SERVER] Ожидание подключений")

# Основной цикл сервера
try:
    while True:
        conn, addr = S.accept()
        print("[CONNECTION] Подключился:", addr)

        if addr[0] == SERVER_IP and not start:
            start = True
            start_time = time.time()
            print("[STARTED] Игра началась!")

        connections += 1
        threading.Thread(target=threaded_client, args=(conn, _id)).start()
        _id += 1

except KeyboardInterrupt:
    print("\n[SERVER] Сервер отключен")
    S.close()