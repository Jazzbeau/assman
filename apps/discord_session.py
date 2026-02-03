import asyncio
from dataclasses import dataclass
from typing import Literal

import requests
from playwright.async_api import (
    Browser,
    BrowserContext,
    Locator,
    Page,
    Playwright,
    async_playwright,
)

import apps.discord_session_utils as utils
from config import config
from models.discord_server import DiscordChannel, DiscordServer


@dataclass
class PlaywrightProperties:
    rpc_port: int
    playwright_instance: Playwright
    browser: Browser
    context: BrowserContext
    main_page: Page
    debug_websocket_url: str


class DiscordSession:
    def __init__(self, app):
        self.app = app
        self.pw_properties: PlaywrightProperties | None = None
        self.server_list: dict[str, DiscordServer] = {}
        self.server_locators: dict[str, Locator] = {}
        self.channel_list: dict[str, DiscordChannel] = {}
        self.channel_locators: dict[str, Locator] = {}

    async def start(self):
        t_rpc_port: int = config.DISCORD_RPC_PORT
        t_playwright_instance: Playwright
        t_browser: Browser
        t_context: BrowserContext
        t_main_page: Page
        t_debug_websocket_url: str
        t_rpc_response = requests.get(
            f"http://localhost:{t_rpc_port}/json/version"
        ).json()
        if "webSocketDebuggerUrl" not in t_rpc_response:
            raise ValueError(
                "No RPC Websocket debugger URL found in RPC response from Discord"
            )

        t_debug_websocket_url = t_rpc_response["webSocketDebuggerUrl"]
        if not t_debug_websocket_url:
            raise ValueError("Debug websocket URL was empty")
        t_playwright_instance = await async_playwright().start()
        t_browser = await t_playwright_instance.chromium.connect_over_cdp(
            t_debug_websocket_url
        )
        if len(t_browser.contexts) > 1:
            raise ValueError("Found multiple Discord Browser Contexts, expected 1")
        elif len(t_browser.contexts) == 0:
            raise ValueError("Browser contexts was empty for Discord instance")
        t_context = t_browser.contexts[0]
        if len(t_context.pages) > 1:
            raise ValueError(
                "Found too many pages in Discord Browser context, expected 1"
            )
        if len(t_context.pages) == 0:
            raise ValueError(
                "Could not find page in Discord Browser context, expected 1"
            )
        if "discord.com" not in t_context.pages[0].url:
            raise ValueError("Discord was not found in URL of main Discord Page")
        t_main_page = t_context.pages[0]
        self.pw_properties = PlaywrightProperties(
            rpc_port=t_rpc_port,
            playwright_instance=t_playwright_instance,
            browser=t_browser,
            context=t_context,
            main_page=t_main_page,
            debug_websocket_url=t_debug_websocket_url,
        )

    # Setters / Builders
    def add_server(self, server: DiscordServer, server_locator: Locator):
        self.server_list[server.id] = server
        self.server_locators[server.id] = server_locator

    def add_channel(self, channel: DiscordChannel, channel_locator: Locator):
        self.channel_list[channel.id] = channel
        self.channel_locators[channel.id] = channel_locator
        self.server_list[channel.server_id].channels[channel.id] = channel

    # Getters
    def get_servers(self) -> dict[str, DiscordServer]:
        return self.server_list

    def get_servers_as_list(self) -> list[DiscordServer]:
        return list(self.server_list.values())

    def get_channels(
        self,
        channel_type: Literal["any", "voice", "text"] = "any",
    ) -> list[DiscordChannel]:
        return utils.get_channels(self.channel_list, channel_type)

    def get_server_by_id(self, id: str) -> DiscordServer:
        return utils.get_server_by_id(self.server_list, id)

    def get_channel_by_id(self, id: str) -> DiscordChannel:
        return utils.get_channel_by_id(self.channel_list, id)

    def get_channels_by_name(
        self,
        name: str,
        strict_match=True,
        case_sensitive=True,
        channel_type: Literal["all", "voice", "text"] = "all",
    ) -> list[DiscordChannel]:
        return utils.get_channels_by_name(
            self.channel_list, name, strict_match, case_sensitive, channel_type
        )

    def get_servers_by_name(
        self,
        name: str,
        strict_match=True,
        case_sensitive=True,
    ) -> list[DiscordServer]:
        return utils.get_servers_by_name(
            self.server_list, name, strict_match, case_sensitive
        )

    # Playwright Factories
    async def build_channel_locator(self, channel: DiscordChannel) -> Locator:
        page = self.get_pw_props().main_page
        locator_identifier = f"channels___{channel.id}"
        new_locator = page.locator(f'a[data-list-item-id="{locator_identifier}"]')
        located_data_id = await new_locator.get_attribute("data-list-item-id")
        located_name = await new_locator.locator('div[class^="name"]').inner_text()
        assert (located_name, located_data_id) == (channel.name, locator_identifier)
        return new_locator

    async def build_channel(
        self, channel: Locator, ch_type: Literal["text", "voice"], server_id: str
    ) -> tuple[DiscordChannel, Locator]:
        name = await channel.locator('div[class^="name"]').inner_text()
        data_id = await channel.get_attribute("data-list-item-id")
        if not isinstance(data_id, str):
            raise ValueError("Channel ID was not of expected string type")
        # Extract channel id from attribute `channel___{id}` -> [`channel`, `{id}`]
        id = data_id.split("___")[-1]
        new_channel = DiscordChannel(id, server_id, name, ch_type)
        new_locator = await self.build_channel_locator(new_channel)
        return (new_channel, new_locator)

    async def build_server_locator(self, server: DiscordServer) -> Locator:
        page = self.get_pw_props().main_page
        server_locator = page.locator(
            f'[data-list-item-id="guildsnav___{server.id}"]:has(img):has(span)'
        )
        assert f"guildsnav___{server.id}" == await server_locator.get_attribute(
            "data-list-item-id"
        )

        return server_locator

    async def build_server(self, server: Locator) -> tuple[DiscordServer, Locator]:
        name = await server.locator("span").inner_text()
        img = await server.locator("img").get_attribute("src")
        if not isinstance(img, str):
            raise ValueError(
                "Could not fetch image id correctly, did not yield string type"
            )
        id_attr = await server.get_attribute("data-list-item-id")
        if not isinstance(id_attr, str):
            raise ValueError(
                "Could not fetch data-list-item-id correctly, did not yield string type"
            )
        id = id_attr.split("___")[1]

        new_server = DiscordServer(id=id, name=name, image_url=img, channels={})
        new_server_locator = await self.build_server_locator(new_server)
        return (new_server, new_server_locator)

    # Playwright Getters
    def get_pw_props(self) -> PlaywrightProperties:
        if self.pw_properties:
            return self.pw_properties
        else:
            raise ValueError("Requested uninitialised Playwright properties")

    def get_server_locator(self, server: DiscordServer) -> Locator:
        try:
            return self.server_locators[server.id]
        except KeyError:
            raise FileNotFoundError(
                f"Server {server.name} did not have corresponding locator in server locator list"
            )

    def get_channel_locator(self, channel: DiscordChannel) -> Locator:
        try:
            return self.channel_locators[channel.id]
        except KeyError:
            raise FileNotFoundError(
                f"Channel {channel.name} of server {self.get_server_by_id(channel.id).name} did not have corresponding locator in channel locator list"
            )

    async def get_channel_nav(self) -> Locator:
        page = self.get_pw_props().main_page
        channel_nav = page.locator('[aria-label="Channels"]')
        assert await channel_nav.count() == 1
        return channel_nav

    async def get_textbox_locator(self) -> Locator:
        page = self.get_pw_props().main_page
        try:
            textbox_locator = page.locator('[role="textbox"][aria-label*="Message"]')
            assert await textbox_locator.count() == 1
            return textbox_locator
        except AssertionError:
            raise ValueError(
                "Found incorrect number of textbox elements in channel view"
            )

    # Playwright Actions
    async def expand_categories(self):
        async def _expand_categories(channel_nav: Locator):
            collapsed_categories = channel_nav.locator('[aria-expanded="false"]')
            while await collapsed_categories.count() != 0:
                target = collapsed_categories.first
                await target.click()

        try:
            await asyncio.wait_for(
                _expand_categories(await self.get_channel_nav()), timeout=5
            )
        except asyncio.TimeoutError:
            raise asyncio.TimeoutError(
                "Timeout error waiting to expand collapsed discord categories on server discovery"
            )

    async def learn_servers(self) -> None:
        page = self.get_pw_props().main_page
        servers = await page.locator(
            '[aria-label="Servers"] [data-list-item-id^="guildsnav___"]:has(img):has(span)'
        ).all()
        for server in servers:
            new_server, new_locator = await self.build_server(server)
            self.add_server(new_server, new_locator)

    async def learn_channels(self, server: DiscordServer) -> None:
        await self.navigate_to_server(server)
        page = self.get_pw_props().main_page
        text_channel_loc = page.locator('[aria-label*="(text channel)"]')
        voice_channel_loc = page.locator('[aria-label*="(voice channel)"]')
        for text_channel in await text_channel_loc.all():
            new_channel, new_locator = await self.build_channel(
                text_channel, "text", server.id
            )
            self.add_channel(new_channel, new_locator)
        for voice_channel in await voice_channel_loc.all():
            new_channel, new_locator = await self.build_channel(
                voice_channel, "voice", server.id
            )
            self.add_channel(new_channel, new_locator)

    # Playwright Navigation Actions
    async def navigate_to_server(self, server: DiscordServer) -> None:
        page = self.get_pw_props().main_page
        locator = self.get_server_locator(server)
        await locator.click()
        await page.wait_for_url(f"**channels/{server.id}**")
        await self.expand_categories()

    async def navigate_to_text_channel(self, channel: DiscordChannel) -> None:
        if channel.type != "text":
            # TODO: this *should* be doable, voice channels DO have a text channel component
            raise ValueError("Cannot navigate to text channel")
        page = self.get_pw_props().main_page
        # Channel requires server to be active
        server = self.get_server_by_id(channel.server_id)
        await self.navigate_to_server(server)

        locator = self.get_channel_locator(channel)
        await locator.click()
        await page.wait_for_url(f"**channels/{server.id}/{channel.id}**")
