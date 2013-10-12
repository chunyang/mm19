""" Special purpose stack for replay attacks
	with size limit 
"""
class ReplayStack(object):
	def __init__(self,maxSize=0):
		self.list = []
		self.maxSize = maxSize

	def push(self,item):
		if self.maxSize == 0:
			pass
		elif len(self.list) == self.maxSize:
			self.list.pop()

		self.list.insert(0,item)

	def pop(self):
		return self.list.pop(0)

	def size(self):
		return len(self.list)