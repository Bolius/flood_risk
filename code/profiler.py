from datetime import datetime

# import json
import asyncio
import aiohttp

# import pandas as pd


async def call_api(session, address):
    start = datetime.now()
    async with session.get(
        "https://exl9ly9iwa.execute-api.eu-central-1.amazonaws.com/Prod/flood-risk",
        params={"address": address},
    ) as response:
        await response.json()
        end = datetime.now()
        return {"status": response.status, "time": str((end - start))}


async def fetch_all(addresses, loop):
    async with aiohttp.ClientSession(loop=loop) as session:
        results = await asyncio.gather(
            *[call_api(session, address) for address in addresses],
            return_exceptions=True,
        )
        return results


# start = datetime.now()
# loop = asyncio.get_event_loop()
# with open("./test_addreesses.json") as dataFile:
#     addreses = json.load(dataFile)["objects"]
#     addreses = [add["values"]["acadr_name"] for add in addreses]
# results = loop.run_until_complete(fetch_all(addreses, loop))
# end = datetime.now()
# print(f"Ran {len(addreses)} in {end - start}")
# results = pd.DataFrame(results)
# results.to_csv("time_results.csv", index=False)


# results = pd.read_csv("time_results.csv")
# times = results["time"].map(lambda time: float(time.split(":")[-1]))
# fig = times.plot(
#     kind="hist", title=f"Mean: {round(times.mean(),2)} -- STD: {round(times.std(),2)}"
# ).get_figure()
#
# fig.savefig("l.png")
