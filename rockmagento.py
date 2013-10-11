"""Utilities for Rockinghorse-Magento data communication"""
import re
import suds
from suds.client import Client

def prettify(ugly):
	"""Attempt to circumvent the 1970s insistence on all-caps"""
	ugly = ugly.upper().replace('&RSQUO;','\'')
	return re.sub("(^|\s|\(|-)([A-Z])([\w']+)", lambda x:x.group(1)+x.group(2)+x.group(3).lower(), ugly)


class Rockmagento:
	"""Wrapper class for the various API things you might want to accomplish.

	Along with your username, password and host, this needs to know two things
	that can be looked up using the web backend. These are id of the magento 
	'attribute set' being used, and the id of the 'medium' attribute. 

	The attribute set is expected to include 'artist', 'title', 'label',
	'medium', 'genre', 'tickler' and 'blurb'."""
	def __init__(self, user, password, host, attr_set_id, medium_attr_id):
		self.client = Client(host+'/index.php/api/v2_soap/index?wsdl=1')
		self.session = self.client.service.login(user, password)
		self.medium_attr_id = medium_attr_id
		self.attr_set_id = attr_set_id

		self.categories =  self.getCategories()
		self.catkeys = {cc[0:4].upper():vv for cc,vv in self.categories.iteritems()}
		self.medium_opts = self.getMediumOpts()

	def _grok_categories(self, category, ddict):
		ddict[category.name] = category.category_id
		for cc in category.children:
			self._grok_categories(cc,ddict)

	def getCategories(self):
		"""Get current list of defined categories"""
		category_dict = {}
		root = self.client.service.catalogCategoryTree(self.session)
		self._grok_categories(root, category_dict)
		return category_dict

	def getMediumOpts(self):
		"""Get current list of defined media options"""
		opts = self.client.service.catalogProductAttributeOptions(self.session, 
			self.medium_attr_id);
		return {o.label: int(o.value) for o in opts if not o.label.isspace()}

	def getAttrs(self):
		"""Gets all additional attributes"""
		pass

	def insertItem(self, rhfields): 
		"""Insert a new item into the magento database. 

		rhfields - dictionary indexed by 'artist', 'title', 'medium', 'label', 
				'price', 'qty', 'catno', and optionally 'tickler' and 'blurb'

		If the item (catno) exists it will call update_item instead"""
		sku = rhfields['stockid'].rstrip().replace(' ', '_')

		try:
			info = self.client.service.catalogProductInfo(self.session, sku, None, None, 'sku')
			print "Item %s already exists (TODO: call update)" % sku
			return -1
		except:
			pass

		artist = prettify(rhfields['artist'])
		title = prettify(rhfields['title'])
		cat_ids = [self.catkeys[rhfields['genre'][:4].upper()]]
		if rhfields['label'][:4].upper() == 'SECO':
			cat_ids.append(self.catkeys['SECO'])


		rh_attr = {'single_data':[ \
			{'key': 'artist', 'value': artist}, \
			{'key': 'medium', 'value': 9}, \
			{'key': 'label', 'value': prettify(rhfields['label'])}, \
			{'key': 'received', 'value': rhfields['received']}, \
			{'key': 'title', 'value': title}] \
		}
		qty = int(rhfields['qty'])
		stock_data = {'qty': qty, 'is_in_stock': 1 if qty > 0 else 0}

		product_deets = 	{
			'categories': cat_ids, \
			'name': artist + ' :: ' + title,\
			'price': rhfields['price'], \
			'visibility': 4, \
			'description': rhfields['blurb'], \
			'short_description': rhfields['tickler'], \
			'weight': 0.0, \
			'tax_class_id': 0, \
			'url_path': sku+'.html', \
			'url_key': sku, \
			'status': 1, \
			'additional_attributes': rh_attr,
			'stock_data': stock_data \
			}

		pid = self.client.service.catalogProductCreate(self.session, 'simple', \
				self.attr_set_id, sku, product_deets);

		return pid


	def updateItem(self, catno, rhfields):
		"""Updates an existing item identified by 'catno' ('sku' in magento)
		
		rhfields - all fields you want to be updated (any of the ones from 
				insert_item above)

		Fails if the catno is not present"""
		pass

	def createCategory(self, name, parent_id, descr='', sortby=['Artist']):
		if name[0:4].upper() in self.catkeys:
			return -1

		details = { \
			'name': name, \
			'is_active': 1, \
			'description': descr, \
		 	'include_in_menu': 1, \
		 	'available_sort_by': sortby, \
		 	'default_sort_by': sortby[0] \
		 	} 

		cid = self.client.service.catalogCategoryCreate(self.session, parent_id, details)
		self.categories[name] = cid;
		self.catkeys[name[0:4].upper()] = cid;

		return cid
