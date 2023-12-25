import contextlib
from client import Network
with contextlib.redirect_stdout(None):
    import pygame
import os
import tkinter as tk
from PIL import ImageTk, Image
from ctypes import *


pygame.font.init()
pygame.mixer.init()
W = (windll.user32.GetSystemMetrics(0))
H = (windll.user32.GetSystemMetrics(1))

# постоянные
PLAYER_RADIUS = 20
START_VEL = 9
BALL_RADIUS = 5
NAME_FONT = pygame.font.SysFont("comicsans", 20)
TIME_FONT = pygame.font.SysFont("comicsans", 30)
SCORE_FONT = pygame.font.SysFont("comicsans", 26)
background = pygame.image.load("фонигры.png")
soundtrack = pygame.mixer.Sound('саундтрек.mp3')
red = (255, 0, 0)
orange = (255, 128, 0)
yellow = (255, 255, 0)
lime = (0, 255, 0)
green = (0, 255, 128)
sblue = (0, 255, 255)
blue = (0, 128, 255)
dblue = (0, 0, 255)
purple = (128, 0, 255)
pink = (255, 0, 255)
gray = (128, 128, 128)
black = (0, 0, 0)
COLORS = [red, orange, yellow, lime, green, sblue,
          blue, dblue, purple, pink, gray,
          black]
COLORS1 = ['red', 'orange', 'yellow', 'lime', 'green', 'lightblue',
           'blue', 'darkblue', 'purple', 'pink', 'gray',
           'black']
camera_x = 0
camera_y = 0
players = {}
balls = []
black_holes = []
color = (255, 0, 0)


#класс для подключения, отправки и получения информации с сервера

class MainMenu:
    def __init__(self, root):
        self.root = root
        self.root.title("Space.IO")
        self.root.state('zoomed')

        # Загрузка фона
        self.background_image = ImageTk.PhotoImage(Image.open("фонменю.jpg"))
        self.canvas = tk.Canvas(root, width=1920, height=1080)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.background_image, anchor="nw")

        # Главная надпись
        self.canvas.create_text(800, 50, text="SPACE.IO", fill="white",
                                font=("Helvetica", "36", "bold"))

        self.canvas.create_text(800, 250, text='Выберите цвет:', fill='white',
                                font=('Helvetica', '24', 'bold'))
        # Никнейм и его ввод
        self.name_label = self.canvas.create_text(800, 450, text="Введите никнейм:", fill="white",
                                                  font=("Helvetica", "24"))
        self.name_entry = tk.Entry(root, font=("Helvetica", "24", 'bold'), justify="center")
        name_entry_window = self.canvas.create_window(800, 500, window=self.name_entry, width=500)

        # Кнопки выбора цвета
        self.color_buttons = []
        self.colors = COLORS
        self.selected_color = None
        for i, color in enumerate(COLORS):
            button = tk.Button(root, bg=self.hex_color(color), activebackground=self.hex_color(color),
                               command=lambda c=color: self.select_color(c), height=3, width=15)
            button_window = self.canvas.create_window(100 + i * 120, 300, window=button)
            self.color_buttons.append(button)

        # Кнопка старт
        self.start_button = tk.Button(root, text="Начать игру", command=self.start_game, height=3, width=20,
                                      font=("Helvetica", "24"))
        start_button_window = self.canvas.create_window(800, 650, window=self.start_button)

    def select_color(self, color):
        self.selected_color = color
        print("Выбранный цвет:", color)

    @staticmethod
    def hex_color(rgb):
    #Конвертирует RGB в HEX
        return "#%02x%02x%02x" % rgb

    def start_game(self):
        name = self.name_entry.get()
        color = self.selected_color
        if color is None:
            print("Цвет не выбран!")
            return
        print("Никнейм:", name, "Выбранный цвет:", color)

        self.root.destroy()  # Закрывает главное окно tkinter
        main(name, color)

# функции

    # конвертирует время из секунд в минуты
def convert_time(t):
    if type(t) == str:
        return t

    if int(t) < 60:
        return str(t) + "s"
    else:
        minutes = str(t // 60)
        seconds = str(t % 60)

        if int(seconds) < 10:
            seconds = "0" + seconds

        return minutes + ":" + seconds


# рисует каждый кадр
def redraw_window(WIN, players, balls, black_holes, game_time, score, camera_x, camera_y):
    WIN.fill((255, 255, 255))  # очищение экрана
    background_surface = pygame.Surface(WIN.get_size())
    background_surface.blit(background, (0, 0))
    WIN.blit(background_surface, (0, 0))
    # рисует еду и шары
    for ball in balls:
        pygame.draw.circle(WIN, ball[2], (ball[0] - camera_x, ball[1] - camera_y), BALL_RADIUS)

    # рисует каждого игрока из списка
    for player in sorted(players, key=lambda x: players[x]["score"]):
        p = players[player]
        pygame.draw.circle(WIN, p["color"], (p["x"] - camera_x, p["y"] - camera_y), PLAYER_RADIUS + round(p["score"]))
        # выводит имя игрока
        text = NAME_FONT.render(p["name"], 1, (255, 255, 255))
        WIN.blit(text, (p["x"] - camera_x - text.get_width() // 2, p["y"] - camera_y - text.get_height() // 2))


    #рисует черные дыры
    for black_hole in black_holes:
        pygame.draw.circle(WIN, (0, 0, 0), (black_hole[0] - camera_x, black_hole[1] - camera_y), black_hole[2])

    # доска счета
    sort_players = list(reversed(sorted(players, key=lambda x: players[x]["score"])))
    title = TIME_FONT.render("Рейтинг", 1, (255, 255, 255))
    start_y = 25
    x = W - title.get_width() - 70
    WIN.blit(title, (x, 0))

    ran = min(len(players), 10)
    for count, i in enumerate(sort_players[:ran]):
        text = SCORE_FONT.render(str(count + 1) + ". " + str(players[i]["name"]), 1, (255, 255, 255))
        WIN.blit(text, (x, start_y + count * 20))

    # табличка личного счета
    text = TIME_FONT.render("Ваш счет: " + str(round(score)), 1, (255, 255, 255))
    WIN.blit(text, (10, 10))



# функция запуска игры и основной цикл
def main(name, color):
    global players
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (0, 30)

    # настройка окна и названия
    WIN = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Space.IO")
    soundtrack.play(loops=-1)
    # подключение игрока и рисовка объектов
    server = Network()
    current_id = server.connect(name, color)
    balls, black_holes, players, game_time = server.send("get")[:4]

    # установка времени
    clock = pygame.time.Clock()

    run = True
    while run:
        clock.tick(100)
        player = players[current_id]
        vel = START_VEL - round(player["score"] / 35)
        if vel <= 1:
            vel = 1

        # получает нажатия клавиш
        keys = pygame.key.get_pressed()
        data = ""
        # движения игрока
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if player["x"] - vel - PLAYER_RADIUS - player["score"] >= 0:
                player["x"] = player["x"] - vel

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if player["x"] + vel + PLAYER_RADIUS + player["score"] <= 5000:
                player["x"] = player["x"] + vel

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            if player["y"] - vel - PLAYER_RADIUS - player["score"] >= 0:
                player["y"] = player["y"] - vel

        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if player["y"] + vel + PLAYER_RADIUS + player["score"] <= 4000:
                player["y"] = player["y"] + vel


        data = "move " + str(player["x"]) + " " + str(player["y"])

        # отправка данных на сервер и получение данных об игроках
        balls, black_holes, players, game_time = server.send(data)

        camera_x = player["x"] - W // 2
        camera_y = player["y"] - H // 2

        for event in pygame.event.get():
            # закрытие окна при нажатии крестика
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                # закрытие окна при нажатии esc
                if event.key == pygame.K_ESCAPE:
                    run = False

        # перерисовка окна и его обновление
        redraw_window(WIN, players, balls, black_holes, game_time, player["score"], camera_x, camera_y)
        pygame.display.update()

    server.disconnect()
    pygame.quit()
    quit()


if __name__ == "__main__":
    root = tk.Tk()
    menu = MainMenu(root)
    root.mainloop()