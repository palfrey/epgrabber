import transmissionrpc
class RobustClient:
	def __init__(self, host, port, user, password):
		self.host = host
		self.port = port
		self.user = user
		self.password = password
		self._make_client()

	def info(self, k):
		return self._robust(lambda: self.client.info(k)[k])

	def _robust(self, act):
		try:
			return act()
		except transmissionrpc.error.TransmissionError:
			self._make_client()
			return act()

	def list(self):
		return self.client.list()

	def remove(self, id):
		return self._robust(lambda: self.client.remove(id))

	def _make_client(self):
		self.client = transmissionrpc.Client(self.host, self.port, self.user, self.password)
