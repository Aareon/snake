from discord.ext import commands
from .utils import sql
from .utils.tag_manager import parser as tag_parser

ALLOWED_ATTRIBUTES = [
    # Object
    "id",
    "created_at",
    "timestamp",
    # User
    "name",
    "discriminator",
    "avatar",
    "bot",
    "avatar_url",
    "default_avatar",
    "default_avatar_url",
    "mention",
    "display_name",
    # Message
    "edited_timestamp",
    "tts",
    "content",
    "mention_everyone",
    "mentions",
    "channel_mentions",
    "role_mentions",
    "pinned",
    "clean_content",
    # Reaction
    "custom_emoji",
    "count",
    "me",
    # Embed
    "title",
    "description",
    "url",
    "color",
    "colour",
    # Server
    "name",
    "afk_timeout",
    "region",
    "afk_channel",
    "icon",
    "owner",
    "unavailable",
    "large",
    "mfa_level",
    "splash",
    "default_channel",
    "icon_url",
    "splash_url",
    "member_count",
    # Member
    "joined_at",
    "status",
    "game",
    "nick",
    # Channel
    "topic",
    "is_private",
    "position",
    "bitrate",
    "user_limit",
    "is_default"
    # TODO: very important: add attributes per-type and global
]

class Tag:
    def __init__(self, tag):
        self.name = tag.name
        self.author_id = tag.author_id
        self.content = tag.content
        self.uses = tag.uses
        self.timestamp = tag.timestamp

    def __repr__(self):
        return f"<Tag(name='{self.name}', author_id={self.author_id}, uses={self.uses}, timestamp='{self.timestamp}')>"

class TagOverrides(tag_parser.TagFunctions):
    def __init__(self, bot, ctx, tag, **kwargs):
        super().__init__()

        self.bot = bot
        self.ctx = ctx
        self.tag = tag
        self.debug = kwargs.get("debug", False)
        self.data_cache = {}

        setattr(self, "if", self._TagOverrides__compare)

    def get(self, key, default='Does not exist'):
        with self.bot.db_scope() as session:
            tag_dict = session.query(sql.TagVariable).filter_by(tag_name=self.tag.name).first()

            if tag_dict is None:
                tag_dict = sql.TagVariable(tag_name=self.tag.name, data={})
                session.add(tag_dict)

            return tag_dict.data.get(key, default)

    def set(self, key, value):
        with self.bot.db_scope() as session:
            tag_dict = session.query(sql.TagVariable).filter_by(tag_name=self.tag.name).first()
            if tag_dict is None:
                tag_dict = sql.TagVariable(tag_name=self.tag.name, data={})
                session.add(tag_dict)

            tag_dict.data[key] = value
            self.bot.db.flag(tag_dict, "data") # force it to re-commit

    def fetch(self, key):
        return self.data_cache[key]

    def cache(self, key, value):
        self.data_cache[key] = value

    def attr(self, obj, key):
        if key not in ALLOWED_ATTRIBUTES:
            raise ValueError(f"Illegal attribute {key}")
        else:
            return getattr(obj, key)

    def author(self):
        return self.ctx.message.author

    def self(self):
        return self.tag

    def channel(self):
        return self.ctx.message.channel

    def server(self):
        return self.ctx.message.server

    def __compare(self, condition, result, else_=''):
        if condition:
            return result
        else:
            return else_

    def eq(self, first, second):
        return first == second or str(first).lower() == str(second).lower()

class Tags:
    def __init__(self, bot):
        self.bot = bot

    async def get_tag(self, tag_name):
        with self.bot.db_scope() as session:
            tag = session.query(sql.Tag).filter_by(name=tag_name).first()
            if tag is not None:
                tag.uses = tag.uses + 1
                return Tag(tag)
            else:
                return None

    @commands.group(name="tag", pass_context=True, brief="tag manager", invoke_without_command=True)
    async def tag_group(self, ctx):
        print("tags")

    @tag_group.command(name="test", pass_context=True, brief="run a test parse")
    async def test_tag(self, ctx, *, text:str):
        tag = await self.get_tag("test")
        try:
            parser = tag_parser.Parser(text, debug=self.bot._DEBUG, override=TagOverrides(self.bot, ctx, tag, debug=self.bot._DEBUG))
            result = await parser()
        except Exception as e:
            await self.bot.say(f"```diff\n- [{type(e).__name__}]: {e}\n```")
            return

        result = str(result)
        await self.bot.say(f"\* {tag.name} is empty \*" if result == "" else result)

def setup(bot):
    bot.add_cog(Tags(bot))