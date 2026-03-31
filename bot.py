import telebot, requests,os
from random import sample
from telebot import types
from flask import Flask, request

TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_KEY = os.environ.get("TMDB_API_KEY")
print("TELEGRAM_TOKEN:", TOKEN)
print("TMDB_API_KEY:", API_KEY)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

WEBHOOK_URL = f"https://tmdb-tg.onrender.com/{TOKEN}"

def setup_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'ok'

@app.route("/")
def index():
    return "Бот онлайн"

class Movie:
    def __init__(self, data):
        self.data = data

    def infoMovie(self):
        title = self.data.get("title") or self.data.get("original_title")

        release_date = self.data.get("release_date")
        year = release_date.split("-")[0] if release_date else "Год не указан"

        tagline = self.data.get("tagline") or None

        overview = self.data.get("overview") or "Описание отсутствует"

        vote_average = (
            round(self.data.get("vote_average", 0), 1)
            if self.data.get("vote_count")
            else "Данных об оценке нет"
        )

        caption = f"{title} ({year})\n"

        if tagline:
            caption += f"{tagline}\n"

        caption += f"\n{overview}\n\nОценка: {vote_average}"

        poster = None
        if self.data.get("poster_path"):
            poster = "https://image.tmdb.org/t/p/w500" + self.data["poster_path"]

        videos = self.data.get("videos", {}).get("results", [])
        trailer_url = None

        for video in videos:
            if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                trailer_url = f"https://www.youtube.com/watch?v={video['key']}"
                break

        if not trailer_url:
            for video in videos:
                if video.get("site") == "YouTube":
                    trailer_url = f"https://www.youtube.com/watch?v={video['key']}"
                    break

        site = f"https://www.themoviedb.org/movie/{self.data.get('id')}"

        return {
            "caption": caption,
            "poster": poster,
            "trailer": trailer_url,
            "site": site
        }

    def title(self):
        title = self.data.get("title") or self.data.get("original_title")

        release_date = self.data.get("release_date")
        year = release_date.split("-")[0] if release_date else "Год не указан"

        caption = f"{title} ({year})\n🎬 Нажми «Читать далее», чтобы открыть карточку фильма"

        return {"caption": caption, "id": self.data.get("id")}

def superMovie(user_url, user_params, mode):
    super_params = {"api_key": API_KEY,
                    "language": "ru-RU"}
    super_url = "https://api.themoviedb.org/3"
    url = super_url+ user_url
    params = super_params | user_params
    if mode == "id":
        params |= {"append_to_response" : "videos"}
    try:
        response = requests.get(url,params=params)
        if response.status_code == 200:
            data = response.json()
            if mode == "id":
                movie_obj = Movie(data)
                return movie_obj.infoMovie()
            else:
                movie_data = data["results"]
                if mode == "top":
                    list_of_movies = movie_data[:min(3,len(movie_data))]
                
                elif mode == "random":
                    list_of_movies = sample(movie_data, min(3, len(movie_data)))
                
                list_for_answer = []
                for i in list_of_movies:
                    movie_obj = Movie(i)
                    list_for_answer.append(movie_obj.title())
                return list_for_answer
        elif response.status_code == 404:
            print("Информация не найдена")
            return "Информация не найдена"
        else:
            print(f' Ошибка API: {response.status_code}')
            return f' Ошибка API: {response.status_code}'
    except Exception as e:
        print(f'Ошибка подключения: {e}')
        return f'Ошибка подключения: {e}'
    
def error(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    button_1 = types.InlineKeyboardButton("Телеграм канал разработчика",url="https://t.me/SWIMER121")
    markup.add(button_1)
    bot.send_message(message.chat.id,"Извините, бот испытывает неполадки. Напишите позднее или обратитесь в поддержку",reply_markup=markup)

def choiceMovie(list_of_movies,message):
    for i in list_of_movies:
        caption = i["caption"]
        markup = types.InlineKeyboardMarkup(row_width=1)
        button_1 = types.InlineKeyboardButton("Читать далее", callback_data=f"id:{i['id']}")
        markup.add(button_1)
        bot.send_message(message.chat.id,caption,reply_markup=markup)

genre_list = {
    "боевик": 28,
    "приключения": 12,
    "анимация": 16,
    "комедия": 35,
    "криминал": 80,
    "документальный": 99,
    "драма": 18,
    "семейный": 10751,
    "фэнтези": 14,
    "история": 36,
    "ужасы": 27,
    "музыка": 10402,
    "мюзикл": 10402,
    "детектив": 9648,
    "романтика": 10749,
    "фантастика": 878,
    "телевизионный фильм": 10770,
    "триллер": 53,
    "военный": 10752,
    "вестерн": 37
}

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id,"""🎬 Привет! Добро пожаловать в кино-бота

Я работаю с базой данных TMDb и умею быстро находить фильмы, показывать их описание, рейтинг и даже трейлеры 🎥
Ты можешь просто написать название фильма или воспользоваться командами ниже

Вот что я умею 👇

🚀 /start — начать работу с ботом
🔎 /search — поиск фильма по названию
⭐ /top — лучшие фильмы
🔥 /popular — популярные фильмы
📈 /trending — фильмы в тренде
🎭 /genre — фильмы по жанру
❓ /help — помощь и обратная связь с разработчиком

Выбери команду или напиши название фильма — и я найду для тебя что-нибудь интересное 🍿""")

@bot.message_handler(commands=["help"])
def help(message):
    text = """Команды бота:
/start — начать работу с ботом и получить общее описание
/search <название> — поиск фильма по названию  
Пример: /search Interstellar
/top — подбор фильмов с высоким рейтингом ⭐
/popular — список популярных фильмов 📊
/trending — фильмы, которые сейчас в тренде 📈
/genre <жанр> <жанр> — подбор фильмов по жанру  
Пример: /genre драма

Доступные жанры:
- боевик ⚔️
- приключения 🧭
- анимация 🎞️
- комедия 🎭
- криминал 🔎
- документальный 📚
- драма 🎬
- семейный 👨‍👩‍👧‍👦
- фэнтези 🧙
- история 🏛️
- ужасы 🕷️
- музыка 🎵
- детектив 🕵️
- романтика ❤️
- фантастика 🚀
- триллер 🔥
- военный 🪖
- вестерн 🤠

Инструкции:
- После команды /search обязательно указывайте название фильма
- После команды /genre указывайте один или несколько жанров из списка через пробел с маленькой буквы
- Все команды вводятся через слэш (/)
- При неверном вводе команда не будет обработана

При возникновении ошибок или некорректной работы повторите запрос позже или обратитесь к разработчику."""

    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton("Связаться с разработчиком", url="https://t.me/SWIMER121")
    markup.add(button)

    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(commands=["search","top","trending","popular"])
def search(message):
    command = message.text.split()[0][1:]
    if command == "search":
        query = " ".join(message.text.split()[1:])
        if not query:
            bot.reply_to(message, "🔎 Напиши название фильма после команды.\n\nПример: /search Интерстеллар")
            return
        list_of_movies = superMovie("/search/movie",{"query":query,"sort_by": "popularity.desc"},"top")
        
    elif command == "top":
        list_of_movies = superMovie("/movie/top_rated",{},"top")
    
    elif command == "trending":
        list_of_movies = superMovie("/trending/movie/week",{},"top")
        
    elif command == "popular":
        list_of_movies = superMovie("/movie/popular",{},"random")
    if not list_of_movies:
        bot.send_message(message.chat.id,"😢 По твоему запросу ничего не нашлось\n\nПопробуй изменить запрос или выбрать другой жанр")
    if type(list_of_movies) == str:
        error(message)
    else:
        choiceMovie(list_of_movies,message)

@bot.message_handler(commands=["genre"])
def discover(message):
    genre = message.text.split()[1:]
    if not genre:
        bot.send_message(message.chat.id,"🎭 Кажется, ты забыл написать жанр 😅\nПопробуй, например:\n /genre боевик комедия\n\nСписок доступных жанров есть в /help")
    genres = []
    for i in genre:
        if i in genre_list:
            genres.append(genre_list[i])
    
    list_of_movies = superMovie("/discover/movie",{"with_genres": ",".join(map(str, genres)), "vote_average.gte": 7, "vote_count.gte": 200},"random")
    if type(list_of_movies) == str:
        error(message)
    else:
        choiceMovie(list_of_movies,message)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if "id:" in call.data:
        movie_id = call.data.split(":")[1]
        movie = superMovie(f"/movie/{movie_id}",{},"id")
        markup = types.InlineKeyboardMarkup()
        if movie["trailer"]:
            button_1 = types.InlineKeyboardButton("Трейлер", url=movie["trailer"])
            markup.add(button_1)
        if movie["site"]:
            button_1 = types.InlineKeyboardButton("Больше информации", url=movie["site"])
            markup.add(button_1)
        if movie["poster"]:
            bot.send_photo(call.message.chat.id,caption=f"{movie['caption']}",photo=movie["poster"],reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id,f"{movie['caption']}",reply_markup=markup)
            
@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text[0] == "/":
        bot.send_message(message.chat.id,"🤔 Неизвестная команда.\n\nПопробуй /help или /start 🎬")
    else:
        bot.send_message(message.chat.id,"🎬 Я могу работать только с командами или названием фильма.\n\nПопробуй /help")

@bot.message_handler(content_types=["photo","document","video"])
def handle_photo(message):
    bot.send_message(message.chat.id,"📸 Я не умею обрабатывать эти данные 😅\n\nНапиши название фильма или используй команды /help")



if __name__ == "__main__":
    setup_webhook()
    print("Webhook set to:", WEBHOOK_URL)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
