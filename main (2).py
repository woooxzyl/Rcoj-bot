import asyncio
import json
import re
import os
from datetime import datetime, timedelta
import discord
import pytz
from discord import Embed, Intents
from discord.ext import commands
from mcrcon import MCRcon
import schedule
import asyncio
import os


intents = Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

file_path = os.path.join(os.getcwd(), 'statuses.json')

RCON_DATA_1 = {"ip": "65.109.33.151", "port": 25575, "password": "default_rcon_password_1"}
RCON_DATA_2 = {"ip": "default_rcon_ip_2", "port": 25576, "password": "default_rcon_password_2"}
RCON_DATA_3 = {"ip": "default_rcon_ip_3", "port": 25576, "password": "default_rcon_password_3"}

DISCORD_CHANNEL_1 = 1207750266779205642
DISCORD_CHANNEL_2 = 1207750265944547348  
DISCORD_CHANNEL_3 = 1207750264728068207 
SEND_CHANNEL_ID = 1192489740361023499

RCON_NEWS = 1207750267785838593
NEWS_CHANNEL_ID = 1207750268712788009
ADMIN_IDS = {939423912155029504, 979336672808431627}
DEVELOPER_ID = 939423912155029504
BLACKLIST = {}
BLOCK_DURATION_PATTERN = re.compile(r'(?P<duration>\d+)(?P<unit>[smhdwMy]?)')

async def send_block_message(ctx, member, duration_delta, reason, moderator):
  end_time = datetime.utcnow() + duration_delta
  formatted_end_time = end_time.strftime('%Y-%m-%d %H:%M:%S')

  block_message = (
      f'**[БЛОКИРОВКА]**\n\n'
      f'Заблокирован: {member.mention}\n'
      f'Модератор: {moderator.mention}\n'
      f'Окончания: {formatted_end_time}\n'
      f'Причина: {reason}'
  )

  await ctx.send(block_message)

forbidden_commands = {
    "default_rcon": [
      "spigot:restart", "spigot", "psudo", "cmi:sudo", "cmi sudo", "minecraft:sudo", "sudo", "minecraft", "cmi", "psudo", "cmi:ban", "cmi ban", "ban", "mute", "kick", "unban", "pardon", "ban-ip", "minecraft:ban", "minecraft:mute", "minecraft:kick",
        "stop", "reload", "restart", "minecraft:stop", "minecraft:reload", "minecraft:restart", "rl", "bukkit:rl",
        "bukkit:reload"
    ],
    "rcon+": [
        "spigot:restart", "spigot", "psudo", "cmi:sudo", "cmi sudo", "minecraft:sudo", "sudo", "stop", "reload", "restart", "minecraft:stop", "minecraft:reload", "minecraft:restart", "rl", "bukkit:rl",
        "bukkit:reload"
    ],
    "full_rcon": ["spigot:restart", "spigot", "psudo", "cmi:sudo", "cmi sudo", "minecraft:sudo", "sudo"]
}

def clean_command(command):
  cleaned_command = re.sub(r'[^a-zA-Z0-9_]', '', command)
  return cleaned_command

async def check_rcon_status(ctx):
    user = ctx.author

    rcon_plus_role = discord.utils.get(ctx.guild.roles, name="rcon+")
    full_rcon_role = discord.utils.get(ctx.guild.roles, name="full_rcon")
    default_rcon_role = discord.utils.get(ctx.guild.roles, name="default_rcon")

    if rcon_plus_role in user.roles:
        return "rcon+"
    elif full_rcon_role in user.roles:
        return "full_rcon"
    elif default_rcon_role in user.roles:
        return "default_rcon"
    else:
        return "Снять"

async def get_role(guild, role_name):
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        role = await guild.create_role(name=role_name)
    return role

async def save_all_members_statuses():
  guild = bot.get_guild(1178642744533602334)
  if guild:
      await create_roles(guild)
      status_data = {}

      for member in guild.members:
          if not member.bot:
              status_data[member.name] = [role.name for role in member.roles]

      with open('statuses.json', 'w', encoding='utf-8') as file:
          json.dump(status_data, file, indent=2, ensure_ascii=False)


async def load_all_members_statuses():
  try:
      with open('statuses.json', 'r', encoding='utf-8') as file:
          status_data = json.load(file)

      guild = bot.get_guild(1178642744533602334)
      if guild:
          await create_roles(guild)

          for member_name, roles in status_data.items():
              member = discord.utils.get(guild.members, name=member_name)
              if member:
                  await member.edit(roles=[await get_role(guild, role) for role in roles])

  except FileNotFoundError:
      pass


async def update_member_status(member):
  # Получаем список ролей участника
  user_roles = [role.name for role in member.roles]

  # Проверяем наличие ролей и устанавливаем соответствующую роль
  if 'rcon' in user_roles:
      role_name = 'rcon'
  elif 'full_rcon' in user_roles:
      role_name = 'full_rcon'
  else:
      role_name = 'default_rcon'

  role = await get_role(member.guild, role_name)
  await member.add_roles(role)

log_file_path = 'logs.txt'
log_channel_id = 1200762618747568178
max_logs_to_display = 50

# Очистка логов раз в 48 часов
def clear_logs():
    try:
        # Удаление старого файла
        os.remove(log_file_path)
    except FileNotFoundError:
        pass
    
    # Создание нового файла
    with open(log_file_path, 'w') as log_file:
        log_file.write("Logs cleared at: " + str(datetime.now()))


# Запуск очистки логов каждые 48 часов
schedule.every(48).hours.do(clear_logs)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

    # Асинхронная функция для периодической проверки расписания
    async def job():
        while True:
            await asyncio.sleep(1)
            schedule.run_pending()

    # Запуск асинхронной задачи
    bot.loop.create_task(job())

@bot.event
async def on_command(ctx):
    # Преобразование времени к UTC+5
    utc_time = datetime.utcnow()
    time_zone = pytz.timezone('Asia/Yekaterinburg')
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(time_zone)

    timestamp = local_time.strftime('%Y-%m-%d %H:%M:%S')

    # Получение объекта автора и его аватарки
    author = ctx.message.author

    # Создание Embed-сообщения
    embed = Embed(color=0x7531FF)
    embed.title = author.name  # Ник пользователя как заголовок
    embed.description = f"**Команда:** {ctx.message.content}"
    embed.set_footer(text=f"Время выполнения: {timestamp}")

    # Добавление аватарки пользователя
    avatar_url = author.avatar.url if author.avatar else None
    embed.set_thumbnail(url=avatar_url)

    # Отправка логов в канал
    log_channel = bot.get_channel(log_channel_id)
    if log_channel:
        await log_channel.send(embed=embed)

        # Запись лога в файл с учетом ID пользователя
        with open(log_file_path, 'a') as log_file:
            log_file.write(f"{timestamp} - {author.id}: {ctx.message.content}\n")

@bot.command(name='logs')
async def display_logs(ctx, user: discord.User = None):
    # Проверяем, есть ли у пользователя необходимая роль
    required_role_id = 1205788506992152616
    required_role = discord.utils.get(ctx.guild.roles, id=required_role_id)

    if required_role and required_role in ctx.author.roles:
        try:
            with open(log_file_path, 'r') as log_file:
                logs = log_file.readlines()
        except FileNotFoundError:
            logs = []

        if user:
            filtered_logs = [log for log in logs if f"{user.id}:" in log]
            embed_title = f"Логи для {user.name}#{user.discriminator}"
        else:
            filtered_logs = logs
            embed_title = "Общие логи"

        embed = Embed(color=0x7531FF)
        embed.title = embed_title
        embed.set_footer(text="Логи команд")

        for log_line in filtered_logs:
            log_parts = log_line.strip().split(" - ")
            timestamp = log_parts[0]
            log_content = log_parts[1].split(": ", 1)
            author_id = log_content[0]
            command = log_content[1]

            if user:
                # Вывод для конкретного пользователя
                embed.add_field(name=f"({timestamp}) ***{command}***", value="\u200b", inline=False)
            else:
                # Вывод для всех пользователей
                author = ctx.guild.get_member(int(author_id))
                author_name = author.name if author else "Неизвестный пользователь"
                embed.add_field(name=f"{author_name} - ({timestamp})", value=f"***{command}***", inline=False)

        if not filtered_logs:
            embed.add_field(name='\u200b', value="Нет логов для отображения.", inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send("У вас нет доступа к просмотру логов.")

@bot.command(name='setstatus')
async def set_user_status(ctx, member: discord.Member = None, status = None):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send('Вы не являетесь администратором бота.')
        return

    if member is None or status is None:
        await ctx.send('Использование команды: `!setstatus <участник> <статус>`')
        return

    rcon_plus_role = await get_role(member.guild, 'rcon+')
    full_rcon_role = await get_role(member.guild, 'full_rcon')
    default_rcon_role = await get_role(member.guild, 'default_rcon')

    if status == 'default_rcon':
        await member.remove_roles(rcon_plus_role, full_rcon_role)
        await member.add_roles(default_rcon_role)
    elif status == 'rcon+':
        await member.add_roles(rcon_plus_role)
        await member.remove_roles(full_rcon_role, default_rcon_role)
    elif status == 'full_rcon':
        await member.add_roles(full_rcon_role)
        await member.remove_roles(rcon_plus_role, default_rcon_role)
    else:
        await ctx.send('Неверный статус. Допустимые статусы: default_rcon, rcon+, full_rcon.')
        return

    await ctx.send(f'Статус участника {member.mention} установлен на `{status}`.')
    await asyncio.sleep(1)

@bot.command(name='status')
async def check_user_status_command(ctx, member: discord.Member = None):
    if member is None:
        rcon_plus_role = await get_role(ctx.guild, 'rcon+')
        full_rcon_role = await get_role(ctx.guild, 'full_rcon')
        default_rcon_role = await get_role(ctx.guild, 'default_rcon')

        if rcon_plus_role in ctx.author.roles:
            await ctx.send('Ваш статус: `rcon+`')
        elif full_rcon_role in ctx.author.roles:
            await ctx.send('Ваш статус: `full_rcon`')
        elif default_rcon_role in ctx.author.roles:
            await ctx.send('Ваш статус: `default_rcon`')
        else:
            await ctx.send('Ваш статус: `обычный ркон`')
    else:
        rcon_plus_role = await get_role(ctx.guild, 'rcon+')
        full_rcon_role = await get_role(ctx.guild, 'full_rcon')
        default_rcon_role = await get_role(ctx.guild, 'default_rcon')

        if rcon_plus_role in member.roles:
            await ctx.send(f'Статус участника {member.mention}: `rcon+`')
        elif full_rcon_role in member.roles:
            await ctx.send(f'Статус участника {member.mention}: `full_rcon`')
        elif default_rcon_role in member.roles:
            await ctx.send(f'Статус участника {member.mention}: `default_rcon`')
        else:
            await ctx.send(f'Статус участника {member.mention}: `обычный ркон`')

@bot.command(name='set_rcon1')
async def set_rcon_credentials_1(ctx, ip, port, password):
    await set_rcon_credentials(ctx, ip, port, password, RCON_DATA_1, DISCORD_CHANNEL_1, SEND_CHANNEL_ID)

@bot.command(name='set_rcon2')
async def set_rcon_credentials_2(ctx, ip, port, password):
    await set_rcon_credentials(ctx, ip, port, password, RCON_DATA_2, DISCORD_CHANNEL_2, SEND_CHANNEL_ID)

@bot.command(name='set_rcon3')
async def set_rcon_credentials_3(ctx, ip, port, password):
    await set_rcon_credentials(ctx, ip, port, password, RCON_DATA_3, DISCORD_CHANNEL_3, SEND_CHANNEL_ID)

async def set_rcon_credentials(ctx, ip, port, password, rcon_data, discord_channel_id, send_channel_id):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send('Вы не являетесь администратором бота.')
        return

    if ctx.channel.id != send_channel_id:
        await ctx.send('Эту команду можно использовать только в специальном канале.')
        return

    rcon_data["ip"] = ip
    rcon_data["port"] = int(port)
    rcon_data["password"] = password
    await ctx.send(f'Данные RCON обновлены для сервера {rcon_data["ip"]}:{rcon_data["port"]}')

@bot.command(name='block')
async def block_user(ctx, member: discord.Member = None, duration_str: str = '30m', *, reason: str = 'Нарушение правила сервера'):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send('❌ У вас нет разрешения на использование этой команды.')
        return

    if member is None:
        await ctx.send('❌ Использование команды: `!block <участник> [длительность] [причина]`')
        return

    try:
        member = await bot.fetch_user(member.id)
    except discord.errors.NotFound:
        await ctx.send('❌ Указанный участник не найден.')
        return

    duration_match = BLOCK_DURATION_PATTERN.match(duration_str)
    if not duration_match:
        await ctx.send('❌ Неверный формат длительности блокировки. Используйте цифры с указанием единицы времени (s, m, h)')
        return

    duration, unit = int(duration_match.group('duration')), duration_match.group('unit')
    duration_delta = timedelta(seconds=duration * {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800, 'M': 2629746, 'y': 31556952}.get(unit, 1))

    moderator = ctx.author
    BLACKLIST[member.id] = {'end_time': datetime.utcnow() + duration_delta, 'reason': reason, 'moderator': moderator.id}

    await send_block_message(ctx, member, duration_delta, reason, moderator)

    await asyncio.sleep(duration_delta.total_seconds())
    if member.id in BLACKLIST:
        del BLACKLIST[member.id]
        await ctx.send(f'RCON снял блокировку с участника {member.mention}.')

    save_blacklist_to_file()

@bot.command(name='unblock')
async def unblock_user(ctx, member: discord.Member = None):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send('❌ У вас нет разрешения на использование этой команды.')
        return

    if member is None:
        await ctx.send('❌ Использование команды: `!unblock <участник>`')
        return

    try:
        member = await bot.fetch_user(member.id)
    except discord.errors.NotFound:
        await ctx.send('❌ Указанный участник не найден.')
        return

    if member.id in BLACKLIST:
        del BLACKLIST[member.id]
        await ctx.send(f'RCON снял блокировку с участника {member.mention}.')
    else:
        await ctx.send('❌ Участник не заблокирован.')

    save_blacklist_to_file()

@bot.command(name='blocklist')
async def blocklist(ctx):
    if not BLACKLIST:
        await ctx.send('❌ Черный список пуст.')
        return

    blocklist_message = 'Список заблокированных участников:\n\n'
    for member_id, data in BLACKLIST.items():
        member = bot.get_user(member_id)
        if member:
            formatted_end_time = data['end_time'].strftime('%Y-%m-%d %H:%M:%S')
            moderator = bot.get_user(data["moderator"])
            moderator_mention = moderator.mention if moderator else "Неизвестный модератор"

            blocklist_message += (
                f'**Заблокирован**: {member.mention}\n'
                f'**Окончания**: {formatted_end_time}\n'
                f'**Причина**: {data["reason"]}\n'
                f'**Модератор**: {moderator_mention}\n\n'
            )

    await ctx.send(blocklist_message)

def save_blacklist_to_file():
    with open('blacklist.txt', 'w') as file:
        for member_id, data in BLACKLIST.items():
            formatted_end_time = data['end_time'].strftime('%Y-%m-%d %H:%M:%S')
            file.write(f'{member_id} | {formatted_end_time} | {data["reason"]} | {data["moderator"]}\n')


@bot.command(name='cmd')
async def send_rcon_command(ctx, *, command=None):
    if command is None:
      # Если команда не указана, отправляем сообщение об использовании с красивыми эмодзи
      usage_message = (
          '**Использование команды !cmd**\n'
          'Вы должны указать команду, которую хотите выполнить.\n\n'
          'Пример:\n'
          '`!cmd ваша_команда`'
      )
      await ctx.send(usage_message)
      return
    channel_id = ctx.channel.id

    if channel_id == DISCORD_CHANNEL_1:
        await send_rcon_command(ctx, command, RCON_DATA_1)
    elif channel_id == DISCORD_CHANNEL_2:
        await send_rcon_command(ctx, command, RCON_DATA_2)
    elif channel_id == DISCORD_CHANNEL_3:
        await send_rcon_command(ctx, command, RCON_DATA_3)
    else:
        await ctx.send('Вы не можете использовать эту команду в данном канале.')

async def send_rcon_command(ctx, command, rcon_data):
    if ctx.author.id in BLACKLIST:
        info = BLACKLIST[ctx.author.id]

        moderator_member = await bot.fetch_user(int(info["moderator"]))

        block_message = (
            f'Вы заблокирован в ркон боте\n'
            f'Заблокировал: {moderator_member.mention if moderator_member else "Неизвестный пользователь"}\n'
            f'Причина: {info["reason"]}\n'
            f'Окончания: {info["end_time"].strftime("%Y-%m-%d %H:%M:%S")}'
        )

        await ctx.send(block_message)
        return

    user_roles = [role.name.lower() for role in ctx.author.roles]
    rcon_roles = ["default_rcon", "rcon+", "full_rcon"]

    # Проверка для каждой роли пользователя
    for role in user_roles:
      role_commands = forbidden_commands.get(role, [])
      if role_commands and command.lower() in role_commands:
          await ctx.send(f'Выполнение команды "{command}" запрещено для вашей роли.')
          return

    if any(role in rcon_roles for role in user_roles):
        cleaned_command = clean_command(command)
        await ctx.send(f'Отправляю команду: `{cleaned_command}`')
        response_data = await send_rcon_command_to_server(cleaned_command, rcon_data)

        if "error" in response_data:
            await ctx.send(response_data["error"])
        else:
            response_data["original_response"]
            cleaned_response = response_data["cleaned_response"]
            await ctx.send(f'Ответ: ```{cleaned_response}```')
    else:
        await ctx.send('Вы не можете выполнить эту команду.')

async def send_rcon_command_to_server(command, rcon_data):
    try:
        with MCRcon(host=rcon_data["ip"], port=rcon_data["port"], password=rcon_data["password"]) as mcr:
            response = mcr.command(command)
            cleaned_response = re.sub("§[0-9a-fk-or]", "", response)
            return {"original_response": response, "cleaned_response": cleaned_response}
    except Exception as e:
        return {"error": f"Ошибка при выполнении команды: {str(e)}"}

def clean_command(command):
    return command

@bot.command(name='ip1')
async def set_ip1(ctx, ip, port):
    await set_server_info(ctx, ip, port, DISCORD_CHANNEL_1, 1)

@bot.command(name='ip2')
async def set_ip2(ctx, ip, port):
    await set_server_info(ctx, ip, port, DISCORD_CHANNEL_2, 2)

@bot.command(name='ip3')
async def set_ip3(ctx, ip, port):
    await set_server_info(ctx, ip, port, DISCORD_CHANNEL_3, 3)

async def set_server_info(ctx, ip, port, discord_channel_id, server_number):
    news_channel = bot.get_channel(NEWS_CHANNEL_ID)
    if news_channel is not None:
        server_channel = bot.get_channel(discord_channel_id)


        server_emoji = "\U0001F4E2"

        embed = discord.Embed(title=f"{server_emoji} Открыт сервер под номером #{server_number}", color=0x7531FF)
        embed.add_field(name="IP", value=f"{ip}:{port}", inline=False)
        embed.add_field(name="Канал", value=server_channel.mention, inline=False)

        await news_channel.send(embed=embed)
        await ctx.send(f'{server_emoji} Информация о сервере #{server_number} успешно отправлена в канал новостей.')
    else:
        await ctx.send('Канал новостей не найден. Пожалуйста, убедитесь, что NEWS_CHANNEL_ID указан верно.')

@bot.command(name='rstatus')
async def reset_user_status(ctx, member: discord.Member = None):
    if ctx.author.id not in ADMIN_IDS:
        await ctx.send('Вы не являетесь администратором бота.')
        return

    if member is None:
        await ctx.send('Использование команды: `!rstatus <участник>`')
        return

    default_rcon_role = await get_role(member.guild, 'default_rcon')
    rcon_plus_role = await get_role(member.guild, 'rcon+')
    full_rcon_role = await get_role(member.guild, 'full_rcon')

    await member.remove_roles(rcon_plus_role, full_rcon_role)
    await member.add_roles(default_rcon_role)

    await ctx.send(f'Статус участника {member.mention} сброшен. Теперь у него статус `default_rcon`.')

ADD_ADMIN_EMOJI = "\U0001F44D"  # Эмодзи для подтверждения
REMOVE_ADMIN_EMOJI = "\U0000274C"  # Эмодзи для удаления

@bot.command(name='radmin')
async def remove_admin(ctx, member: discord.Member = None):
    if not member:
        await ctx.send('Использование команды: `!radmin @участник`')
        return

    if ctx.author.id not in ADMIN_IDS:
        await ctx.send('Вы не являетесь администратором бота.')
        return

    if member.id not in ADMIN_IDS:
        await ctx.send(f'{REMOVE_ADMIN_EMOJI} Участник {member.mention} не является администратором.')
        return

    ADMIN_IDS.remove(member.id)
    await ctx.send(f'{REMOVE_ADMIN_EMOJI} Участник {member.mention} удален из списка администраторов.')


@bot.command(name='setadmin')
async def set_admin(ctx, member: discord.Member = None):
    if not member:
        await ctx.send('Использование команды: `!setadmin @участник`')
        return

    if ctx.author.id not in ADMIN_IDS:
        await ctx.send('Вы не являетесь администратором бота.')
        return

    if member.id in ADMIN_IDS:
        await ctx.send(f'{REMOVE_ADMIN_EMOJI} Участник {member.mention} уже является администратором.')
        return

    ADMIN_IDS.add(member.id)
    await ctx.send(f'{ADD_ADMIN_EMOJI} Участник {member.mention} добавлен в список администраторов.')

bot.remove_command('help')


@bot.command(name='cmds')
async def send_help(ctx):
    if ctx.author.id in ADMIN_IDS:
        admin_help_message = (
            "**Доступные команды для администраторов:**\n\n"
            "`!cmd <ваша_команда>` - отправить команду на сервер Minecraft\n"
            "`!status <участник>` - проверить статус участника\n"
            "`!setadmin <участник>` - добавить участника в список администраторов\n"
            "`!radmin <участник>` - удалить участника из списка администраторов\n"
            "`!block <участник> [длительность] [причина]` - заблокировать участника на сервере\n"
            "`!unblock <участник>` - снять блокировку с участника\n"
            "`!blocklist` - показать список заблокированных участников\n"
            "`!set_rcon1 <ip> <port> <password>` - установить данные RCON для сервера 1\n"
            "`!set_rcon2 <ip> <port> <password>` - установить данные RCON для сервера 2\n"
            "`!set_rcon3 <ip> <port> <password>` - установить данные RCON для сервера 3\n"
            "`!ip1 <ip> <port>` - установить IP и порт для сервера 1\n"
            "`!ip2 <ip> <port>` - установить IP и порт для сервера 2\n"
            "`!ip3 <ip> <port>` - установить IP и порт для сервера 3\n"
        )
        await ctx.author.send(admin_help_message)
        await ctx.send("Доступные команды для администраторов отправлены в личные сообщения.")
    else:
        user_help_message = (
            "**Доступные команды:**\n\n"
            "`!cmd <ваша_команда>` - отправить команду на сервер Minecraft\n"
            "`!status <участник>` - проверить статус участника\n"
            "`!listadmin` - список администраторов ркон бота"
        )
        await ctx.send(user_help_message)

@bot.command(name='listadmin')
async def list_admins(ctx):
    admin_list = '\n'.join([f'<@{admin_id}>' for admin_id in ADMIN_IDS])

    embed = discord.Embed(title='Список администраторов', description=admin_list, color=0x7531FF)
    await ctx.send(embed=embed)

@bot.command(name='upg', usage='!upg <версия> <новость>')
async def update_rcon_news(ctx, version=None, *, news=None):
    """
    Добавляет новость об обновлении RCON.

    Параметры:
    - версия: номер версии обновления
    - новость: краткое описание новости
    """
    # Эмодзи для красивого оформления
    emoji_success = "✅"
    emoji_warning = "⚠️"
    emoji_error = "❌"

    if ctx.author.id == DEVELOPER_ID:
        news_channel_id = RCON_NEWS  # Замените на ваш ID канала для новостей RCON
        news_channel = ctx.guild.get_channel(news_channel_id)

        if not news_channel:
            await ctx.send(f"{emoji_error} Не удалось найти канал для новостей RCON.")
            return

        if version is None or news is None:
            # Если аргументы не указаны, отправляем сообщение об использовании
            await ctx.send(
                f"{emoji_warning} **Использование команды !upg**\n"
                f"Вы должны указать версию и новость обновления.\n\n"
                f"Пример:\n"
                f"`!upg 1.0 Новые возможности RCON!`"
            )
            return

        try:
            # Преобразование . в тире и форматирование
            formatted_news = '- ' + news.replace('.', '\n- ').strip()

            await news_channel.send(
                f'🚀 **Обновление RCON {version}!** 🚀\n\n'
                f'📰 **Новости:**\n\n'
                f'{formatted_news}\n\n'
                f'**Следите за обновлениями!**'
            )
            await ctx.send(f"{emoji_success} Новость успешно добавлена!")
        except Exception as e:
            await ctx.send(f"{emoji_error} Произошла ошибка при добавлении новости: {str(e)}")
    else:
        await ctx.send(f"{emoji_error} У вас нет разрешения на использование этой команды. Команда доступна только для разработчика.")

bot.run('MTE5ODk0MjQ0NTk1MDQ3MjIyMg.GCQpSI.Gip1K1p0h7hrvX9XeBHxuY56yirVDdho8LpfWU')