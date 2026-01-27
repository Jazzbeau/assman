import asyncio

import psutil

from apps.discord_app import DiscordApp


async def test_app():
    dc = DiscordApp()
    print("Launching discord result:\t", end="")
    print(await dc.launch())
    dc_props = dc.get_process_properties()
    pc = psutil.Process(dc_props.process_id)
    await dc.start_playwright()
    print(f"Discord process running:\t{dc.is_running()}")
    print(f"Discord process status: \t{pc.status()}")
    print(dc.find_window_name())
    if dc.session:
        dc_pw = dc.session.get_pw_props()
        print(await dc_pw.main_page.title())
        await dc_pw.main_page.goto("http://www.google.com")
        print(dc.find_window_name())
        print(await dc_pw.main_page.title())
    await asyncio.sleep(10)
    print("Terminating Discord")
    await dc.terminate()
    print(f"Discord process running:\t{dc.is_running()}")
    print(f"Discord process status: \t{pc.status()}")


async def test_server():
    dc = DiscordApp()
    await dc.launch()
    await dc.start_playwright()
    await dc.session.learn_servers()
    server = list(dc.session.server_list.values())[0]
    await dc.session.learn_channels(server)
