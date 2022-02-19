# AttendenceDiscordBot

# Установка Linux

Клонировать репозиторий:
```
$ git clone https://github.com/xincas/AttendenceDiscordBot.git
$ cd AttendenceDiscordBot/
```

Установить библиотеку discord:
```
$ pip install discord
```

Создать переменную окружения TOKEN:
```
$ export TOKEN="your token"
```

Запустить start.sh:
```
$ sh start.sh
```

# Как использовать

В чате логирования использовать команду `!посещения (channel_name) (time_start) (time_end)`.

Время в формате `ДД/ММ/ГГ|ЧЧ/ММ/СС`

Затем бот отправляет вам в личные сообщение файл `output.tsv`
