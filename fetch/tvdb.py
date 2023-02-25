from re import compile
from time import strptime
from codecs import open
import json
import requests
import os.path
from urlgrab import URLTimeoutError


class tvdb:
    args = {"sid": "Tvdb id"}
    login = json.loads(
        open(os.path.join(os.path.dirname(__file__), "tvdb-login")).read()
    )
    token = None

    def get_token(self):
        print("getting token")
        t = requests.post("https://api.thetvdb.com/login", json=self.login)
        if t.status_code == 503:
            print("TVDB LOGIN DOWN")
            return
        t.raise_for_status()
        self.token = t.json()["token"]

    def run(self, inf, sid):
        neweps = []
        page = 1
        while True:
            url = "https://api.thetvdb.com/series/%s/episodes?page=%d" % (sid, page)
            if not inf["cache"].has_item(url, max_age=60 * 60 * 24 * 2):
                if self.token == None:
                    self.get_token()
                if self.token == None:  # failure
                    return inf["core"](inf, [])

            try:
                data = (
                    inf["cache"]
                    .get(
                        url,
                        headers={"Authorization": "Bearer %s" % self.token},
                        max_age=60 * 60 * 24 * 2,
                    )
                    .read()
                )
            except URLTimeoutError as e:
                if e.code == 404:
                    break
                raise
            episodes = json.loads(data)["data"]
            for ep in episodes:
                try:
                    neweps.append(
                        (
                            ep["airedSeason"],
                            ep["airedEpisodeNumber"],
                            strptime(ep["firstAired"], "%Y-%m-%d")
                            if ep["firstAired"] != ""
                            and ep["firstAired"] != "0000-00-00"
                            else None,
                            ep["episodeName"],
                        )
                    )
                except:
                    print(ep)
                    raise
            if len(episodes) == 100:
                page += 1
                continue
            else:
                break

        return inf["core"](inf, neweps)
