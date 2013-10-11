from rockmagento import Rockmagento, prettify
import csv

host = 'http://127.0.0.1/magento'
user = 'user'
password = 'password'
rhid = 9 
mediums = 136

RM = Rockmagento(user, password, host, rhid, mediums)

# ------------------------------------------------------------------------
# Add categories
do_categories = False
if do_categories:
	not_music = ['MOVIE','MAGAZINE','BOOK','ACCESSORIES']	# not definative
	music_parent_id = RM.categories['Genres']		# or whatever it's called
	default_id = RM.categories['Default Category']	

	for line in open('genres.txt'):
		line = line.rstrip()
		if line in not_music:
			RM.createCategory(prettify(line), default_id)
		else:
			RM.createCategory(prettify(line), music_parent_id)


# ------------------------------------------------------------------------
# products

do_products = True
fp = open('raw.csv','r')
exported = csv.DictReader(fp,dialect=csv.excel)
for pp in exported:
	print 'Adding ', pp['stockid']
	pid = RM.insertItem(pp)

fp.close()


