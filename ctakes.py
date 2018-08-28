## IMPORTS
import sys
import requests
import json
from functools import partial

import cloudconvert

import package.apis.snomed_api
import package.apis.wikipedia_api
from package.apis.entrez_api import *
import package.apis.cloudconvert_api as cc

from package.classes.entity_class import Entity
from package.classes.summary_class import Summary

from PyQt5.QtWidgets import (QFileDialog, QPushButton, QWidget, QLineEdit, QApplication, QVBoxLayout, QLabel)



def check_key(annotation, key):
	try:
		value = annotation[key]
		return value
	except KeyError:
		return None


def print_dict(o):
	for x in o: print(f'{x}: {o[x]}')


class Button(QPushButton):
  
	def __init__(self, title, parent):
		super().__init__(title, parent)
		

class Exit(QPushButton):
  
	def __init__(self, title, parent):
		super().__init__(title, parent)
		

class UploadWindow(QWidget):
  
	def __init__(self):
		super().__init__()
		
		self.initUI()
		
		
	def initUI(self):

		edit = QLineEdit('', self)
		edit.setDragEnabled(True)
		edit.move(30, 65)

		button = Button("Button", self)
		button.move(190, 65)
		button.clicked.connect(self.upload_pdf)

		button2 = Button("Exit", self)
		button2.move(190, 85)
		button2.clicked.connect(self.exit)
		
		self.setWindowTitle('cTAKES Program')
		self.setGeometry(300, 300, 300, 150)

	def exit(self):
		self.close()
		# sys.exit(app.exec_())
    

	def upload_pdf(self):
		dialog = QFileDialog()
		fname = dialog.getOpenFileName(None, "Import PDF", "", "PDF data file (*.pdf)")
		print("FNAME PRINT: ", fname[0])
		self.fname = fname[0]


def main():

	print("########################")

	app = QApplication(sys.argv)
	ex = UploadWindow()
	ex.show()
	app.exec_()  

	print("BEFORE EXIT")

	print(ex.fname)

	print("AFTER EXIT")


	# import sys
	# from PyQt5.QtWidgets import QApplication, QWidget
	
	# app = QApplication(sys.argv)

	# w = QWidget()
	# w.resize(250, 150)
	# w.move(300, 300)
	# w.setWindowTitle('Simple')
	# w.show()
	# sys.exit(app.exec_())


	# pass the pdf to the cloud converter
	cc.main(ex.fname)

	# open text to be parsed
	input_file = open("package/output.txt", "r")
	input_file = input_file.read()
	

	# sample texts
	text01 = "Patient took an aspirin for knee pain."
	text02 = "Patient has a strong aspirin allergy. She took paracetamol 500mg orally on March 1, 2015. Her father also has medication allergies"
	text03 = "Patient took a strong aspirin for her parkinsons."
	text04 = "Alex took an aspirin for her knee pain. John took paracetamol for his ankle pain."
	text05 = "The patient seems to be calm. Their blood pressure is low. The baby has a small scar on it's forehead. The baby is taking paracetamol."
	text06 = "Paracetamol. Pain. Knee. Stretching. Down syndrome."

	# set the virtual machine IP address, port is 80
	virtualmachine_ip = '51.140.141.203'
	port = '80'

	# call ctakes-server
	req = requests.get("http://{}:{}/ctakes?text={}".format(virtualmachine_ip, port, input_file))

	# convert the request json into list
	req_list = req.json()
	list_len = len(req_list)

	# make a dictionary
	json_dict = json.loads(req.text)

	# open new file in directory and save the data as json
	print("Writing to JSON file....")
	json_file = open('package/data/data.json', 'w')
	json_file.write(json.dumps(req_list))
	json_file.close()
	print("JSON file saved!")


	# matching keys for JSON file
	med_ment = "org.apache.ctakes.typesystem.type.textsem.MedicationMention"
	sym_ment = "org.apache.ctakes.typesystem.type.textsem.SignSymptomMention"
	ana_ment = "org.apache.ctakes.typesystem.type.textsem.AnatomicalSiteMention"
	pro_ment = "org.apache.ctakes.typesystem.type.textsem.ProcedureMention"
	dis_ment = "org.apache.ctakes.typesystem.type.textsem.DiseaseDisorderMention"


	# store data
	medicine_list = []
	symptom_list = []
	anatomy_list = []
	procedure_list = []
	disease_list = []

	# duplicate checks
	duplicate_checklist_codes = []
	duplicate_checklist_names = []


	def general_extractor(number, typ):
		annotation = json_dict[i]["annotation"]
		num = 0

		try:
			ontology = annotation["ontologyConceptArr"][num]["annotation"]
		except TypeError:
			# doesnt exist in json
			return

		# check if the scheme is SNOMED
		while(ontology["codingScheme"] == "RXNORM"):
			num = num+1
			try:
				ontology = annotation["ontologyConceptArr"][num]["annotation"]
			except IndexError:
				# snomed doesnt exist
				return


		# get generic information
		name = ontology["preferredText"]
		subject = annotation["subject"]
		snomed_code = ontology["code"]


		if name == None:
			return

		## empty variables
		med_route = None
		med_allergy = None
		med_strength = None
		med_frequency = None
		med_duration = None
		med_dosage = None

		sym_body_laterality = None
		sym_history = None
		sym_duration = None
		sym_start_time = None
		sym_severity = None
		sym_body_location = None

		ana_body_laterality = None
		ana_body_side = None

		pro_duration = None
		pro_method = None
		pro_start_time = None
		pro_end_time = None
		pro_body_location = None
		pro_device = None

		dis_course = None
		dis_start_time = None
		dis_end_time = None
		dis_associated_symptom = None
		dis_body_location = None
		dis_severity = None
		dis_alleviating_factor = None
		dis_exacerbating_factor = None



		## get additional contextual information if available

		if(typ == "medicine"):
			# see if additional medication information available, if not then continue
			med_route = check_key(annotation, "medicationRoute")
			med_allergy = check_key(annotation, "medicationAllergy")
			med_strength = check_key(annotation, "medicationStrength")
			med_frequency = check_key(annotation, "medicationFrequency")
			med_duration = check_key(annotation, "medicationDuration")
			med_dosage = check_key(annotation, "medicationDosage")

		if(typ == "symptom"):
			# see if additional symptom information available, if not then continue
			sym_body_laterality = check_key(annotation, "bodyLaterality")
			sym_history = check_key(annotation, "historyOf")
			sym_duration = check_key(annotation, "duration")
			sym_start_time = check_key(annotation, "startTime")
			sym_severity = check_key(annotation, "severity")
			sym_body_location = check_key(annotation, "bodyLocation")

		if(typ == "anatomy"):
			# see if additional symptom information available, if not then continue
			ana_body_laterality = check_key(annotation, "bodyLaterality")
			ana_body_side = check_key(annotation, "bodySide")

		if(typ == "procedure"):
			# see if additional symptom information available, if not then continue
			pro_duration = check_key(annotation, "duration")
			pro_method = check_key(annotation, "method")
			pro_start_time = check_key(annotation, "startTime")
			pro_end_time = check_key(annotation, "endTime")
			pro_body_location = check_key(annotation, "bodyLocation")
			pro_device = check_key(annotation, "procedureDevice")

		if(typ == "disease/disorder"):
			# see if additional symptom information available, if not then continue
			dis_course = check_key(annotation, "course")
			dis_start_time = check_key(annotation, "startTime")
			dis_end_time = check_key(annotation, "endTime")
			dis_history = check_key(annotation, "historyOf")
			dis_associated_symptom = check_key(annotation, "associatedSignSymptom")
			dis_body_location = check_key(annotation, "bodyLocation")
			dis_severity = check_key(annotation, "severity")
			dis_alleviating_factor = check_key(annotation, "alleviatingFactor")
			dis_exacerbating_factor = check_key(annotation, "exacerbatingFactor")




		print("")

		# duplicate filters
		for ent in duplicate_checklist_codes:
			if(ent==snomed_code):
				return

		for ent in duplicate_checklist_names:
			if(ent==name):
				return


		# create simple entity
		# ent = Entity(name, subject, snomed_code, typ)

		# create complex entity
		ent = Entity(name, subject, snomed_code, typ, med_route, med_allergy, med_strength, med_frequency, med_duration, med_dosage, sym_body_laterality, sym_history, sym_duration, sym_start_time, sym_severity, sym_body_location, ana_body_laterality, ana_body_side, pro_duration, pro_method, pro_start_time, pro_end_time, pro_body_location, pro_device, dis_course, dis_start_time, dis_end_time, dis_associated_symptom, dis_body_location, dis_severity, dis_alleviating_factor, dis_exacerbating_factor)


		# get PUBMED articles
		# ent.get_articles()

		# print articles
		# ent.printArticles()

		# get SNOMED term from SNOMED database
		# ent.get_snomed_term()

		# get 2 sentence wikipedia description (NOTE: takes a while)
		# ent.get_wikipedia_description(2)

		# get image of entity
		# ent.get_image()


		# print all available information on entity to console
		ent.printAll()

		# json = ent.toJSON()

		# print("Writing to JSON file....")
		# json_file = open('package/data/ENTITY.json', 'w')
		# json_file.write(json)
		# json_file.close()
		# print("JSON file saved!")

	
		

		#for duplicate checks
		duplicate_checklist_codes.append(ent.snomed_code())
		duplicate_checklist_names.append(ent.name())


		# store entity
		def add_to_medicine_list():
			medicine_list.append(ent)
		def add_to_symptom_list():
			symptom_list.append(ent)
		def add_to_anatomy_list():
			anatomy_list.append(ent)
		def add_to_procedure_list():
			procedure_list.append(ent)
		def add_to_disease_list():
			disease_list.append(ent)

		def add_to_list(typ):

			switcher = {
				"medicine": add_to_medicine_list,
				"symptom": add_to_symptom_list,
				"anatomy": add_to_anatomy_list,
				"procedure": add_to_procedure_list,
				"disease/disorder": add_to_disease_list
			}
			func = switcher.get(typ, lambda: "No mention")

			func()

		add_to_list(ent.type())


		# print("--NAME: {}".format(name))
		# print("--SUBJECT: {}".format(subject))
		# print("--SNOMED: {}".format(snomed_code))


	def medication_mention(number):
		typ = "medicine"
		general_extractor(number, typ)
		# return "medicine"
	 
	def symptom_mention(number):
		typ = "symptom"
		general_extractor(number, typ)
		# return "symptom/disease"
	
	def anatomy_mention(number):
		typ = "anatomy"
		general_extractor(number, typ)
		# return "anatomy"

	def procedure_mention(number):
		typ = "procedure"
		general_extractor(number, typ)

	def disease_mention(number):
		typ = "disease/disorder"
		general_extractor(number, typ)
	 
	def find_umls_concept(argument, number):
		switcher = {
			med_ment: partial(medication_mention, number),
			sym_ment: partial(symptom_mention, number),
			ana_ment: partial(anatomy_mention, number),
			pro_ment: partial(procedure_mention, number),
			dis_ment: partial(disease_mention, number)
		}
		# Get the function from switcher dictionary
		func = switcher.get(argument, lambda: "No mention")

		# Execute the function
		# print(func())
		func()


	# parse json file
	for i in range(list_len):
		find_umls_concept(json_dict[i]["typ"], i)


	## SUMMARY

	# create summary object
	summary = Summary(medicine_list, symptom_list, anatomy_list, procedure_list, disease_list)

	summary.toJSON()
	# print quick stats
	# print("")
	# print_dict(summary.quick_stats())
	# print("")



	## VISUAL DEBUG ##

	print("")
	print("#################SUMMARY")
	print("############SUMMARY#####")
	print("#######SUMMARY##########")
	print("SUMMARY#################")

	print("")
	print("MEDICINE")
	for thing in medicine_list:
		print(">",thing.name())

	print("")
	print("SYMPTOMS")
	for thing in symptom_list:
		print(">",thing.name())

	print("")
	print("DISEASES")
	for thing in disease_list:
		print(">",thing.name())

	print("")
	print("ANATOMY")
	for thing in anatomy_list:
		print(">",thing.name())

	print("")
	print("PROCEDURES")
	for thing in procedure_list:
		print(">",thing.name())

	print("")


	# # TODO: When you have your own Client ID and secret, put down their values here:
	# clientId = "FREE_TRIAL_ACCOUNT"
	# clientSecret = "PUBLIC_SECRET"

	# # TODO: Specify the URL of your small PDF document (less than 1MB and 10 pages)
	# # To extract text from bigger PDf document, you need to use the async method.
	# url = "http://www.better-fundraising-ideas.com/support-files/the-best-snail-jokes.pdf"

	# headers = {
	#     'X-WM-CLIENT-ID': clientId, 
	#     'X-WM-CLIENT-SECRET': clientSecret
	# }

	# r = requests.get('https://api.whatsmate.net/v1/pdf/extract?url=' + url, 
	#     headers=headers)

	# print("Status code: " + str(r.status_code))
	# print("Extracted Text: \n")
	# print(str(r.content))

	# api = cloudconvert.Api('X0LnpbqjPzPCKTWJAh50nMORz0olrqfJHHJ9gYFaQRfBuwv7QaEmmUPpwftXiAuY')

	# process = api.convert({
	#     'inputformat': 'pdf',
	#     'outputformat': 'txt',
	#     'input': 'upload',
	#     'file': open('package/input.pdf', 'rb')
	# })
	# process.wait() # wait until conversion finished
	# process.download("package/output.txt") # download output file

	
if __name__ == "__main__":
	main()




	