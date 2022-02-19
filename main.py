import discord
from discord.ext import commands
from datetime import datetime
import os
import pytz
import re
import csv


bot = commands.Bot(command_prefix="!")


@bot.event
async def on_ready():
  print("Bot is ready!")


# ctx - context (основная информация о сообщении, которое вызвало функцию)
# ch - канал для которого требуется составить отчет по посещаемости
# start - время с которого будут братся логи (начало пары) format = '%d/%m/%y|%H:%M:%S'
# end -время до которого будут братся логи (конец пары) format = '%d/%m/%y|%H:%M:%S'
# example: !посещения SUAI 18/02/22|00:00:00 18/02/22|23:59:59
@bot.command()
async def посещения(ctx, ch, start, end):
  # Упоковка всех каналов сервера в словарь
  channels = [channel for channel in ctx.guild.channels]
  c_names = [chs.name for chs in channels]
  dic_ch = dict(zip(c_names, channels))

  # Проверка наличия роли "stuff" у пользователя
  author = await ctx.guild.fetch_member(ctx.author.id)
  if ("stuff" not in [role.name for role in author.roles]):
    await ctx.send(f"User \"@{author.id}\" haven't role \"stuff\"")
    return

  # Проверка наличия канала ch на сервере
  if (ch not in dic_ch.keys()):
    await ctx.send(f"Channel \"{ch}\" isn't exist!")
    return
  channel_id = dic_ch[ch].id
  
  format = '%d/%m/%y|%H:%M:%S%z'
  date_time_start_local = datetime.strptime(start + "+0300", format)
  date_time_end_local = datetime.strptime(end + "+0300", format)
  start_utc = date_time_start_local.astimezone(pytz.utc).replace(tzinfo=None)
  end_utc = date_time_end_local.astimezone(pytz.utc).replace(tzinfo=None)

  # Словарь хранящий пользователей и логи с вязанные с ними
  # Структура: 
  #{ 
  #  user_id1 : [log_of_user1_1, log_of_user1_2, log_of_user1_3, ...],
  #  user_id2 : [log_of_user2_1, log_of_user2_2, log_of_user2_3, ...],
  #  ...
  #}
  dic = dict()

  # Функция добавляет текущий log в словарь к пользователю с user_id 
  def add_log_of_user(user_id, log):
    if (user_id not in dic.keys()):
      dic[user_id] = [log]
    else:
      dic[user_id].append(log)

  # Цикл просматривает историю сообщений канала ch с времени date_time_start_local до date_time_end_local
  async for elem in ctx.channel.history(limit=None, after=start_utc, before=end_utc):
    # Просмотр только сообщений от "Dyno"
    if (elem.author.name == "Dyno"):
      # Поис по регулярному выражению: первый элемент всегда id пользователя, второй id канала (может и не быть)
      ids = re.findall("\d+", elem.embeds[0].description)
      user_id = ids[0]
      # Если размер ids = 2, то сообщение содержит в себе слова либо joined, либо left
      # Иначе пользователь перешел с другово канала
      if (len(ids) == 2):
        channel_id_in_embed = ids[1]
        # Если канал из лога совпадает с каналом ch (аргумент функции),
        #   то добавляем данный лог к текущему пользователю
        if (channel_id_in_embed == str(channel_id)):
          if (elem.embeds[0].description.find("joined") != -1):
            add_log_of_user(user_id, ("joined", elem.embeds[0].timestamp))
          else:
            add_log_of_user(user_id, ("left", elem.embeds[0].timestamp))
      else:
        # Если канал из лога совпадает с каналом ch (аргумент функции),
        #   то добавляем данный лог к текущему пользователю
        # Example: лог содержит подстроку "`#{channel_name_1}` -> `#{channel_name_2}`"
        #   Если искомый канал - ch находится на позиции channel_name_1, то значит пользователь вышел с канала ch
        #   Если искомый канал - ch находится на позиции channel_name_2, то значит пользователь вошел в канала ch
        #   Иначе лог не содержит названия канала ch - пропускаем
        channels_names = re.findall("`#(.*?)`", elem.embeds[0].description)
        if (channels_names[0].find(ch) != -1):
          add_log_of_user(user_id, ("left", elem.embeds[0].timestamp))
        elif (channels_names[1].find(ch) != -1):
          add_log_of_user(user_id, ("joined", elem.embeds[0].timestamp))
        else:
          continue
       
  # Создаем файл
  with open('output.tsv', 'w', newline='') as f_output:
    # Проходим по всему словарю
    for user_id in dic.keys():
      # Подтягиваем участника сервера (для нахождения nickname'а, т.к. он заполняется как "ФИО группа")
      member = await ctx.guild.fetch_member(user_id)
      logs = dic[user_id]

      # Добавляем фиктивные записи для пользователя
      #   Если нет первой записи о присоединении к каналу
      #   или если нет последней записи о выходе из канала
      if (logs[0][0] == "left"):
        logs.insert(0, ("joined", 0))
      if (logs[-1][0] == "joined"):
        logs.append(("left", 0))

      # Функция возвращает генератор, который делит входной список на пары [[1, 2], [3, 4], ...]
      def chunk_using_generators(lst, n):
        for i in range(0, len(lst), n):
          yield lst[i:i + n]
  
      logs = chunk_using_generators(logs, 2)
      # Для каждой пары генерируем строку
      for pair in logs:
        # pair имеет структуру [ ("joined", timestamp1), ("left", timestamp2) ]
        diff = ""
        start = pair[0][1]
        end = pair[1][1]
        # Вычисляем продолжительность текущей сессии (если timestamp1 и timestamp2 не равны 0)
        if (pair[0][1] != 0 and pair[1][1] != 0):
          diff = pair[1][1] - pair[0][1]
        if (pair[0][1] == 0):
          start = ""
        else:
          start = pair[0][1].astimezone(pytz.timezone('Europe/Moscow'))
        if (pair[1][1] == 0):
          end = ""
        else:
          end = pair[1][1].astimezone(pytz.timezone('Europe/Moscow'))

        # Составление строки
        row = [member.display_name, start, end, diff]
        # Запись строки в файл
        tsv_output = csv.writer(f_output, delimiter='\t')
        tsv_output.writerow(row)

  # Отправка файла пользователю, который воспользовался ботом
  file = discord.File("output.tsv")
  await ctx.author.send(file=file, content="")
        
        
bot.run(os.environ['TOKEN'])
