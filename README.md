# EUCovidCertificateReader
Unofficial app which shows data inside the european heatlh certificate.

# Important Warning

**Do not use this application on certificates without the consent of their owners. It is illegal! Only use it on your own certificate. I will not be responsible for the misuse of this program.**

# Dependancies

- base45
- cbor2
- cose

To install it: `$ pip install base45 cbor2 cose`

# Usage

First, scan the QR Code with your favorite reader on your smartphone. Then, copy the result string (beginning with 'HC1:'), and put it in the program standard input. For example, you can use the following command:

`$ echo 'HC1:....' | ./EU_certificate_reader.py`

Or, with an input file:

`$ ./EU_certificate_reader.py < my_file.txt`
