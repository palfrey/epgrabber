import re
from time import strptime
from xml.dom import minidom


class tvrage:
    args = {"sid": "Tvrage id from http://services.tvrage.com/info.php?page=main"}

    def run(self, inf, sid):
        url = "http://services.tvrage.com/feeds/episode_list.php?sid=%s" % sid
        data = inf["cache"].get(url, max_age=60 * 60 * 24 * 2).read()
        data = data.encode("utf-8")
        open("dump", "wb").write(data)
        xml = minidom.parseString(data)
        neweps = []
        for seasonNode in xml.getElementsByTagName("Season"):
            season = seasonNode.getAttribute("no")
            for ep in seasonNode.getElementsByTagName("episode"):
                title = ep.getElementsByTagName("title")[0].firstChild.data
                airdate = ep.getElementsByTagName("airdate")[0].firstChild.data
                if airdate.find("00") != -1:
                    date = None
                else:
                    date = strptime(airdate, "%Y-%m-%d")
                epnum = ep.getElementsByTagName("seasonnum")[0].firstChild.data
                # print title, date, season, epnum
                neweps.append((int(season), int(epnum), date, title))
        return inf["core"](inf, neweps)
