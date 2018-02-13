"""Warning cog"""

# Credits go to FwiedRice, The Tasty Jaffa#3975, helo i am sit guy#9501 and the many people on the Red Server and Discord API

import discord
import os
import shutil
import aiohttp
import asyncio
from discord.ext import commands
from .utils import checks
from .utils.chat_formatting import pagify, box
import logging
import time
import re
import zlib, marshal, base64
import uuid
from .utils.chat_formatting import *
from .utils.dataIO import fileIO, dataIO
from .utils import checks
from discord.ext import commands
from enum import Enum
from __main__ import send_cmd_help

default_warn = ("user.mention, you have received your "
                "warning #warn.count! At warn.limit warnings you "
                "will be banned!")
default_max = 3
default_ban = ("After warn.limit warnings, user.name has been banned.")
default_channel = "warning_review"
default_muterole = 'Muted'
defrevoke = "This is to let you know that a warning has been removed."
try:
    from tabulate import tabulate
except Exception as e:
    raise RuntimeError("You must run `pip3 install tabulate`.") from e

log = logging.getLogger('red.punish')

UNIT_TABLE = {'s': 1, 'm': 60, 'h': 60 * 60, 'd': 60 * 60 * 24}
UNIT_SUF_TABLE = {'sec': (1, ''),
                  'min': (60, ''),
                  'hr': (60 * 60, 's'),
                  'day': (60 * 60 * 24, 's')
                  }
defmutetime = '10m'
PURGE_MESSAGES = 1  # for cpunish
PATH = 'data/account/'
JSON = PATH + 'mutedtime.json'
JSONLIST = PATH + 'warninglist.json'



class BadTimeExpr(Exception):
    pass


def _parse_time(time):
    if any(u in time for u in UNIT_TABLE.keys()):
        delim = '([0-9.]*[{}])'.format(''.join(UNIT_TABLE.keys()))
        time = re.split(delim, time)
        time = sum([_timespec_sec(t) for t in time if t != ''])
    elif not time.isdigit():
        raise BadTimeExpr("invalid expression '%s'" % time)
    return int(time)


def _timespec_sec(t):
    timespec = t[-1]
    if timespec.lower() not in UNIT_TABLE:
        raise BadTimeExpr("unknown unit '%c'" % timespec)
    timeint = float(t[:-1])
    return timeint * UNIT_TABLE[timespec]


def _generate_timespec(sec):
    timespec = []

    def sort_key(kt):
        k, t = kt
        return t[0]
    for unit, kt in sorted(UNIT_SUF_TABLE.items(), key=sort_key, reverse=True):
        secs, suf = kt
        q = sec // secs
        if q:
            if q <= 1:
                suf = ''
            timespec.append('%02.d%s%s' % (q, unit, suf))
        sec = sec % secs
    return ', '.join(timespec)
        

class Warn:
    "Put misbehaving users in timeout"
    def __init__(self, bot):
        self.bot = bot
        self.json = compat_load(JSON)
        self.handles = {}
        bot.loop.create_task(self.on_load())
        self.profile = "data/account/warnings.json"
        self.riceCog = dataIO.load_json(self.profile)
        self.warning_settings = "data/account/warning_settings.json"
        self.riceCog2 = dataIO.load_json(self.warning_settings)
        self.warninglist = "data/account/nobnl.json"
        self.norole = dataIO.load_json(self.warninglist)
        self.modrole = "data/red/settings.json"
        self.modrole2 = dataIO.load_json(self.modrole)
        self.warnlist = "data/account/warninglist.json"
        self.warnlist2 = dataIO.load_json(self.warnlist)
        for x in self.bot.servers:
            try:
                self.norole[x.id]
            except:

                self.norole[x.id]={
                    }

    def save(self):
        dataIO.save_json(JSON, self.json)

    def data_check(self, ctx=None, user=None, server=None):
        if ctx:
            sid = ctx.message.server.id
            uid = ctx.message.author.id
        else:
            sid = server.id
            uid = user.id
        if sid not in self.riceCog:
            self.riceCog[sid] = {}
        if uid not in self.riceCog[sid]:
            self.riceCog[sid][uid] = {"Count": 0}


    @commands.group(no_pm=True, pass_context=True, name='warnset')
    async def _warnset(self, ctx):
        self.data_check(ctx)
        if ctx.message.server.id not in self.riceCog2:
            self.riceCog2[ctx.message.server.id] = {}
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            server = ctx.message.server
            try:
                msg = self.riceCog2[server.id]["warn_message"]
            except:
                msg = default_warn
            try:
                ban = self.riceCog2[server.id]["ban_message"]
            except:
                ban = default_ban
            try:
                _max = self.riceCog2[server.id]["max"]
            except:
                _max = default_max
            try:
                defchannel = self.riceCog2[server.id]["defchannel"]
            except:
                defchannel = default_channel        
            try:
                mutetime = self.riceCog2[server.id]["mutetime"]
            except:
                mutetime = defmutetime    
            try:
                muterole = self.riceCog2[server.id]["muterole"]
            except:
                muterole = default_muterole 
            try:
                revokemsg = self.riceCog2[server.id]["revokemsg"]
            except:
                revokemsg = defrevoke                
            message = "```\n"
            message += "Warn Message - {}\n"
            message += "Ban Message - {}\n"
            message += "Warn Limit - {}\n"
            message += "Log Channel - {}\n"
            message += "Mute Time - {}\n" 
            message += "Mute Role - {}\n"   
            message += "Revoke Message - {}\n"               
            message += "```"
            await self.bot.say(message.format(msg,
                                              ban,
                                              _max, defchannel, mutetime, muterole, revokemsg))
                                              
    @_warnset.command(no_pm=True, pass_context=True, manage_server=True)
    async def muterole(self, ctx, rolename: str):
        """Change the default mute time for the first warning"""
        self.data_check(ctx)
        server = ctx.message.server
        
        self.riceCog2[server.id]["muterole"] = rolename
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say("Muted role name is now: **{}**".format(rolename))

           
    @_warnset.command(no_pm=True, pass_context=True, manage_server=True)
    async def mutetime(self, ctx):
        """Change the default mute time for the first warning"""
        self.data_check(ctx)
        server = ctx.message.server
        
        await self.bot.say("Please make sure to set the time with the correct time prefix at the end. (*For minutes 'm', for hours 'h'*)\n\nPlease type your timeframe now.")
        muteroletime = await self.bot.wait_for_message(channel = ctx.message.channel, author = ctx.message.author)

        if "m" in muteroletime.content or "s" in muteroletime.content or "h" in muteroletime.content:
            self.riceCog2[server.id]["mutetime"] = muteroletime.content
            dataIO.save_json(self.warning_settings,
                             self.riceCog2)
            await self.bot.say("Default mute time is now: **{}**".format(muteroletime.content))
        else:
            await self.bot.say("You've done something wrong! Please make sure that the format is correct!")
            return
           

    @_warnset.command(no_pm=True, pass_context=True, manage_server=True)
    async def defchannel(self, ctx, channel: str):
        """Change the default logging channel"""
        self.data_check(ctx)
        server = ctx.message.server

        self.riceCog2[server.id]["defchannel"] = channel
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say("Log channel is now: **{}**".format(channel))
            
    @_warnset.command(no_pm=True, pass_context=True, manage_server=True)
    async def pm(self, ctx):
        """Enable/disable PM warn"""
        server = ctx.message.server
        self.data_check(ctx)
        if 'pm_warn' not in self.riceCog[server.id]:
            self.riceCog[server.id]['pm_warn'] = False

        p = self.riceCog[server.id]['pm_warn']
        if p:
            self.riceCog[server.id]['pm_warn'] = False
            await self.bot.say("Warnings are now in the channel.")
        elif not p:
            self.riceCog[server.id]['pm_warn'] = True
            await self.bot.say("Warnings are now in DM.")

    @_warnset.command(no_pm=True, pass_context=True, manage_server=True)
    async def poop(self, ctx):
        """Enable/disable poop emojis per warning."""
        self.data_check(ctx)
        server = ctx.message.server
        true_msg = "Poop emojis per warning enabled."
        false_msg = "Poop emojis per warning disabled."
        if 'poop' not in self.riceCog2[server.id]:
            self.riceCog2[server.id]['poop'] = True
            msg = true_msg
        elif self.riceCog2[server.id]['poop'] == True:
            self.riceCog2[server.id]['poop'] = False
            msg = false_msg
        elif self.riceCog2[server.id]['poop'] == False:
            self.riceCog2[server.id]['poop'] = True
            msg = true_msg
        else:
            msg = "Error."
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say(msg)

    @_warnset.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True, manage_server=True)
    async def max(self, ctx, limit: int):
        """Sets the max amount of warnings before banning."""
        self.data_check(ctx)
        server = ctx.message.server

        self.riceCog2[server.id]["max"] = limit
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say("Warn limit is now: \n{}".format(limit))

    @_warnset.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True, manage_server=True)
    async def revokemsg(self, ctx, *, msg=None):
        self.data_check(ctx)
        """Set the message on warning being revoked.

        To get a full list of information, use **warnset message** without any parameters."""
        if not msg:
            await self.bot.say("```Set the message on warning being removed.\n\n"
                               "To get a full list of information, use "
                               "**warnset message** without any parameters.```")
            return
        server = ctx.message.server

        self.riceCog2[server.id]["revokemsg"] = msg
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say("Revoke message is now: \n{}".format(msg))
        
    @_warnset.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True, manage_server=True)
    async def ban(self, ctx, *, msg=None):
        self.data_check(ctx)
        """Set the ban message.

        To get a full list of information, use **warnset message** without any parameters."""
        if not msg:
            await self.bot.say("```Set the ban message.\n\n"
                               "To get a full list of information, use "
                               "**warnset message** without any parameters.```")
            return
        server = ctx.message.server

        self.riceCog2[server.id]["ban_message"] = msg
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say("Ban message is now: \n{}".format(msg))

    @_warnset.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True, manage_server=True)
    async def reset(self, ctx):
        """Resets all the warnings settings for this server"""
        self.data_check(ctx)
        server = ctx.message.server
        author = ctx.message.author
        channel = ctx.message.channel
        await self.bot.say("Are you sure you want to reset all warn settings"
                           "for this server?\n"
                           "Type **yes** within the next 15 seconds.")
        msg = await self.bot.wait_for_message(author=author,
                                              channel=channel,
                                              timeout=15.0)
        if msg.content.lower().strip() == "yes":
            self.riceCog2[server.id]["warn_message"] = default_warn
            self.riceCog2[server.id]["ban_message"] = default_ban
            self.riceCog2[server.id]["max"] = default_max
            self.riceCog2[server.id]["defchannel"] = default_channel
            self.riceCog2[server.id]["mutetime"] = defmutetime
        else:
            await self.bot.say("Nevermind then.")
            return

    @_warnset.command(no_pm=True, pass_context=True)
    @checks.admin_or_permissions(ban_members=True, manage_server=True)
    async def message(self, ctx, *, msg=None):
        self.data_check(ctx)
        """Set the warning message

        user.mention - mentions the user
        user.name   - names the user
        user.id     - gets id of user
        warn.count  - gets the # of this warn
        warn.limit  - # of warns allowed

        Example:

        **You, user.mention, have received Warning warn.count. After warn.limit,
        you will be banned.**

        You can set it either for every server.
        To set the ban message, use *warnset ban*
        """
        if not msg:
            await self.bot.say("```Set the warning message\n\n"
                               "user.mention - mentions the user\n"
                               "user.name   - names the user\n"
                               "user.id     - gets id of user\n"
                               "warn.count  - gets the # of this warn\n"
                               "warn.limit  - # of warns allowed\n\n"

                               "Example:\n\n"

                               "**You, user.mention, have received Warning "
                               "warn.count. After warn.limit, you will be "
                               "banned.**\n\n"

                               "You can set it either for every server.\n"
                               "To set the ban message, use *warnset ban*\n```")
            return

        server = ctx.message.server

        self.riceCog2[server.id]["warn_message"] = msg
        dataIO.save_json(self.warning_settings,
                         self.riceCog2)
        await self.bot.say("Warn message is now: \n{}".format(msg))

    async def filter_message(self, msg, user, count, _max):
        msg = msg.replace("user.mention",
                          user.mention)
        msg = msg.replace("user.name",
                          user.name)
        msg = msg.replace("user.id",
                          user.id)
        msg = msg.replace("warn.count",
                          str(count))
        msg = msg.replace("warn.limit",
                          str(_max))
        return msg

    @commands.command(no_pm=True, pass_context=True)
    @checks.mod()
    async def warn(self, ctx, user: discord.Member, *, reason: str=None):
        """Warns the user - At 3 warnings the user gets banned"""
        self.data_check(ctx)
        server = ctx.message.server
        author = ctx.message.author
        channel = ctx.message.channel

        can_ban = channel.permissions_for(server.me).ban_members
        can_role = channel.permissions_for(server.me).manage_roles

        if reason is None:
            msg = await self.bot.say("Please enter a reason for the warning!")
            await asyncio.sleep(5)
            await self.bot.delete_message(msg)
            await self.bot.delete_message(ctx.message)
            return

        if can_ban:
            pass
            await self.bot.delete_message(ctx.message)
        else:
            await self.bot.say("Sorry, I can't warn this user.\n"
                               "I am missing the `ban_members` permission")
            return

        if server.id not in self.riceCog2:
            msg = default_warn
            ban = default_ban
            _max = default_max
            defchannel = default_channel

        if server.id not in self.riceCog:
            self.riceCog[server.id] = {}
            
        if server.id not in self.warnlist2:
            self.warnlist2[server.id] = {}           

        if 'pm_warn' not in self.riceCog[server.id]:
            self.riceCog[server.id]['pm_warn'] = False

        p = self.riceCog[server.id]['pm_warn']

        try:
            msg = self.riceCog2[server.id]["warn_message"]
        except:
            msg = default_warn
        try:
            mutetime = self.riceCog2[server.id]["mutetime"]
        except:
            mutetime = defmutetime
        try:
            ban = self.riceCog2[server.id]["ban_message"]
        except:
            ban = default_ban
        try:
            _max = self.riceCog2[server.id]["max"]
        except:
            _max = default_max
        try:
            defchannel = self.riceCog2[server.id]["defchannel"]
        except:
            defchannel = default_channel
        colour = 0x9e0101

        # checks if the user is in the file
        if server.id not in self.riceCog2:
            self.riceCog2[server.id] = {}
            dataIO.save_json(self.warning_settings,
                             self.riceCog2)
        if server.id not in self.riceCog:
            self.riceCog[server.id] = {}
            dataIO.save_json(self.profile,
                             self.riceCog)
            if user.id not in self.riceCog[server.id]:
                self.riceCog[server.id][user.id] = {}
                dataIO.save_json(self.profile,
                                 self.riceCog)
            else:
                pass
        else:
            if user.id not in self.riceCog[server.id]:
                self.riceCog[server.id][user.id] = {}
                dataIO.save_json(self.profile,
                                 self.riceCog)
            else:
                pass

        if "Count" in self.riceCog[server.id][user.id]:
            count = self.riceCog[server.id][user.id]["Count"]
        else:
            count = 0   
        try:
            defchannel = self.riceCog2[server.id]["defchannel"]
        except:
            defchannel = default_channel
        channel = discord.utils.get(server.channels, name = defchannel)
        if channel is None:
            msg = await self.bot.say ("I was unable to write to your log channel. Please make sure there is a channel called {} on the server!".format(defchannel))
            return
        else:
            pass
           

        # checks how many warnings the user has
        if count == 0:
            count += 1
            msg = await self.filter_message(msg=msg,
                                            user=user,
                                            count=count,
                                            _max=_max)
            data = discord.Embed(colour=colour)
            data.add_field(name="Warning:",
                           value=msg)
            if reason:
                data.add_field(name="Reason:",
                               value=reason,
                               inline=False)
            data.add_field(name="​​Additional Actions:", value="*In addition to this you have been muted for {} as a result of your actions.*".format(mutetime), inline=False)
            data.set_footer(text=server.name)
            if p:
                #if dm is on
                await self.bot.send_message(user, embed=data)   
            elif not p:
                #if dm is not on
                await self.bot.say(embed=data)
                
            #run and log
            await self._punish_cmd_common(ctx, user, reason=reason, duration=mutetime)
            mod=author
            user=user
            reason=reason
            countnum = "{}/3".format(count)
            ID = uuid.uuid4()
            jsonid = "{}".format(ID)
            embed=discord.Embed(title="User Warned:", color=colour)
            embed.add_field(name="Case ID:", value=ID, inline=False)
            embed.add_field(name="Moderator:", value=mod, inline=False)
            embed.add_field(name="User:", value="{0} ({0.id})".format(user), inline=False)
            embed.add_field(name="Reason:", value=reason, inline=False)
            embed.add_field(name="Warning Number:", value=countnum, inline=False)
            react = await self.bot.send_message(channel, embed=embed)
            await self.bot.add_reaction(react, "\U0001f44d")
            await self.bot.add_reaction(react, "\U0001f44e")
            await self.bot.add_reaction(react, "\U0001f937")

            self.riceCog[server.id][user.id].update({"Count": count})
            dataIO.save_json(self.profile,
                             self.riceCog)
            
            self.warnlist2[server.id][jsonid] = {
                                        'User': user.id,
                                        'Mod': mod.id,
                                        'Reason': reason,
                                        'Warning Number': countnum
                                    }
            dataIO.save_json(self.warnlist,
                 self.warnlist2)   
            
        elif count > 0 and count < _max -1:
            count += 1
            msg = await self.filter_message(msg=msg,
                                            user=user,
                                            count=count,
                                            _max=_max)
            data = discord.Embed(colour=colour)
            data.add_field(name="Warning:",
                           value=msg)
            if reason:
                data.add_field(name="Reason:",
                               value=reason,
                               inline=False)
            data.set_footer(text=server.name)
            if p:
                #if pm on
                await self.bot.send_message(user, embed=data)
            elif not p:
                #if pm off
                await self.bot.say(embed=data)
                
            #run and log
            mod=author
            user=user
            reason=reason
            ID = uuid.uuid4()
            jsonid = "{}".format(ID)
            countnum = "{}/3".format(count)
            embed=discord.Embed(title="User Warned:", color=colour)
            embed.add_field(name="Case ID:", value=ID, inline=False)
            embed.add_field(name="Moderator:", value=mod, inline=False)
            embed.add_field(name="User:", value="{0} ({0.id})".format(user), inline=False)
            embed.add_field(name="Reason:", value=reason, inline=False)
            embed.add_field(name="Warning Number:", value=countnum, inline=False)
            react = await self.bot.send_message(channel, embed=embed)
            await self.bot.add_reaction(react, "\U0001f44d")
            await self.bot.add_reaction(react, "\U0001f44e")
            await self.bot.add_reaction(react, "\U0001f937")
            self.riceCog[server.id][user.id].update({"Count": count})
            dataIO.save_json(self.profile,
                             self.riceCog)
            self.warnlist2[server.id][jsonid]= {
                                        'User': user.id,
                                        'Mod': mod.id,
                                        'Reason': reason,
                                        'Warning Number': countnum
                                    }
            dataIO.save_json(self.warnlist,
                 self.warnlist2) 

        else:
            msg = ban
            msg = await self.filter_message(msg=msg,
                                            user=user,
                                            count=count,
                                            _max=_max)
            data = discord.Embed(colour=colour)
            data.add_field(name="Warning",
                           value=msg)
            if reason:
                data.add_field(name="Reason",
                               value=reason,
                               inline=False)
            data.set_footer(text=server.name)
            if p:
                await self.bot.send_message(user, embed=data)
            elif not p:
                await self.bot.say(embed=data)
                
            #run and log
            mod=author
            user=user
            reason=reason
            ID = uuid.uuid4()
            jsonid = "{}".format(ID)
            bantext = "Max Warnings reached."
            embed=discord.Embed(title="User Banned:", color=colour)
            embed.add_field(name="Case ID:", value=ID, inline=False)
            embed.add_field(name="Moderator:", value=mod, inline=False)
            embed.add_field(name="User:", value="{0} ({0.id})".format(user), inline=False)
            embed.add_field(name="Reason:", value=reason, inline=False)
            embed.add_field(name="Additional Actions:", value="*As the user has reached 3 warnings they have been banned from the server.*", inline=False)
            react = await self.bot.send_message(channel, embed=embed)
            await self.bot.add_reaction(react, "\U0001f44d")
            await self.bot.add_reaction(react, "\U0001f44e")
            await self.bot.add_reaction(react, "\U0001f937")
            count = 0
            self.riceCog[server.id][user.id].update({"Count": count})
            dataIO.save_json(self.profile,
                             self.riceCog)
            self.warnlist2[server.id][jsonid] = {
                                        'User': user.id,
                                        'Mod': mod.id,
                                        'Reason': reason,
                                        'Warning Number': bantext
                                        }
            dataIO.save_json(self.warnlist,
                 self.warnlist2)                        
            try:
                await self.bot.ban(user, delete_message_days=0)
            except discord.errors.Forbidden:
                await self.bot.say("I don't have permissions to ban that user.")

        if 'poop' in self.riceCog2[server.id] and can_role:
            if self.riceCog2[server.id]['poop'] == True:
                poops = count * "\U0001f528"
                role_name = "Warning {}".format(poops)
                is_there = False
                colour = 0xbc7642
                for role in server.roles:
                    if role.name == role_name:
                        poop_role = role
                        is_there = True
                if not is_there:
                    poop_role = await self.bot.create_role(server)
                    await self.bot.edit_role(role=poop_role,
                                             name=role_name,
                                             server=server)
                try:
                    await self.bot.add_roles(user,
                                             poop_role)
                except discord.errors.Forbidden:
                    await self.bot.say("No permission to add roles")
                    
    @commands.command(no_pm=True, pass_context=True)
    @checks.mod()
    async def warnings(self, ctx):
        """Lists all the warnings on the server"""
        server = ctx.message.server
        server_id = server.id
        if not (server_id in self.warnlist2 and self.warnlist2[server_id]):
            await self.bot.say("No users are currently punished.")
            return

        def getmname(mid):
            member = discord.utils.get(server.members, id=mid)
            if member:
                if member.nick:
                    return '%s (%s)' % (member.nick, member)
                else:
                    return str(member)
            else:
                return '(member not present, id #%d)'

        headers = ['Member', 'Warning Number', 'Moderator', 'Reason']
        table = []
        disp_table = []
        now = time.time()
        for member_id, data in self.warnlist2[server_id].items():

            #if not member_id.isdigit():
                #continue
            print ("704")
            member_name = getmname(data['User'])
            warnnum = data['Warning Number']
            punisher_name = getmname(data['Mod'])
            reason = data['Reason']
            table.append((member_name, warnnum, punisher_name, reason))

        #for _, name, warnum, mod, reason in sorted(table, key=lambda x: x[0]):
            disp_table.append((member_name, warnnum, punisher_name, reason))

        for page in pagify(tabulate(disp_table, headers)):
            await self.bot.say(box(page))
    @commands.command(no_pm=True, pass_context=True)
    @checks.mod()
    async def remove(self, ctx, user: discord.Member):
        self.data_check(ctx)
        author = ctx.message.author
        server = author.server
        channel = ctx.message.channel
        can_role = channel.permissions_for(server.me).manage_roles
        count = self.riceCog[server.id][user.id]["Count"]
        try:
            revokemsg = self.riceCog2[server.id]["revokemsg"]
        except:
            revokemsg = defrevoke

        if server.id not in self.riceCog:
            self.riceCog[server.id] = {}
            dataIO.save_json(self.profile,
                             self.riceCog)
            if user.id not in self.riceCog[server.id]:
                self.riceCog[server.id][user.id] = {}
                dataIO.save_json(self.profile,
                                 self.riceCog)
            else:
                pass
        else:
            if user.id not in self.riceCog[server.id]:
                self.riceCog[server.id][user.id] = {}
                dataIO.save_json(self.profile,
                                 self.riceCog)
            else:
                pass
                


        if "Count" in self.riceCog[server.id][user.id]:
            count = self.riceCog[server.id][user.id]["Count"]
        else:
            count = 0

        if count != 0:
            msg = await self.bot.say("A warning for {} has been removed!".format(user))
            await self.bot.send_message(user, revokemsg)
            count -= 1
            self.riceCog[server.id][user.id].update({"Count": count})
            dataIO.save_json(self.profile,
                             self.riceCog)
            if 'poop' in self.riceCog2[server.id] and can_role:
                if self.riceCog2[server.id]['poop'] == True:
                    try:
                        role = role = list(filter(lambda r: r.name.startswith('Warning \U0001f528'), server.roles))
                        await self.bot.remove_roles(user, *role)
                    except discord.errors.Forbidden:
                        await self.bot.say("No permission to add roles")
                    if count >=1:
                        poops = count * "\U0001f528"
                        role_name = "Warning {}".format(poops)
                        is_there = False
                        colour = 0xbc7642
                        for role in server.roles:
                            if role.name == role_name:
                                poop_role = role
                                is_there = True
                        if not is_there:
                            poop_role = await self.bot.create_role(server)
                            await self.bot.edit_role(role=poop_role,
                                                     name=role_name,
                                                     server=server)
                        try:
                            await self.bot.add_roles(user,
                                                     poop_role)
                        except discord.errors.Forbidden:
                            await self.bot.say("No permission to add roles")                             
            await asyncio.sleep(15)
            await self.bot.delete_message(msg)
            await self.bot.delete_message(ctx.message)
        else:
            msg = await self.bot.say("You don't have any warnings to clear, "
                               + str(user.mention) + "!")
            await asyncio.sleep(15)
            await self.bot.delete_message(msg)
            await self.bot.delete_message(ctx.message)       

    @commands.command(no_pm=True, pass_context=True)
    @checks.mod()
    async def clean(self, ctx, user: discord.Member):
        """Removes all punishments from a user"""
        self.data_check(ctx)
        author = ctx.message.author
        server = author.server
        colour = server.me.colour
        channel = ctx.message.channel
        can_role = channel.permissions_for(server.me).manage_roles
        count = self.riceCog[server.id][user.id]["Count"]
        muterole = await self.get_role(user.server)

        if server.id not in self.riceCog:
            self.riceCog[server.id] = {}
            dataIO.save_json(self.profile,
                             self.riceCog)
            if user.id not in self.riceCog[server.id]:
                self.riceCog[server.id][user.id] = {}
                dataIO.save_json(self.profile,
                                 self.riceCog)
            else:
                pass
        else:
            if user.id not in self.riceCog[server.id]:
                self.riceCog[server.id][user.id] = {}
                dataIO.save_json(self.profile,
                                 self.riceCog)
            else:
                pass
        await self.bot.delete_message(ctx.message)
        if "Count" in self.riceCog[server.id][user.id]:
            count = self.riceCog[server.id][user.id]["Count"]
        else:
            count = 0
        await self.bot.say("**The following punishments for {} have been removed:**".format(user))
        if count != 0:
            count = 0
            self.riceCog[server.id][user.id].update({"Count": count})
            dataIO.save_json(self.profile,
                             self.riceCog)

            self.bot.remove_roles(user, muterole)
            msg = await self.bot.say("Mute Role")
            if 'poop' in self.riceCog2[server.id] and can_role:
                if self.riceCog2[server.id]['poop'] == True:
                    try:
                        role = role = list(filter(lambda r: r.name.startswith('Warning \U0001f528'), server.roles))
                        await self.bot.remove_roles(user, *role)
                        msg = await self.bot.say("Warning Roles")
                    except discord.errors.Forbidden:
                        await self.bot.say("No permission to add roles")  

        if user.id in self.norole[server.id] and 'Role' == True:
            self.norole[server.id][user.id] = {'Role': False}
            dataIO.save_json(self.warninglist, self.norole)
            nobnl = discord.utils.get(server.roles, name = "NoBNL")
            await self.bot.remove_roles(user,nobnl)
            msg = await self.bot.say("NoBNL Role")

        else:
            msg = await self.bot.say("No more punishments to remove!")
    @commands.command(no_pm=True, pass_context=True)
    @checks.mod()
    async def deny(self, ctx, user: discord.Member, *, reason: str=None):
        """Denies a user from the #bnl_discussion channel"""
        self.data_check(ctx)
        server = ctx.message.server
        try:
            defchannel = self.riceCog2[server.id]["defchannel"]
        except:
            defchannel = default_channel
        channel = discord.utils.get(server.channels, name = defchannel)
        if channel is None:
            msg = await self.bot.say ("I was unable to write to your log channel. Please make sure there is a channel called {} on the server!".format(defchannel))
            return
        else:
            pass
        if reason is None:
            msg = await self.bot.say("Please enter a reason for the warning!")
            await asyncio.sleep(5)
            await self.bot.delete_message(msg)
            return
        if user.id in self.norole[server.id]:
            if self.norole[server.id][user.id]['Role'] == True:
                msg = await self.bot.say("This user has already been denied access to the #bnl_discussion channel.")
                await asyncio.sleep(8)
                await self.bot.delete_message(msg)          
                await self.bot.delete_message(ctx.message)
                return
            else:
                nobnl = discord.utils.get(server.roles, name = "NoBNL")
                mod = ctx.message.author
                await self.bot.delete_message(ctx.message)
                await self.bot.add_roles(user, nobnl)
                dmuser = await self.bot.start_private_message(user)
                await self.bot.send_message(dmuser, "Howdy!\nThis is to let you know that you have been denied access to the #bnl_discussion channel for the reason:\n\n```{}``` \nPlease speak to a member of staff if you have an issue.".format(reason))
                user=user
                reason=reason
                ID = uuid.uuid4()
                embed=discord.Embed(title="User Denied:", color=0xA00000)
                embed.add_field(name="Case ID:", value=ID, inline=False)
                embed.add_field(name="Moderator:", value=mod, inline=False)
                embed.add_field(name="User:", value="{0} ({0.id})".format(user), inline=False)
                embed.add_field(name="Reason:", value=reason, inline=False)
                react = await self.bot.send_message(channel, embed=embed)
                await self.bot.add_reaction(react, "\U0001f44d")
                await self.bot.add_reaction(react, "\U0001f44e")
                await self.bot.add_reaction(react, "\U0001f937")
                self.norole[server.id][user.id] = {
                    'Reason': reason,
                    'Mod': ctx.message.author.id,
                    'Role': True
                }
                dataIO.save_json(self.warninglist, self.norole)
    @commands.command(no_pm=True, pass_context=True)
    @checks.mod()
    async def approve(self, ctx, user: discord.Member):
        """Allows a user access to the #bnl_discussion channel"""
        server = ctx.message.server
        if user.id in self.norole[server.id]:
            if self.norole[server.id][user.id]['Role'] == True:
                self.norole[server.id][user.id] = {'Role': False}
                dataIO.save_json(self.warninglist, self.norole)
                nobnl = discord.utils.get(server.roles, name = "NoBNL")
                await self.bot.remove_roles(user,nobnl)
                msg = await self.bot.say ("Role removed!")
                await asyncio.sleep(8)
                await self.bot.delete_message(msg)  
                await self.bot.delete_message(ctx.message)
            else:
                msg = await self.bot.say("There is no role to remove!")
                await asyncio.sleep(8)
                await self.bot.delete_message(msg)
                await self.bot.delete_message(ctx.message)
                
# clear role
    async def get_role(self, server):
        try:
            muterole = self.riceCog2[server.id]["muterole"]
        except:
            muterole = default_muterole   
        default_name = muterole
        role_id = self.json.get(server.id, {}).get('ROLE_ID')

        if role_id:
            role = discord.utils.get(server.roles, id=role_id)
        else:
            role = discord.utils.get(server.roles, name=default_name)

        if role is None:
            perms = server.me.server_permissions
            if not perms.manage_roles and perms.manage_channels:
                await self.bot.say("The Manage Roles and Manage Channels permissions are required to use this command.")
                return None

            else:
                perms = discord.Permissions.none()
                role = await self.bot.create_role(server, name=default_name, permissions=perms)
                print ("860")
                await self.bot.move_role(server, role, server.me.top_role.position - 1)

                for channel in server.channels:
                    await self.setup_channel(channel, role)

        if role and role.id != role_id:
            if server.id not in self.json:
                self.json[server.id] = {}
            self.json[server.id]['ROLE_ID'] = role.id
            self.save()

        return role

    async def on_load(self):
        await self.bot.wait_until_ready()

        for serverid, members in self.json.copy().items():
            server = self.bot.get_server(serverid)
            me = server.me

            # Bot is no longer in the server
            if not server:
                del(self.json[serverid])
                continue

            role = await self.get_role(server)
            if not role:
                log.error("Needed to create punish role in %s, but couldn't."
                          % server.name)
                continue

            for member_id, data in members.copy().items():
                if not member_id.isdigit():
                    continue

                until = data['until']
                if until:
                    duration = until - time.time()

                member = server.get_member(member_id)
                if until and duration < 0:
                    if member:
                        reason = 'Punishment removal overdue, maybe bot was offline. '
                        if self.json[server.id][member_id]['reason']:
                            reason += self.json[server.id][member_id]['reason']
                        await self._unpunish(member, reason)
                    else:  # member disappeared
                        del(self.json[server.id][member.id])

                elif member and role not in member.roles:
                    if role >= me.top_role:
                        log.error("Needed to re-add punish role to %s in %s, "
                                  "but couldn't." % (member, server.name))
                        continue
                    await self.bot.add_roles(member, role)
                    if until:
                        self.schedule_unpunish(duration, member)

        self.save()

    async def _punish_cmd_common(self, ctx, member, reason, duration):
        server = ctx.message.server
        note = ''
        
        duration = _parse_time(duration)
        if duration < 1:
            await self.bot.say("Duration must be 1 second or longer.")
            return False

        role = await self.get_role(member.server)

        if role >= server.me.top_role:
            await self.bot.say('The %s role is too high for me to manage.' % role)
            return

        if server.id not in self.json:
            self.json[server.id] = {}

        if note:
            msg += ' ' + note

        if server.id not in self.json:
            self.json[server.id] = {}

        self.json[server.id][member.id] = {
            'until': (time.time() + duration),
            'by': ctx.message.author.id,
            'reason': reason
        }

        await self.bot.add_roles(member, role)
        self.save()

        # schedule callback for role removal
        if duration:
            self.schedule_unpunish(duration, member)

        return True

    def schedule_unpunish(self, delay, member, reason=None):
        """Schedules role removal, canceling and removing existing tasks if present"""
        sid = member.server.id

        if sid not in self.handles:
            self.handles[sid] = {}

        if member.id in self.handles[sid]:
            self.handles[sid][member.id].cancel()

        coro = self._unpunish(member, reason)

        handle = self.bot.loop.call_later(delay, self.bot.loop.create_task, coro)
        self.handles[sid][member.id] = handle

    async def _unpunish(self, member, reason=None):
        """Remove punish role, delete record and task handle"""
        role = await self.get_role(member.server)
        if role:
            # Has to be done first to prevent triggering on_member_update listener
            self._unpunish_data(member)
            await self.bot.remove_roles(member, role)

            msg = 'Your punishment in %s has ended.' % member.server.name
            if reason:
                msg += "\nReason was: %s" % reason
                
    def _unpunish_data(self, member):
        """Removes punish data entry and cancels any present callback"""
        sid = member.server.id
        if sid in self.json and member.id in self.json[sid]:
            del(self.json[member.server.id][member.id])
            self.save()

        if sid in self.handles and member.id in self.handles[sid]:
            self.handles[sid][member.id].cancel()
            del(self.handles[member.server.id][member.id])

    # Functions related to unpunishing
    async def on_member_update(self, before, after):
        """Remove scheduled unpunish when manually removed"""
        sid = before.server.id

        if not (sid in self.json and before.id in self.json[sid]):
            return
        role = await self.get_role(before.server)
        if role and role in before.roles and role not in after.roles:
                #msg += '\nReason was: ' + self.json[sid][before.id]

            #msg = 'Your punishment in %s was ended early by a moderator/admin.' % before.server.name
            #if self.json[sid][before.id]:
            #await self.bot.send_message(after, msg)
            self._unpunish_data(after)

    async def setup_channel(self, channel, role):
        perms = discord.PermissionOverwrite()
        role = await self.get_role(channel.server)
        
        if channel.type == discord.ChannelType.text:
            perms.send_messages = False
            perms.send_tts_messages = False
        elif channel.type == discord.ChannelType.voice:
            perms.speak = False

        await self.bot.edit_channel_permissions(channel, role, overwrite=perms)
        
    async def on_channel_create(self, channel):
        """Run when new channels are created and set up role permissions"""
        if channel.is_private:
            return

        role = await self.get_role(channel.server)
        if not role:
            return

        await self.setup_channel(channel, role)
       
        
    async def on_member_join(self, member):
        """Restore punishment if punished user leaves/rejoins"""
        sid = member.server.id
        role = await self.get_role(member.server)
        try:
            muterole = self.riceCog2[server.id]["muterole"]
        except:
            muterole = default_muterole  

        if 'poop' in self.riceCog2[sid]:
            if self.riceCog2[sid]['poop'] == True:
                if member.id in self.riceCog[sid]:
                    if count >= 1:
                        count = self.riceCog[sid][member.id]["Count"]
                        poops = "\U0001f528" * count
                        role_name = "Warning {}".format(poops)
                        is_there = False
                        colour = 0xbc7642
                        for role in member.server.roles:
                            if role.name == role_name:
                                poop_role = role
                                is_there = True
                        if not is_there:
                            server = member.server
                            poop_role = await self.bot.create_role(server)
                            await self.bot.edit_role(role=poop_role,
                                                     name=role_name,
                                                     server=server)
                            try:
                                await self.bot.add_roles(member,
                                                         poop_role)
                            except discord.errors.Forbidden:
                                await self.bot.say("No permission to add roles")
                else:
                    pass
        if member.id in self.norole[sid]:
            if self.norole[sid]['role'] == True:
                role = discord.utils.get(member.server.roles, name="NoBNL")
                await self.bot.add_roles(member, role)
            
        if not role or not (sid in self.json and member.id in self.json[sid]):
            return

        duration = self.json[sid][member.id]['until'] - time.time()
        if duration > 0:
            role = discord.utils.get(member.server.roles, name=muterole)
            await self.bot.add_roles(member, role)

            reason = 'Punishment re-added on rejoin. '
            if self.json[sid][member.id]['reason']:
                reason += self.json[sid][member.id]['reason']

            if member.id not in self.handles[sid]:
                self.schedule_unpunish(duration, member, reason)
        

    async def on_reaction_add (self, reaction, user):
        channel = reaction.message.channel
        server = reaction.message.server
        reactor = user
        msg = reaction.message
        embed = msg.embeds[0]
        k = {'user':user, 'server':reaction.message.server}
        self.data_check(**k)
        roleneed = self.modrole2[server.id]['ADMIN_ROLE']
        role_needed = discord.utils.get(server.roles, name = roleneed)
        if not role_needed in reactor.roles:
            return
        try:
            defchannel = self.riceCog2[server.id]["defchannel"]
        except:
            defchannel = default_channel
        try:
            revokemsg = self.riceCog2[server.id]["revokemsg"]
        except:
            revokemsg = defrevoke
        
        logchannel = discord.utils.get(server.channels, name = defchannel)
        if logchannel is None:
            print("I was unable to write to your log channel. Please make sure there is a channel called {} on the server!".format(defchannel))
            return
        else:
            pass
            
 
        if 'title' not in embed:
            return
        if "Denied" in embed['title']:
            if reaction.emoji == '\U0001f528' and reaction.message.channel == logchannel:
                if user.id in self.norole[server.id]:
                    if self.norole[server.id][user.id]['Role'] == True:
                        self.norole[server.id][user.id] = {'Role': False}
                        dataIO.save_json(self.warninglist, self.norole)
                        nobnl = discord.utils.get(server.roles, name = "NoBNL")
                        await self.bot.remove_roles(user,nobnl)
                        msg = reaction.message
                        newembed = discord.Embed(title="Role Revoked:", color=0xA00000, description =  "The NoBNL role for {} has been revoked.".format(user))
                        newmsg = " "
                        await self.bot.edit_message(msg, newmsg, embed=newembed)    
                        await self.bot.clear_reactions(msg)
        else:
            title = embed['title']
            user_field = [f for f in embed['fields'] if f['name'] == 'User:'][0]
            user_id = user_field['value'].split('(')[-1][:-1]
            user = discord.utils.get(msg.server.members, id=user_id)
            if reaction.emoji == '\U0001f528' and reaction.message.channel == logchannel:
#command
                can_role = channel.permissions_for(server.me).manage_roles
                count = self.riceCog[server.id][user.id]["Count"]

                if server.id not in self.riceCog:
                    self.riceCog[server.id] = {}
                    dataIO.save_json(self.profile,
                                     self.riceCog)
                    if user.id not in self.riceCog[server.id]:
                        self.riceCog[server.id][user.id] = {}
                        dataIO.save_json(self.profile,
                                         self.riceCog)
                    else:
                        pass
                else:
                    if user.id not in self.riceCog[server.id]:
                        self.riceCog[server.id][user.id] = {}
                        dataIO.save_json(self.profile,
                                         self.riceCog)
                    else:
                        pass

                            
                if "Count" in self.riceCog[server.id][user.id]:
                    count = self.riceCog[server.id][user.id]["Count"]
                else:
                    count = 0

                if count != 0:
                    await self.bot.send_message(user, revokemsg)
                    count -= 1
                    self.riceCog[server.id][user.id].update({"Count": count})
                    dataIO.save_json(self.profile,
                                     self.riceCog)
                    #warnid = msg.embeds[0]['fields'][0]['value']
                    #del(self.warnlist2[server.id][warnid])
                    #dataIO.save_json(self.warnlist2, self.warnlist)
                    if 'poop' in self.riceCog2[server.id] and can_role:
                        if self.riceCog2[server.id]['poop'] == True:
                            try:
                                role = role = list(filter(lambda r: r.name.startswith('Warning \U0001f528'), server.roles))
                                await self.bot.remove_roles(user, *role)
                            except discord.errors.Forbidden:
                                await self.bot.send_message(channel, "No permission to add roles")
                        if count >= 1:
                            poops = count * "\U0001f528"
                            role_name = "Warning {}".format(poops)
                            is_there = False
                            colour = 0xbc7642
                            for role in server.roles:
                                if role.name == role_name:
                                    poop_role = role
                                    is_there = True
                            if not is_there:
                                poop_role = await self.bot.create_role(server)
                                await self.bot.edit_role(role=poop_role,
                                                         name=role_name,
                                                         server=server)
                            try:
                                await self.bot.add_roles(user,
                                                         poop_role)
                            except discord.errors.Forbidden:
                                await self.bot.say("No permission to add roles")                
                    msg = reaction.message
                    newembed = discord.Embed(title="Warning Revoked:", color=0xA00000, description =  "The warning for {} has been revoked.".format(user))
                    newmsg = " "
                    await self.bot.edit_message(msg, newmsg, embed=newembed)    
                    await self.bot.clear_reactions(msg)
                else:
                    msg = await self.bot.send_message(channel, "There are no warnings to clear for the selected case.")
            if reaction.emoji == '\U0001f4ce' and reaction.message.channel == logchannel:
                dmchannel = await self.bot.start_private_message(reactor)
                await self.bot.send_message(dmchannel, "Please send an attachment")
                msg = await self.bot.wait_for_message(channel=dmchannel, author=reactor)
                if msg.attachments:
                    attachmentlist = msg.attachments[0]
                    attachment = attachmentlist['url']
                    attach = "**Attachments:**\n\n" + attachment + "\n\n"
                    attachnew = reaction.message.content + "\n\n" + attachment
                    if "Attachments:" in reaction.message.content:
                        await self.bot.send_message(dmchannel, "Thanks!")
                        await self.bot.edit_message(reaction.message, attachnew) 
                        await self.bot.remove_reaction(reaction.message, emoji = '\U0001f4ce', member = reactor)
                                
                        #await self.bot.send_message(dmchannel, "There is already an attachment!")
                    else:
                        await self.bot.send_message(dmchannel, "Thanks!")
                        await self.bot.edit_message(reaction.message, attach)
                        await self.bot.remove_reaction(reaction.message, emoji = '\U0001f4ce', member = reactor)
                    #await self.bot.send_message(channel, attachment)
                elif "discord" in msg.content:
                    attach = "**Attachments:**\n\n" + msg.content + "\n\n"
                    if "Attachments:" in reaction.message.content:
                        attachnew = reaction.message.content + "\n\n" + msg.content
                        await self.bot.send_message(dmchannel, "Thanks!")
                        await self.bot.edit_message(reaction.message, attachnew)
                        await self.bot.remove_reaction(reaction.message, emoji = '\U0001f4ce', member = reactor)
                    else:
                        attach = "**Attachments:**\n\n" + msg.content + "\n\n"
                        await self.bot.edit_message(reaction.message, attach)
                        await self.bot.send_message(dmchannel, "Thanks!")
                        await self.bot.remove_reaction(reaction.message, emoji = '\U0001f4ce', member = reactor)
                else:
                    await self.bot.send_message(dmchannel, "**Error:** Please make sure to attach an image!")
                    await self.bot.remove_reaction(reaction.message, emoji = '\U0001f4ce', member = reactor)
            if reaction.emoji == '\U0001f5a8' and reaction.message.channel == logchannel:
                printme = msg.embeds[0]['fields'][0]['value']
                print (printme)
            else:
                return

def compat_load(path):
    data = dataIO.load_json(path)
    for server, punishments in data.items():
        for user, pdata in punishments.items():
            if not user.isdigit():
                continue
            by = pdata.pop('givenby', None)
            by = by if by else pdata.pop('by', None)
            pdata['by'] = by
            pdata['until'] = pdata.pop('until', None)
            pdata['until'] = pdata.pop('until', None)
            pdata['reason'] = pdata.pop('reason', None)
    return data


def check_folder():
    if not os.path.exists("data/account"):
        print("Creating data/account/server.id folder")
        os.makedirs("data/account")
    if not os.path.exists(PATH):
        log.debug('Creating folder: data/account')
        os.makedirs(PATH)


def check_file():
    data = {}
    f = "data/account/warnings.json"
    g = "data/account/warning_settings.json"
    c = "data/account/nobnl.json"
    d = "data/account/warninglist.json"
    if not dataIO.is_valid_json(f):
        print("Creating data/account/warnings.json")
        dataIO.save_json(f,
                         data)
    if not dataIO.is_valid_json(g):
        print("Creating data/account/warning_settings.json")
        dataIO.save_json(g,
                         data)
    if not dataIO.is_valid_json(c):
        print("Creating data/account/nobnl.json")
        dataIO.save_json(c,
                         data)
    if not dataIO.is_valid_json(d):
        print("Creating data/account/warninglist.json")
        dataIO.save_json(d,
                         data)
    if not dataIO.is_valid_json(JSON):
        print('Creating empty %s' % JSON)
        dataIO.save_json(JSON, {})

def setup(bot):
    check_folder()
    check_file()
    n = Warn(bot)
    bot.add_cog(Warn(bot))
