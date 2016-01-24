from django.db import models
from datetime import datetime, time, date
import sys

# fix for utf-8
reload(sys)
sys.setdefaultencoding('utf-8')


class Node(models.Model):
	name = models.CharField(max_length=255)
	query_name = models.CharField(max_length=255)
	image = models.ImageField(upload_to='nodes')
	# first:latitude second:longitude (in future maybe for mobile devices?)
	# geo_loc = models.CharField(max_length=255)

	def __unicode__(self):
		return self.name

	def serialize(self):
		return {'name':self.name,
				'image':self.image.url }

class Route(models.Model):
	start = models.ForeignKey(Node, related_name='start')
	destination = models.ForeignKey(Node, related_name='destination')
	raw_data = models.TextField()

	def __unicode__(self):
		return self.start.name + " => " + self.destination.name

	@property
	def next(self):

		def time_diff(start, end):
		    if isinstance(start, time):
		        assert isinstance(end, time)
		        start, end = [datetime.combine(datetime.min, t) for t in [start, end]]
		    if start <= end:
		        return end - start
		    else:
		        end += timedelta(1)
		        assert end > start
		        return end - start

		try:
			time_list = Time.objects.filter(route=self, time__gte=datetime.now())
			next_in_secs = int(time_diff(datetime.now().time(), time_list[0].time).total_seconds())
		except IndexError, e:
			next_in_secs = ""
		
		try:
			next_next_one = time_list[1].time.strftime("%H:%M")
		except IndexError, e:
			next_next_one = "DONE"

		try:
			time_list = Time.objects.filter(route=self, time__gte=datetime.now())
			next_ring = time_list[0].ring
		except IndexError, e:
			next_ring = False
		
		return {"in_secs": next_in_secs, "next_next_one": next_next_one, "ring": next_ring}


	def save(self, **kwargs):
		super(Route, self).save()
		Time.objects.filter(route=self).delete()
		if self.raw_data:
			ring = False
			for i in self.raw_data.split(" - "):
				if i == "Ring":
					ring = True
					continue
				else:
					Time(ring=ring, route=self, time=datetime.strptime(i, "%H:%M").time()).save()
					ring = False

	def serialize(self):
		return {'destination':self.destination.name,
				'destination_image':self.destination.image.url,
        		'raw_data':self.raw_data,
        		'next':self.next}

class Time(models.Model):
	route= models.ForeignKey(Route, related_name='time')
	time = models.TimeField()
	ring = models.BooleanField(default=False)

	def __unicode__(self):
		return self.route.start.name + " => " + self.route.destination.name + " : " + self.time.strftime("%H:%M")
