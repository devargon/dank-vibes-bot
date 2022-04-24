import discord
from discord.ext import commands

from main import dvvt


class WatchList(commands.Cog):
    def __init__(self, client):
        self.client: dvvt = client

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        chan_notify_id = 616007729718231161 if member.guild.id == 595457764935991326 else 871737314831908974 if member.guild.id == 871734809154707467 else None
        chan = member.guild.get_channel(chan_notify_id)
        if chan is not None and chan.permissions_for(member.guild.get_member(self.client.user.id)).send_messages:
            channel_exists = True
        else:
            channel_exists = False
        if len(result := await self.client.db.fetch("SELECT user_id, remarks FROM watchlist WHERE guild_id = $1 AND target_id = $2", member.guild.id, member.id)) > 0:
            for row in result:
                remarks = row.get('remarks')
                remarks = "" if remarks is None else f"\n**Remarks:** {remarks}"
                msg = f"{member.mention} **{member}** ({member.id}) has joined **{member.guild.name}**. {remarks}"

                user_id = row['user_id']
                if (notifier := member.guild.get_member(user_id)) is not None:
                    notify_type = await self.client.db.fetchval("SELECT watchlist_notify FROM userconfig WHERE user_id = $1", user_id)
                    if notify_type is None or notify_type == 0:
                        continue
                    elif notify_type == 1: #DM

                        try:
                            await notifier.send(msg)
                        except Exception as e:
                            await chan.send(f"{notifier.mention} {msg}")
                        else:
                            continue
                    elif notify_type == 2: #Channel
                        await chan.send(f"{notifier.mention} {msg}")
        else:
            return

