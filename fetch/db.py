import re

# dattebayo
class db:
    def run(self, inf, prefix):
        cache = inf["cache"]
        data = cache.get("http://www.dattebayo.com/t/").read()
        items = re.findall("/t/([a-z]+)([\d-]+)\.torrent", data)
        # print items
        poss = []
        for (pfx, number) in items:
            if number.find("-") != -1:
                test = int(number.split("-")[0])
            else:
                test = int(number)
            if prefix == pfx and test > inf["episode"]:
                poss.append(number)
        if len(poss) == 0:
            return None
        best = sorted(poss)[0]

        if best.find("-") == -1:
            number = int(best)
        else:
            number = int(best.split("-", 2)[1])

        return {
            "name": inf["name"],
            "epnum": number,
            "date": inf["yesterday"],
            "url": "http://www.dattebayo.com/t/%s%s.torrent" % (prefix, best),
        }
