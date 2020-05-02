# .SRT .FCPXML CONVERTER

A python script that converts between .srt files and .fcpxml files to create/extract embedded captions for Final Cut Pro.
Optional feature to convert between Simplified/Traditional Chinese (using OpenCC).

## Getting Started

You only need `srt_converter.py` and `Template.xml` (if converting to .fcpxml).

Make sure you have Python 3 installed.

For conversion between Simplified/Traditional Chinese, you would need OpenCC for Python.
You can install it using:
```
pip install opencc-python-reimplemented
```

## Usage

You can use `python srt_converter.py -h` to see all the flags supported and their usage:
```
usage: srt_converter.py [-h] -i INPUT -o OUTPUT [-c CONVERT] [-t TEMPLATE] [-fr FRAMERATE]
                        [--offset OFFSET]

Convert between .srt and .fcpxml files for subtitles creation.

optional arguments:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        name for the input file (.srt or .fcpxml)
  -o OUTPUT, --output OUTPUT
                        name for the ouput file (.srt or .fcpxml)
  -c CONVERT, --convert CONVERT
                        (optional) to use OpenCC to convert between Simplified/Traditional
                        Chinese. Please specify the OpenCC configurations (e.g., s2t, t2s)
  -t TEMPLATE, --template TEMPLATE
                        (optional) to use a user-specific template file to generate .fcpxml.
                        Default to 'Template.xml'
  -fr FRAMERATE, --framerate FRAMERATE
                        (optional) framerate should be set in the template. This argument
                        provides a sanity check. Default to 29.97fps
  --offset OFFSET       (optional) move the entire timeline forward/backward from input to
                        output. In seconds
```

Input file name '-i' and ouput file name '-o' are required. They have to be either .srt or .fcpxml files.

You can create your own fcpxml template (change framerate, set text location, format, etc.) using Final Cut Pro. 
The script will use the **first** title in the timeline as the prototype to create all title elements.

Please also make sure the framerate is correctly specified in your template (as `fcpxml>resources>format>frameDuration`)
Please set the `-fr` flag (in fps) to the correct framerate if the framerate is not 29.97fps (default)
The `-fr` flag is intended only as a sanity check. The output framerate is solely determined by the template file.

## Testing

Some tests are provided in `/FCPX_test`. You can rerun the tests following the following steps:

1) Export the `test1` project of the library `srt_converter_test` into `xml_output.fcpxml` in Final Cut Pro

2) Convert `xml_output.fcpxml` to `xml2srt.srt` using (assume you are in the directory):
```
python ../srt_converter.py -i "xml_output.fcpxml" -o "xml2srt.srt"
```

3) Then you can convert back `xml2srt.srt` to `xml2srt2xml.fcpxml` based on `xml_output.fcpxml` as the template using:
```
python ../srt_converter.py -i "xml2srt.srt" -o "xml2srt2xml.fcpxml" -t "xml_output.fcpxml" -fr 23.98
```

4) If you import `xml2srt2xml.fcpxml` back into Final Cut Pro - you should be able to get a project file that is exactly identical to what we started with. 

## Template

Theoratically, any .xml or .fcpxml file can be a template. However, I would recommend keeping the template simple so that the output .fcpxml file would not contain any unnecessary information. 

Please also make sure the template `<spine>` has at least one `<title>` tag that the script can use to create other titles.

