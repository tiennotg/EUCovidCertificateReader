#!/usr/bin/python3

'''
  Copyright 2021 Guilhem Tiennot
  
  Python script that decodes data from European Health Certificate.
  It reads standard input, and try to decode each line.
  
  Usage: Read your health certificate with your smartphone and a QR-Code
	Reader, then copy the data and put in into the program via stdin.
  
  Dependencies: base45, zlib, cbor2, cose
  
  EU_certificate_reader is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
  
  EU_certificate_reader is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License
  along with EU_certificate_reader.  If not, see <https://www.gnu.org/licenses/>.
'''

from base45 import b45decode
from base64 import b64encode
from zlib import decompress
from cbor2 import loads as cbor2_load
from cose.messages import CoseMessage
from cose.headers import KID
from datetime import datetime
from sys import stdin
import locale


#################### DATA ####################
##############################################

PREFIX="HC1:"
ENCODING="utf-8"

ISSUER_INDEX = 1
ISSUING_DATE_INDEX = 6
EXPIRING_DATE_INDEX = 4
CERTIFICATE_LIST_INDEX = -260
KID_INDEX = 'kid'

VERSION_KEY = "ver"
NAME_KEY = "nam"
FIRSTNAME_KEY = "gn"
LASTNAME_KEY = "fn"
BIRTHDATE_KEY = "dob"

RECOVERY_CERT_KEY = "r"
TEST_CERT_KEY = "t"
VACCINE_CERT_KEY = "v"

DISEASE_LIST = {"840539006": "COVID-19"}
VACCINE_LIST = {"1119305005": "antigénique","1119349007": "ARNm","J07BX03": "ARNm"}
PRODUCT_NAME_LIST = {"EU/1/20/1528": "Comirnaty", "EU/1/20/1507": "Moderna", "EU/1/21/1529": "Vaxzevria",
	"EU/1/20/1525": "Janssen"}
PROVIDER_LIST = {"ORG-100001699": "AstraZeneca AB", "ORG-100030215": "Biontech Manufacturing GmbH",
	"ORG-100001417": "Janssen-Cilag International", "ORG-100031184": "Moderna Biotech Spain S.L.",
	"ORG-100006270": "Curevac AG", "ORG-100013793": "CanSino Biologics",
	"ORG-100020693": "China Sinopharm International Corp. (Pékin)",
	"ORG-100010771": "Sinopharm Weiqida Europe Pharmaceutical s.r.o. (Prague)",
	"ORG-100024420": "Sinopharm Zhijun (Shenzhen) Pharmaceutical Co. Ltd.",
	"ORG-100032020": "Novavax CZ AS"}
COUNTRY_LIST = {"AD": "Andorre", "AE": "Émirats arabes unis", "AF" : "Afghanistan",
	"AG": "Antigua-et-Barbuda", "AI": "Anguilla", "AL": "Albanie", "AM": "Arménie",
	"AO": "Angola", "AQ": "Antarctique", "AR": "Argentine", "AS": "Samoa américaines",
	"AT": "Autriche", "AU": "Australie", "AW": "Aruba", "AX": "Îles Åland",
	"AZ": "Azerbaïdjan", "BA": "Bosnie-Herzégovine", "BB": "Barbade",
	"BD": "Bangladesh", "BE": "Belgique", "BF": "Burkina Faso", "BG": "Bulgarie",
	"BH": "Bahreïn", "BI": "Burundi", "BJ": "Bénin", "BL": "Saint Barthélemy",
	"BM": "Bermudes", "BN": "Brunéi Darussalam", "BO": "Bolivie",
	"BQ": "Bonaire, Saint Eustache et Saba", "BR": "Brésil", "BS": "Bahamas",
	"BT": "Bhoutan", "BV": "Île Bouve", "BW": "Botswana", "BY": "Biélorussie",
	"BZ": "Belize", "CA": "Canada", "CC": "Îles Cocos",
	"CD": "République démocratique du Congo", "CF": "République centrafricaine",
	"CG": "Congo", "CH": "Suisse", "CI": "Côte d'Ivoire", "CK": "Îles Cook",
	"CL": "Chili", "CM": "Cameroun", "CN": "Chine", "CO": "Colombie",
	"CR": "Costa Rica", "CU": "Cuba", "CV": "Cabo Verde", "CW": "Curaçao",
	"CX": "Île Christmas", "CY": "Chypre", "CZ": "République tchèque", "DE": "Allemagne",
	"DJ": "Djibouti", "DK": "Danemark", "DM": "Dominique", "DO": "République dominicaine",
	"DZ": "Algérie", "EC": "Équateur", "EE": "Estonie", "EG": "Égypte",
	"EH": "Sahara occidental", "ER": "Érythrée", "ES": "Espagne", "ET": "Éthiopie",
	"FI": "Finlande", "FJ": "Fidji", "FK": "Îles Falkland (Malouines)",
	"FM": "États fédérés de Micronésie", "FO": "Îles Féroé", "FR": "France",
	"GA": "Gabon", "GB": "Royaume-uni",
	"GD": "Grenade", "GE": "Géorgie", "GF": "Guyane française", "GG": "Guernesey",
	"GH": "Ghana", "GI": "Gibraltar", "GL": "Groenland", "GM": "Gambie",
	"GN": "Guinée", "GP": "Guadeloupe", "GQ": "Guinée équatoriale", "GR": "Grèce",
	"GS": "Géorgie du sud et les îles Sandwich du sud", "GT": "Guatemala",
	"GU": "Guam", "GW": "Guinée-Bissau", "GY": "Guyana", "HK": "Hong Kong",
	"HM": "Îles Heard et îles McDonald", "HN": "Honduras", "HR": "Croatie",
	"HT": "Haïti", "HU": "Hongrie", "ID": "Indonesie", "IE": "Irlande",
	"IL": "Israël", "IM": "Île de Man", "IN": "Inde", "IO": "Territoire britannique de l'océan indien",
	"IQ": "Iraq", "IR": "Iran", "IS": "Islande", "IT": "Italie",
	"JE": "Jersey", "JM": "Jamaïque", "JO": "Jordanie", "JP": "Japon", "KE": "Kenya",
	"KG": "Kirghizistan", "KH": "Cambodge", "KI": "Kiribati", "KM": "Comores",
	"KN": "Saint-Christophe-et-Niévès", "KP": "Corée du nord",
	"KR": "Corée du sud", "KW": "Koweït", "KY": "Îles Caïmans",
	"KZ": "Kazakhstan", "LA": "Laos",
	"LB": "Liban", "LC": "Sainte-Lucie", "LI": "Liechtenstein", "LK": "Sri Lanka",
	"LR": "Libéria", "LS": "Lesotho", "LT": "Lituanie", "LU": "Luxembourg",
	"LV": "Lettonie", "LY": "Libye", "MA": "Maroc", "MC": "Monaco",
	"MD": "Moldavie", "ME": "Monténégro", "MF": "Saint Martin (partie française)",
	"MG": "Madagascar", "MH": "Îles Marshall", "MK": "Macédoine",
	"ML": "Mali", "MM": "Myanmar", "MN": "Mongolie", "MO": "Macao",
	"MP": "Îles Mariannes du nord", "MQ": "Martinique", "MR": "Mauritanie",
	"MS": "Montserrat", "MT": "Malte", "MU": "Maurice", "MV": "Maldives",
	"MW": "Malawi", "MX": "Mexique", "MY": "Malaisie", "MZ": "Mozambique",
	"NA": "Namibie", "NC": "Nouvelle-Calédonie", "NE": "Niger", "NF": "Île Norfolk",
	"NG": "Nigéria", "NI": "Nicaragua", "NL": "Pays-bas", "NO": "Norvège",
	"NP": "Népal", "NR": "Nauru", "NU": "Niue", "NZ": "Nouvelle-zélande", "OM": "Oman",
	"PA": "Panama", "PE": "Pérou", "PF": "Polynésie française", "PG": "Papouasie-Nouvelle-Guinée",
	"PH": "Philippines", "PK": "Pakistan", "PL": "Pologne", "PM": "Saint-Pierre-et-Miquelon",
	"PN": "Îles Pitcairn", "PR": "Porto Rico", "PS": "Palestine", "PT": "Portugal",
	"PW": "Palaos", "PY": "Paraguay", "QA": "Qatar", "RE": "Réunion", "RO": "Roumanie",
	"RS": "Serbie", "RU": "Russie", "RW": "Rwanda", "SA": "Arabie saoudite",
	"SB": "Îles Salomon", "SC": "Seychelles", "SD": "Soudan", "SE": "Suède",
	"SG": "Singapour", "SH": "Saint Hélène, Ascension et Tristan da Cunha",
	"SI": "Slovénie", "SJ": "Svalbard et île Jan Mayen", "SK": "Slovaquie",
	"SL": "Sierra Leone", "SM": "Saint-Marin", "SN": "Sénégal", "SO": "Somalie",
	"SR": "Suriname", "SS": "Soudan du sud", "ST": "Sao-Tomé-et-Principe",
	"SV": "Salvador", "SX": "Saint-Martin (partie néerlandaise)", "SY": "Syrie",
	"SZ": "Eswatini", "TC": "Îles turques-et-Caïques", "TD": "Tchad",
	"TF": "Terres australes et antarctiques françaises", "TG": "Togo", "TH": "Thaïlande",
	"TJ": "Tadjikistan", "TK": "Tokelau", "TL": "Timor oriental", "TM": "Turkménistan",
	"TN": "Tunisie", "TO": "Tonga", "TR": "Turquie", "TT": "Trinité-et-Tobago",
	"TV": "Tuvalu", "TW": "Taiwan", "TZ": "Tanzanie",
	"UA": "Ukraine", "UG": "Ouganda", "UM": "Îles mineures éloignées des États-Unis",
	"US": "États-Unis", "UY": "Uruguay", "UZ": "Ouzbékistan",
	"VA": "Vatican", "VC": "Saint-Vincent-et-les-Grenadines",
	"VE": "Vénézuela", "VG": "Îles vierges britanniques",
	"VI": "Îles vierges des États-Unis", "VN": "Viêt Nam", "VU": "Vanuatu",
	"WF": "Wallis-et-Futuna", "WS": "Samoa", "YE": "Yémen",
	"YT": "Mayotte", "ZA": "Afrique du sud", "ZM": "Zambie", "ZW": "Zimbabwe"}
TEST_TYPE_LIST = {"LP6464-4": "PCR", "LP217198-3": "antigénique"}
TEST_NAME_LIST = {"1833": "AAZ-LMB, COVID-VIRO", "1232": "Abbott Rapid Diagnostics, Panbio COVID-19 Ag Rapid Test",
	"1468": "ACON Laboratories, Inc, Flowflex SARS-CoV-2 Antigen rapid test",
	"1304": "AMEDA Labordiagnostik GmbH, AMP Rapid Test SARS-CoV-2 Ag",
	"1822": "Anbio (Xiamen) Biotechnology Co., Ltd, Rapid COVID-19 Antigen Test(Colloidal Gold)",
	"1815": "Anhui Deep Blue Medical Technology Co., Ltd, COVID-19 (SARS-CoV-2) Antigen Test Kit (Colloidal Gold) - Nasal Swab",
	"1736": "Anhui Deep Blue Medical Technology Co., Ltd, COVID-19 (SARS-CoV-2) Antigen Test Kit (Colloidal Gold)",
	"768": "ArcDia International Ltd, mariPOC SARS-CoV-2",
	"1654": "Asan Pharmaceutical CO., LTD, Asan Easy Test COVID-19 Ag",
	"2010": "Atlas Link Technology Co., Ltd., NOVA Test® SARS-CoV-2 Antigen Rapid Test Kit (Colloidal Gold Immunochromatography)",
	"1906": "Azure Biotech Inc, COVID-19 Antigen Rapid Test Device",
	"1870": "Beijing Hotgen Biotech Co., Ltd, Novel Coronavirus 2019-nCoV Antigen Test (Colloidal Gold)",
	"1331": "Beijing Lepu Medical Technology Co., Ltd, SARS-CoV-2 Antigen Rapid Test Kit",
	"1484": "Beijing Wantai Biological Pharmacy Enterprise Co., Ltd, Wantai SARS-CoV-2 Ag Rapid Test (FIA)",
	"1223": "BIOSYNEX S.A., BIOSYNEX COVID-19 Ag BSS",
	"1236": "BTNX Inc, Rapid Response COVID-19 Antigen Rapid Test",
	"1173": "CerTest Biotec, CerTest SARS-CoV-2 Card test",
	"1919": "Core Technology Co., Ltd, Coretests COVID-19 Ag Test",
	"1225": "DDS DIAGNOSTIC, Test Rapid Covid-19 Antigen (tampon nazofaringian)",
	"1375": "DIALAB GmbH, DIAQUICK COVID-19 Ag Cassette",
	"1244": "GenBody, Inc, Genbody COVID-19 Ag Test",
	"1253": "GenSure Biotech Inc, GenSure COVID-19 Antigen Rapid Kit (REF: P2004)",
	"1144": "Green Cross Medical Science Corp., GENEDIA W COVID-19 Ag",
	"1747": "Guangdong Hecin Scientific, Inc., 2019-nCoV Antigen Test Kit (colloidal gold method)",
	"1360": "Guangdong Wesail Biotech Co., Ltd, COVID-19 Ag Test Kit",
	"1437": "Guangzhou Wondfo Biotech Co., Ltd, Wondfo 2019-nCoV Antigen Test (Lateral Flow Method)",
	"1256": "Hangzhou AllTest Biotech Co., Ltd, COVID-19 and Influenza A+B Antigen Combo Rapid Test",
	"1363": "Hangzhou Clongene Biotech Co., Ltd, Covid-19 Antigen Rapid Test Kit",
	"1365": "Hangzhou Clongene Biotech Co., Ltd, COVID-19/Influenza A+B Antigen Combo Rapid Test",
	"1844": "Hangzhou Immuno Biotech Co.,Ltd, Immunobio SARS-CoV-2 Antigen ANTERIOR NASAL Rapid Test Kit (minimal invasive)",
	"1215": "Hangzhou Laihe Biotech Co., Ltd, LYHER Novel Coronavirus (COVID-19) Antigen Test Kit(Colloidal Gold)",
	"1392": "Hangzhou Testsea Biotechnology Co., Ltd, COVID-19 Antigen Test Cassette",
	"1767": "Healgen Scientific, Coronavirus Ag Rapid Test Cassette",
	"1263": "Humasis, Humasis COVID-19 Ag Test",
	"1333": "Joinstar Biomedical Technology Co., Ltd, COVID-19 Rapid Antigen Test (Colloidal Gold)",
	"1764": "JOYSBIO (Tianjin) Biotechnology Co., Ltd, SARS-CoV-2 Antigen Rapid Test Kit (Colloidal Gold)",
	"1266": "Labnovation Technologies Inc, SARS-CoV-2 Antigen Rapid Test Kit",
	"1267": "LumiQuick Diagnostics Inc, QuickProfile COVID-19 Antigen Test",
	"1268": "LumiraDX, LumiraDx SARS-CoV-2 Ag Test",
	"1180": "MEDsan GmbH, MEDsan SARS-CoV-2 Antigen Rapid Test",
	"1190": "möLab, COVID-19 Rapid Antigen Test",
	"1481": "MP Biomedicals, Rapid SARS-CoV-2 Antigen Test Card",
	"1162": "Nal von minden GmbH, NADAL COVID-19 Ag Test",
	"1420": "NanoEntek, FREND COVID-19 Ag",
	"1199": "Oncosem Onkolojik Sistemler San. ve Tic. A.S., CAT",
	"308": "PCL Inc, PCL COVID19 Ag Rapid FIA",
	"1271": "Precision Biosensor, Inc, Exdia COVID-19 Ag",
	"1341": "Qingdao Hightop Biotech Co., Ltd, SARS-CoV-2 Antigen Rapid Test (Immunochromatography)",
	"1097": "Quidel Corporation, Sofia SARS Antigen FIA",
	"1606": "RapiGEN Inc, BIOCREDIT COVID-19 Ag - SARS-CoV 2 Antigen test",
	"1604": "Roche (SD BIOSENSOR), SARS-CoV-2 Antigen Rapid Test",
	"1489": "Safecare Biotech (Hangzhou) Co. Ltd, COVID-19 Antigen Rapid Test Kit (Swab)",
	"1490": "Safecare Biotech (Hangzhou) Co. Ltd, Multi-Respiratory Virus Antigen Test Kit(Swab)  (Influenza A+B/ COVID-19)",
	"344": "SD BIOSENSOR Inc, STANDARD F COVID-19 Ag FIA",
	"345": "SD BIOSENSOR Inc, STANDARD Q COVID-19 Ag Test",
	"1319": "SGA Medikal, V-Chek SARS-CoV-2 Ag Rapid Test Kit (Colloidal Gold)",
	"2017": "Shenzhen Ultra-Diagnostics Biotec.Co.,Ltd, SARS-CoV-2 Antigen Test Kit",
	"1769": "Shenzhen Watmind Medical Co., Ltd, SARS-CoV-2 Ag Diagnostic Test Kit (Colloidal Gold)",
	"1574": "Shenzhen Zhenrui Biotechnology Co., Ltd, Zhenrui ®COVID-19 Antigen Test Cassette",
	"1218": "Siemens Healthineers, CLINITEST Rapid Covid-19 Antigen Test",
	"1114": "Sugentech, Inc, SGTi-flex COVID-19 Ag",
	"1466": "TODA PHARMA, TODA CORONADIAG Ag",
	"1934": "Tody Laboratories Int., Coronavirus (SARS-CoV 2) Antigen - Oral Fluid",
	"1443": "Vitrosens Biotechnology Co., Ltd, RapidFor SARS-CoV-2 Rapid Ag Test",
	"1246": "VivaChek Biotech (Hangzhou) Co., Ltd, Vivadiag SARS CoV 2 Ag Rapid Test",
	"1763": "Xiamen AmonMed Biotechnology Co., Ltd, COVID-19 Antigen Rapid Test Kit (Colloidal Gold)",
	"1278": "Xiamen Boson Biotech Co. Ltd, Rapid SARS-CoV-2 Antigen Test Card",
	"1456": "Xiamen Wiz Biotech Co., Ltd, SARS-CoV-2 Antigen Rapid Test",
	"1884": "Xiamen Wiz Biotech Co., Ltd, SARS-CoV-2 Antigen Rapid Test (Colloidal Gold)",
	"1296": "Zhejiang Anji Saianfu Biotech Co., Ltd, AndLucky COVID-19 Antigen Rapid Test",
	"1295": "Zhejiang Anji Saianfu Biotech Co., Ltd, reOpenTest COVID-19 Antigen Rapid Test",
	"1343": "Zhezhiang Orient Gene Biotech Co., Ltd, Coronavirus Ag Rapid Test Cassette (Swab)"}


CERT_FIELDS = {"v": {"tg": ["Maladie ciblée :", DISEASE_LIST],
	"vp": ["Type de vaccin :", VACCINE_LIST],
	"mp": ["Nom du produit :", PRODUCT_NAME_LIST],
	"ma": ["Fabricant :", PROVIDER_LIST],
	"dn": ["Nombre de doses injectées :",{}],"sd": ["Nombre total de doses requises :",{}],
	"dt": ["Date de la dernière injection :",{}], "co": ["Pays :", COUNTRY_LIST],
	"is": ["Autorité de délivrance :", {}],
	"ci": ["Identifiant du certificat :", {}]},
	"t": {"tg": ["Maladie ciblée :", DISEASE_LIST],
	"tt": ["Type de test :", TEST_TYPE_LIST],
	"nm": ["Nom du test :", TEST_NAME_LIST],
	"ma": ["", {}],"sc": ["Date du test :", {}],
	"tr": ["Résultat du test :", {"260415000": "négatif", "260373001": "positif"}],
	"tc": ["Centre de test :", {}], "co": ["Pays :", COUNTRY_LIST],
	"is": ["Autorité de délivrance :", {}],"ci": ["Identifiant du certificat :", {}]},
	"r": {"tg": ["Maladie ciblée :",DISEASE_LIST],
	"fr": ["Date du premier test positif :", {}],
	"co": ["Pays :", COUNTRY_LIST],
	"is": ["Autorité de délivrance :", {}],
	"df": ["Date de début de validité :", {}],
	"du": ["Date de fin de validité :", {}],"ci": ["Identifiant du certificat :", {}]}}


################# END OF DATA ################
##############################################

#
# European Health Cerfificate format:
# 	- Data is packed into a CBOR struct
#	- CBOR struct is included (and signed) into a COSE struct
#	- The COSE struct is compress with zlib algorithm
#	- The compressed COSE struct is base45-encoded
#	- Last, a QR-Code is generated with the base45 message
#


# Checks the version of the Health Certificate. If it's OK, then return
# the decoded data in a COSE object.
#
# Process: encoded data -> decode base45 -> decompress from zlib -> decode COSE struct -> COSE object

def GetCOSEstruct(inputstr):
	if not inputstr[0:len(PREFIX)] == PREFIX:
		raise ValueError("Format de passeport non supporté.")
	return CoseMessage.decode(decompress(b45decode(inputstr[len(PREFIX):])))

# Extracts data from the CBOR struct, contained into COSE object.
# Add public key identifier to the dictionnary.

def GetData(COSEstruct):
	d = cbor2_load(COSEstruct.payload)
	d['kid'] = b64encode(COSEstruct.get_attr(KID)).decode(ENCODING)
	return d

# Converts the python dictionnary into human readable text

def DataToText(datahash):
	fields = [["Émetteur du document :", datahash[ISSUER_INDEX]]]
	
	for f in (("Date d’émission :", datahash[ISSUING_DATE_INDEX]), ("Date de fin de validité :", datahash[EXPIRING_DATE_INDEX])):
		d = datetime.fromtimestamp(f[1])
		fields += [[f[0], d.strftime("%A %d %B %Y à %Hh%M")]]
	
	fields += [["ID de la clé de signature :",datahash[KID_INDEX]]]
	
	fields += [["",""],["##########","Certificat(s) ##########"],["",""]]
	
	for i in datahash[CERTIFICATE_LIST_INDEX]:
		fields += [["Version :", datahash[CERTIFICATE_LIST_INDEX][i][VERSION_KEY]],
			["Nom :", datahash[CERTIFICATE_LIST_INDEX][i][NAME_KEY][LASTNAME_KEY]],
			["Prénom :", datahash[CERTIFICATE_LIST_INDEX][i][NAME_KEY][FIRSTNAME_KEY]],
			["Date de naissance :", datahash[CERTIFICATE_LIST_INDEX][i][BIRTHDATE_KEY]]]
		
		if RECOVERY_CERT_KEY in datahash[CERTIFICATE_LIST_INDEX][i].keys():
			fields += [["Type de certificat :","Rétablissement"]]
			key = RECOVERY_CERT_KEY
		elif TEST_CERT_KEY in datahash[CERTIFICATE_LIST_INDEX][i].keys():
			fields += [["Type de certificat :","Test"]]
			key = TEST_CERT_KEY
		elif VACCINE_CERT_KEY in datahash[CERTIFICATE_LIST_INDEX][i].keys():
			fields += [["Type de certificat :","Vaccination"]]
			key = VACCINE_CERT_KEY
		
		for f in datahash[CERTIFICATE_LIST_INDEX][i][key][0]:
			if len(CERT_FIELDS[key][f][1].keys()) == 0:
				fields += [[CERT_FIELDS[key][f][0], str(datahash[CERTIFICATE_LIST_INDEX][i][key][0][f])]]
			else:
				fields += [[CERT_FIELDS[key][f][0], CERT_FIELDS[key][f][1][str(datahash[CERTIFICATE_LIST_INDEX][i][key][0][f])]]]
		
	fields += [["",""],["##########",""],["",""]]
	
	s = ""
	for f in fields:
		f_str = " ".join(f)
		s = "\n".join((s,f_str))
	
	return s

# The program reads standard input, and for each line, attempts to decode data

locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
for line in stdin:
	d = GetCOSEstruct(line.strip('\n'))
	print(DataToText(GetData(d)))
