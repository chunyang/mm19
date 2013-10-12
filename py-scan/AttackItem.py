class AttackItem(object):
	def __init__(self, coord, nAttacks):
		self.coord = coord
		self.nAttacks = nAttacks

	def __str__(self):
		return "<%s> nAttacks=%d" % (self.coord,self.nAttacks)

	def __repr__(self):
		return "<%s> nAttacks=%d" % (self.coord,self.nAttacks)
