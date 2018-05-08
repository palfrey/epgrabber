from re import compile
from time import strptime
from codecs import open
import json
import requests
import os.path

class tvdb:
	args = {"sid":"Tvdb id"}

	login = json.loads(open(os.path.join(os.path.dirname(__file__), "tvdb-login")).read())

	token = None

	def get_token(self):
		print "getting token"
		t = requests.post("https://api.thetvdb.com/login", json=self.login)
		t.raise_for_status()
		self.token = t.json()["token"]

	def run(self,inf,sid):
		url = "https://api.thetvdb.com/series/%s/episodes" % sid
		if not inf["cache"].has_item(url):
			if self.token == None:
				self.get_token()

		data = inf["cache"].get(url, headers={"Authorization": "Bearer %s" % self.token}, max_age=60*60*24*2).read()
		episodes = json.loads(data)["data"]
		if len(episodes) > 100:
			raise Exception
		neweps = []
		for ep in episodes:
			try:
				neweps.append((ep["airedSeason"], ep["airedEpisodeNumber"], strptime(ep["firstAired"], "%Y-%m-%d") if ep["firstAired"] != "" else None, ep["episodeName"]))
			except:
				print ep
				raise
		return inf["core"](inf,neweps)
