import asyncio
import time
from pprint import pprint

import psutil
from playwright.async_api import Locator

from apps.discord_app import DiscordApp
from models.discord_server import DiscordChannel, DiscordServer


async def test_app():
    dc = DiscordApp()
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


async def test_routine():
    # Launch app and session
    discord = DiscordApp()
    await discord.launch()
    await discord.start_playwright()
    await discord.learn_servers()

    # Get first server
    res = discord.get_servers_by_name("zone", strict_match=False, case_sensitive=False)
    assert len(res) == 1
    plonch_zone = res[0]
    await discord.learn_channels(plonch_zone)

    # Get second server
    res = discord.get_servers_by_name(
        "gavin and", strict_match=False, case_sensitive=False
    )
    assert len(res) == 1
    gavin_server = res[0]
    await discord.learn_channels(gavin_server)

    gavin_text_channels = gavin_server.get_channels("text")
    gavin_voice_channels = gavin_server.get_channels("voice")

    plonch_text_channels = plonch_zone.get_channels("text")
    plonch_voice_channels = plonch_zone.get_channels("voice")

    for category in [
        (gavin_text_channels, "Gavin Text Channel"),
        (gavin_voice_channels, "Gavin Voice Channel"),
        (plonch_text_channels, "Plonch Text Channel"),
        (plonch_voice_channels, "Plonch Voice Channel"),
    ]:
        for channel in category[0]:
            print(f"{category[1]}:\t {channel.name}")


async def test_discord():
    discord = DiscordApp()
    failed_cases = []
    test_num = 0
    ts = t0 = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}] Launching Discord: ")
        await discord.launch()
        assert discord.is_running()
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        et = type(e).__name__
        te = time.time()
        print(f"FAILED IN {round(te-ts, 3)}s WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}] Injecting Playwright: ")
        await discord.start_playwright()
        assert discord.session
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        et = type(e).__name__
        te = time.time()
        print(f"FAILED IN {round(te-ts, 3)}s WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}] Learn Servers: ")
        await discord.learn_servers()
        assert discord.session.server_list
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        te = time.time()
        et = type(e).__name__
        print(f"FAILED IN {round(te-ts, 3)}s WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}] Get (Retrieve) Servers: ")
        servers = discord.get_servers()
        assert servers
        t4 = time.time()
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        te = time.time()
        et = type(e).__name__
        t4 = time.time()
        print(f"FAILED IN {round(te-ts, 3)}s WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}] Correct value for returned server: ")
        active_server = list(servers.values())[0]
        assert isinstance(active_server, DiscordServer)
        t5 = time.time()
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        et = type(e).__name__
        te = time.time()
        t5 = time.time()
        print(f"FAILED IN {round(te-ts, 3)}s WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}] Learn Server Channels: ")
        await discord.learn_channels(active_server)
        assert len(list(discord.session.channel_list.values())) > 5
        t6 = time.time()
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        te = time.time()
        et = type(e).__name__
        t6 = time.time()
        print(f"FAILED IN {round(te-ts, 3)}s WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}] Correct value for returned channel: ")
        active_channel = list(discord.session.channel_list.values())[0]
        assert isinstance(active_channel, DiscordChannel)
        t7 = time.time()
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        te = time.time()
        et = type(e).__name__
        t7 = time.time()
        print(f"FAILED IN {round(te-ts)}s WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}] Navigate to five channels: ")
        channels = list(discord.session.channel_list.values())[0:5]
        for channel in channels:
            await discord.session.navigate_to_text_channel(channel)
            await asyncio.sleep(0.2)
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        te = time.time()
        et = type(e).__name__
        print(f"FAILED IN {te-ts} WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}]: Session: Get Servers Function")
        servers = discord.session.get_servers()
        assert servers
        assert isinstance(list(servers.values())[0], DiscordServer)
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        te = time.time()
        et = type(e).__name__
        print(f"FAILED IN {te-ts} WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}]: Session: Get Channel by ID Function")
        channel_id = list(discord.session.channel_list.keys())[0]
        channel = discord.session.get_channel_by_id(channel_id)
        assert isinstance(channel, DiscordChannel)
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        te = time.time()
        et = type(e).__name__
        print(f"FAILED IN {te-ts} WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}]: Session: Get Server by ID Function")
        server_id = list(discord.session.server_list.keys())[0]
        server = discord.session.get_server_by_id(server_id)
        assert isinstance(server, DiscordServer)
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        te = time.time()
        et = type(e).__name__
        print(f"FAILED IN {te-ts} WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}]: Session: Get Server Locator Function, test locator")
        #

        server = list(discord.session.server_list.values())[0]
        server_locator = discord.session.get_server_locator(server)
        print(server_locator)
        assert isinstance(server_locator, Locator)
        count = await server_locator.count()
        await server_locator.click()  # button="right")
        assert count == 1
        #
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        te = time.time()
        et = type(e).__name__
        print(f"FAILED IN {te-ts} WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")

    ts = time.time()
    try:
        test_num += 1
        print(f"[TEST {test_num}]: Navigate to server function")
        #

        server = list(discord.session.server_list.values())[0]
        await discord.session.navigate_to_server(server)

        #
        te = time.time()
        print(f"PASSED IN {round(te-ts, 3)}s")
    except Exception as e:
        te = time.time()
        et = type(e).__name__
        print(f"FAILED IN {te-ts} WITH EXCEPTION {et}")
        print(f"MESSAGE: {str(e)}")
        failed_cases.append(test_num)
    finally:
        print("")
    print(f"TESTS COMPLETED IN {round(te-ts, 3)}s")
    if not failed_cases:
        print("NO FAILED CASES")
    else:
        print(f"FAILED CASES: {failed_cases}")
