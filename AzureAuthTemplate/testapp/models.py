from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
import json


# Simple model to persist Azure AD user attributes for quick access in views
class AzureUser(models.Model):
	user_id = models.CharField(max_length=255, unique=True)
	name = models.CharField(max_length=255, blank=True)
	first_name = models.CharField(max_length=255, blank=True)
	email = models.EmailField(blank=True)
	office_location = models.CharField(max_length=255, blank=True)
	position = models.CharField(max_length=255, blank=True)
	# store roles as JSON text to remain DB-agnostic; keep simple for sqlite
	roles = models.TextField(blank=True, default='[]')
	graph_token = models.TextField(blank=True, null=True)
	last_seen = models.DateTimeField(auto_now=True)

	def set_roles(self, roles_list):
		self.roles = json.dumps(roles_list, cls=DjangoJSONEncoder)

	def get_roles(self):
		try:
			return json.loads(self.roles)
		except Exception:
			return []

	def __str__(self):
		return f"AzureUser({self.user_id} - {self.email})"
