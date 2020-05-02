"""
SRT & FCPXML CONVERTER
REQUIREMENT: OpenCC (pip install opencc-python-reimplemented)
AUTHOR: MICHAEL HONG
"""

import xml.etree.ElementTree as ET
import re
import copy
import argparse

parser = argparse.ArgumentParser(description="Convert between .srt and .fcpxml files for subtitles creation.")
parser.add_argument('-i', '--input', required=True, help="name for the input file (.srt or .fcpxml)")
parser.add_argument('-o', '--output', required=True, help="name for the ouput file (.srt or .fcpxml)")
parser.add_argument('-c', '--convert', 
	help="(optional) to use OpenCC to convert between Simplified/Traditional Chinese. Please specify the OpenCC configurations (e.g., s2t, t2s)")
parser.add_argument('-t', '--template', default='Template.xml',
	help="(optional) to use a user-specific template file to generate .fcpxml. Default to 'Template.xml'")
parser.add_argument('-fr', '--framerate', default=29.97, type=float,
	help='(optional) framerate should be set in the template. This argument provides a sanity check. Default to 29.97fps')
parser.add_argument('--offset', type=float,
	help='(optional) move the entire timeline forward/backward from input to output. In seconds')
args = parser.parse_args()

FILE_IN		 = args.input 
FILE_OUT 	 = args.output
XML_TEMPLATE = args.template

cc = None
if args.convert:
	from opencc import OpenCC
	cc = OpenCC(args.convert)

framerate_tuple = (1001, 30000) # default to 29.97fps

## TIME STAMP CONVERSION METHODS

def convert_xml_t(s, return_tuple=False):
	if '/' not in s:	# whole seconds
		return float(s[:-1])
	components = s.split('/')
	x = float(components[0])
	y = float(components[1][:-1])
	if return_tuple: ## convert to int
		return (int(components[0]), int(components[1][:-1]))
	return (x / y)

def convert_t_xml(t):
	multiplier, denominator = framerate_tuple
	x = int(int(int(t * denominator) / multiplier)) * multiplier
	if x % denominator == 0:
		return '%ds' % (x / denominator) ## whole number
	return f'{x}/{denominator}s'

def convert_t_srt(t):
	t_int = int(t)
	ms = int((t - t_int) * 1000)
	s = t_int % 60
	m = int(t_int / 60) % 60
	h = int(t_int / 3600)
	return f'{h:02}:{m:02}:{s:02},{ms:03}'

def convert_srt_t(arr):
	return float(arr[0]) * 3600. + float(arr[1]) * 60. + \
		float(arr[2]) + float(arr[3]) / 1000.

def convert_text(__str):
	if cc:
		return cc.convert(__str)
	return __str

################
# INPUT CONVERSTION METHODS

def process_input_srt():
	f = open(FILE_IN, 'r', encoding='utf-8-sig')
	lines = f.read().splitlines()
	total_rows = len(lines)

	i = 0
	data = []

	while i < total_rows:
		i += 1
		m = re.match('(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)', lines[i])
		t_start  = convert_srt_t(m.groups()[0:4])
		t_end    = convert_srt_t(m.groups()[4:8])
		data.append((t_start, t_end, lines[i + 1]))

		i += 3

	return data

def process_input_fcpxml():
	xml = ET.parse(FILE_IN)
	root = xml.getroot()
	n_library = root[1]
	n_event = n_library[0]
	n_project = n_event[0]
	n_sequence = n_project[0]
	n_spine = n_sequence[0]

	data = []
	for node in n_spine:
		if node.tag == 'title':

			n_text = node.find('text')[0].text
			if n_text == 'Title':
				continue # remove bad frames

			offset = convert_xml_t(node.get('offset')) 
			duration = convert_xml_t(node.get('duration'))
			end = offset + duration
			data.append((offset, end, n_text))

	return data

def process_output_srt(data):
	f = open(FILE_OUT, 'w')

	counter = 1
	for line in data:
		t_start, t_end, text = line
		f.write (f'{counter}\n')
		f.write (convert_t_srt(t_start) + ' --> ' + convert_t_srt(t_end) + '\n')
		f.write (convert_text(text) + '\n')
		f.write ('\n')
		counter += 1

	f.close()


def process_output_fcpxml(data):
	xml = ET.parse(XML_TEMPLATE)
	root = xml.getroot()

	# check if template frameDuration is consistent with specified frame rate
	n_resources = root[0]

	xml_framerate = n_resources.find('format').get('frameDuration')
	xml_framerate_fps = 1 / convert_xml_t(xml_framerate)
	if abs(args.framerate - xml_framerate_fps) > 0.005:
		raise Exception('template framerate %.2ffps is inconsistent with specified framerate %.2ffps.\
		 Please set the correct framerate using flag -fr.' % (xml_framerate_fps, args.framerate))

	global framerate_tuple
	framerate_tuple = convert_xml_t(xml_framerate, return_tuple=True)

	n_library = root[1]
	n_event = n_library[0]
	n_event.set('name', 'CC_XML')
	n_project = n_event[0]
	n_project.set('name', event_name)

	n_sequence = n_project[0]
	n_spine = n_sequence[0]

	title_proto = n_spine.find('title') ## find the first title as template
	n_spine.append(ET.Element('divider')) ## add a divider between template and content

	counter = 1	
	for line in data:
		t_start, t_end, text = line

		# insert gap if not starting from 0s
		if counter == 1 and t_start > 0:
			gap_new = ET.Element('gap')
			gap_new.set('name', 'Gap')
			gap_new.set('offset', '0s')
			gap_new.set('duration', convert_t_xml(t_start))
			gap_new.set('start', '0s')
			n_spine.append(gap_new)

		title_new = copy.deepcopy(title_proto)

		offset   = convert_t_xml(t_start)
		duration = convert_t_xml(t_end - t_start)
		output_text = convert_text(text) # apply conversion


		title_new.set('name', '{%d} %s' % (counter, output_text))
		title_new.set('offset', offset)
		title_new.set('duration', duration)
		title_new.set('start', offset)

		title_new.find('text')[0].text = output_text
		title_new.find('text')[0].set('ref', 'ts%d' % (counter))
		title_new.find('text-style-def').set('id', 'ts%d' % (counter))

		n_spine.append(title_new)

		counter += 1
	
	while n_spine[0].tag != 'divider':
		n_spine.remove(n_spine[0])
	n_spine.remove(n_spine[0]) # remove divider

	f = open(FILE_OUT, 'w')
	f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	f.write('<!DOCTYPE fcpxml>\n')
	f.write('\n')
	f.write(ET.tostring(root, encoding='UTF-8', xml_declaration=False).decode('utf-8'))
	f.close()


################

event_name = ''

## convert input file to internal representation
if FILE_IN.endswith('.srt'):
	data = process_input_srt()
	event_name = FILE_IN[:-4]
elif FILE_IN.endswith('.fcpxml'):
	data = process_input_fcpxml()
	event_name = FILE_IN[:-7]
else:
	raise Exception('unsupported input file type: ' + FILE_IN)

## apply global offset (if applicable)
if args.offset:
	data = list(map(lambda x: (x[0] + args.offset, x[1] + args.offset, x[2]), data))

## convert internal representation to output
if FILE_OUT.endswith('.srt'):
	process_output_srt(data)
elif FILE_OUT.endswith('.fcpxml'):
	process_output_fcpxml(data)
else:
	raise Exception('unsupported output file type: ' + FILE_OUT)

