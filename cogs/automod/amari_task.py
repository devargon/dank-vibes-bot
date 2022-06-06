import amari
import discord
from discord.ext import commands, tasks
from main import dvvt
from utils.format import print_exception
from utils.specialobjects import AwaitingAmariData, NoAmariData
import time

def get_current_time():
    return round(time.time())

sample_data = {
    123456789: {
        'leaderboard': amari.Leaderboard,
        'last_update': 1234567,
        'error': None
    }
}

class AmariTask(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @tasks.loop(seconds=20)
    async def amari_task(self):
        await self.client.wait_until_ready()
        for guild in self.client.guilds:
            data = self.client.amari_data.get(guild.id, None)
            if data is None:
                self.client.amari_data[guild.id] = {
                    'leaderboard': AwaitingAmariData,
                    'last_update': get_current_time(),
                    'error': None,
                }
            else:
                if data['leaderboard'] == NoAmariData:
                    if get_current_time() - data['last_update'] < 300:
                        continue
            try:
                leaderboard = await self.client.AmariClient.fetch_full_leaderboard(guild.id)
            except amari.exceptions.NotFound as e:
                self.client.amari_data[guild.id]['leaderboard'] = NoAmariData
                self.client.amari_data[guild.id]['last_update'] = get_current_time()
                continue
            except amari.exceptions.InvalidToken as e:
                self.client.amari_data[guild.id]['error'] = e
                print_exception("AMARI TOKEN IS INVALID", e)
                continue
            except amari.exceptions.RatelimitException as e:
                self.client.amari_data[guild.id]['error'] = e
                continue
            except amari.exceptions.AmariServerError as e:
                self.client.amari_data[guild.id]['error'] = e
                continue
            except amari.exceptions.HTTPException as e:
                if "Unable to find the requested guild" in str(e):
                    self.client.amari_data[guild.id]['leaderboard'] = NoAmariData
                    self.client.amari_data[guild.id]['last_update'] = get_current_time()
                else:
                    self.client.amari_data[guild.id]['error'] = e
                    self.client.amari_data[guild.id]['last_update'] = get_current_time()
                continue
            except Exception as e:
                print_exception(f"Ignoring exception in amari_task", e)
                self.client.amari_data[guild.id]['error'] = e
                self.client.amari_data[guild.id]['last_update'] = get_current_time()
                continue
            else:
                self.client.amari_data[guild.id]['leaderboard'] = leaderboard
                self.client.amari_data[guild.id]['last_update'] = get_current_time()
                self.client.amari_data[guild.id]['error'] = None
                continue

