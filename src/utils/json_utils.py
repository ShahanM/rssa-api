from flask.json import JSONEncoder
import decimal
import datetime


class RssaJsonEncoder(JSONEncoder):
	def default(self, obj):
		if isinstance(obj, decimal.Decimal):
			return float(obj)
		if isinstance(obj, datetime.timedelta):
			return str(obj)
		if isinstance(obj, datetime.datetime):
			return obj.isoformat
        
		return JSONEncoder.default(self, obj)
