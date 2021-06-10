import requests, os, re
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize
from tqdm import tqdm

DOMAIN = "https://financialaid.arizona.edu"
CHECKED = []
STACK = []
BAD_URLS = {}
HEADER = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"}
ATTRIBUTES = [".pdf", ".xlsx", ".png", ".ppt", ".xls", ".doc", "@", "bit.ly", "tel:", ".aspx"]

#==============================================================================

def start_url_check():
	"""
	Purpose:
		This function checks that the submitted url is valid and, if so, starts checking its links
	Dependencies:
		requests
	Arguements:
		None
	Returns:
		None
	"""
	# remove text file from previous session
	remove_old_files()

	# get url to check
	url = "https://financialaid.arizona.edu"

	response = requests.get(url, headers=HEADER)

	# if the site has not been updated since it was last visited it will sometimes return a 304 response code. We dont want to mistake these for a redirect
	if response.history:
		not_modified = "<Response [304]>" == str(response.history[0])
	
	# make sure the entered url is valid 
	if response.history and not not_modified:
		print("Bad URL")
	else:
		check(url, "header_site")
		check(url)
		check(url, "footer_site")
		
		while STACK:
			url = STACK.pop()
			if url not in CHECKED:
				check(url)

	return None

#==============================================================================

def remove_old_files():
	try:
		os.remove("url_response.txt")
	except:
		pass
	try:
		os.remove("url_response.txt")
	except:
		pass
	try:
		os.remove("url_response.txt")
	except:
		pass

	return None

#==============================================================================

def check(url, section="main"):
	"""
	Purpose:
		This function begins the process of checking a URL. It gets all the hrefs from a parent page and keeps track of which ones do not return a 200 http response code so they can be appended to a text file. 
	Dependencies:
		BeautifulSoup
	Arguements:
		url - a URL submitted by the user
		section - an id attribute that specifies a section of the page. main in unique to each page, header and foot are on each page. Prevents program from scraping the header and footer of every page. 
	Returns:
		None
	"""
	links = []
	
	soup = BeautifulSoup(requests.get(url, headers=HEADER).content, "html.parser").find(id=section)

	if soup:
		for a in tqdm(soup.findAll('a'),desc=url):
			link = a.get('href')
			if link:
				links += validate_link(link, url)

	if len(links) > 0:
		write_output(links, url)

	# TODO: insert a string inot a regex statement
	word = "UA"

	if word and soup:
		find_word(url, soup, word)

	CHECKED.append(url)
	
	return None

#==============================================================================

def validate_link(link, url):
	clean_link = get_clean_link(link, url)
	response = None
	links = []
	
	if clean_link in BAD_URLS:
		links.append((clean_link, BAD_URLS[clean_link]))
	
	else:
		attribute = bool([True for e in ATTRIBUTES if e in clean_link])
		anchor = '#' in clean_link and url in clean_link
		if not attribute and not anchor and clean_link not in CHECKED:
			response = get_response(clean_link)
	
	if response:
		links.append(response)
		BAD_URLS[response[0]] = str(response[1])

	return links

#==============================================================================

def get_clean_link(link, url):
	"""
	Purpose:
		Sometimes href atrributes dont have a simple url in them. Then can have references and anchors which are not full urls and will not generate an accruate http response. This function will turn the href into a url that can be used to get an accurate response code.
	Dependencies:
		None
	Arguements:
		link - the href pulled from an a tag that may need to be modified so an http response can be generated
		url - the parent page that the link was found on
	Returns:
		A link that is capable of generating a http response code		
	"""
	clean_link = link

	# relative path (/page_name/page_name2) 
	if link[0] == '/': 
		if DOMAIN[-1] == '/':
			clean_link = DOMAIN[:-1] + link
		else:
			clean_link = DOMAIN + link

	# anchor (#go_here)
	if link[0] == '#':
		if url[-1] == '/':
			clean_link = url[:-1] + link
		else:
			clean_link = url + link
	
	# relative path (page_name/page_name2)
	if '.' not in clean_link:
		if DOMAIN[-1] == '/':
			clean_link = DOMAIN + link
		else:
			clean_link = DOMAIN + '/' + link

	return clean_link

#==============================================================================

def get_response(clean_link):
	"""
	Purpose:
		This function gets an http response from a cleaned link. 
	Dependencies:
		requests
	Arguements:
		clean_link - a url that has been processed by clean_link
	Returns:
		if a response code is generated, the link and its reponse code
		if no response code is generated, the link and "No Response"
		if a 200 response code is generated, None
	"""
	try:
		response = requests.get(clean_link, headers=HEADER)

		# if the site has not been updated since it was last visited it will sometimes return a 304 response code. We dont want to mistake these for a redirect
		if response.history:
			not_modified = "<Response [304]>" == str(response.history[0])
		else: # there is a reponse history but the code is not 304
			not_modified = False
			
		# the link did not return a 200 response code
		if response.history and not not_modified:
			BAD_URLS[clean_link] = str(response.history[0])
			return clean_link, str(response.history[0])

	except:
		# not sure what happened, consider the link bad
		BAD_URLS[clean_link] = "No Response"
		return clean_link, "No Response"

	if DOMAIN in clean_link and clean_link not in CHECKED:
		STACK.append(clean_link)
		output = open("fa urls.txt",'a')
		output.write(clean_link + "\n")
		output.close()
	
	# the link returned a 200 response code
	return None

#==============================================================================

def write_output(links, url):
	"""
	Purpose:
		Creates a text file of urls that did not return a 200 response code
	Dependencies:
		None
	Arguements:
		links - a list of tuples consisting of the url and http response code
		url - the parent page that the links were found on
	Returns:
		None	
	"""

	output = open("url_response.txt", 'a', encoding="utf-8")
	output.write(url + "\n")
	for e in links:
		if e[0]:
			output.write("\t" + e[0] + ": " + e[1] + "\n")
	output.write("\n")
	output.close()	

	return None

#==============================================================================

def find_word(url, soup, word):
	count = 0
	text = sent_tokenize(soup.get_text())
	
	for sentence in text:
		if re.search(r'\bUA\b', sentence):
			count += 1

	if count:
		output = open("found_words.txt", 'a', encoding="utf-8")
		output.write(url + "\n")
		if count > 1:
			output.write("\t" + str(count) + " sentences with " + word + "\n")
		else:
			output.write("\t" + str(count) + " sentence with " + word + "\n")
			output.write("\n")
			output.close()

	return None

#==============================================================================

def main():

	start_url_check()
	print("Finished")

#==============================================================================

if __name__ == '__main__':
	main()