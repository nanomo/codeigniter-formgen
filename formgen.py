#!/usr/bin/env python

import re, sys, math
from time import localtime, strftime
from settings import *

tablename = ''
controllername = ''
modelname = ''
field = {}
generation_time = strftime("%Y-%m-%d %H:%M:%S %Z", localtime())

# Special fields are set in SQL statements so are skipped for function arguments and form fields. Remove field names from here to expose throughout.
special_fields = ['created','id','modified','deleted'] 

filename = 'sql.txt'
if len(sys.argv) == 2:
	if sys.argv[1] == '-h' or sys.argv[1] == '--help':
		print "Usage: formgen.py <filename>"
		print "  Default SQL file is sql.txt"
		exit()
	filename = sys.argv[1]

with open(filename) as f:
	content = f.readlines()

fieldcount = 0
for line in content:
        x = re.search(r"CREATE TABLE `(\w+)`.*#\s+(.*)$",line)
        if x:  
                tablename = x.group(1)
		nicetablename = x.group(2)
		print tablename + " : " + nicetablename
		controllername = tablename.capitalize()
		modelname = controllername + 's'

        f = re.search(r"^\s+`(\w+)` ([0-9a-zA-Z\(\)]+).*#\s+(.*)$",line)
        if f:  
		field[fieldcount] = {}
                field[fieldcount]['name'] = f.group(1)
		field[fieldcount]['type'] = f.group(2)
		field[fieldcount]['label'] = f.group(3)
		if f.group(1) in special_fields :
			special = " ***"
		else :
			special = ''
		print str(field[fieldcount]) + special
		fieldcount = fieldcount + 1


#print ""
#print "tablename: " + tablename
#print "controllername: " + controllername
#print ""
#print "field: " + str(field)

### create blocks for replacement 

# arguments for new/edit model functions - <fg_new_arguments>
fg_new_arguments = ''
rendered_field_count = 0
for f in field:
	if field[f]['name'] not in special_fields :#!= 'id' and field[f]['name'] != 'created' and field[f]['name'] != 'deleted' and field[f]['name'] != 'modified':
		fg_new_arguments = fg_new_arguments + "$"+field[f]['name']
		rendered_field_count = rendered_field_count + 1
		if rendered_field_count < len(field) - len(special_fields):
			fg_new_arguments = fg_new_arguments + ', /* '+str(rendered_field_count)+ ' */'
		if rendered_field_count % 6 == 5:
			fg_new_arguments = fg_new_arguments + "\n\t\t\t\t" 

# get statements for model functions - <fg_form_fields>
fg_form_fields = ''
for f in field:
	fg_form_fields = fg_form_fields + "\t\t\t$a['"+field[f]['name']+"'] = $row->"+field[f]['name']+";\n"

# set statements for model  <fg_new_field_sets>
fg_new_field_sets = ''
for f in field:
	if field[f]['name'] not in special_fields :
		fg_new_field_sets = fg_new_field_sets + "\t\t$this->db->set('"+field[f]['name']+"', $"+field[f]['name']+");\n"

# controller form validation rules - <fg_form_validation_rules>
fg_form_validation_rules = ''
for f in field:
	if field[f]['name'] not in special_fields :
		fg_form_validation_rules = fg_form_validation_rules + "\t\t\t$this->form_validation->set_rules('"+field[f]['name']+"', '"+field[f]['label']+"', 'trim|xss_clean');\n"

# controller form validation values - <fg_form_validation_values>
fg_form_validation_values = ''
rendered_field_count = 0
for f in field:
	if field[f]['name'] not in special_fields :
		fg_form_validation_values = fg_form_validation_values + "\t\t\t\t\t\t$this->form_validation->set_value('"+field[f]['name']+"')"
		rendered_field_count = rendered_field_count + 1
		if rendered_field_count < len(field) - len(special_fields):
			fg_form_validation_values = fg_form_validation_values + ', /* '+str(f)+ ' */\n'

# view edit field definitions
fg_field_definitions = ''
for f in field:
	if field[f]['name'] not in special_fields :
		fg_field_definitions = fg_field_definitions + "$"+field[f]['name']+""" = array(
\t'name'	=> '"""+field[f]['name']+"""',
\t'id'	=> '"""+field[f]['name']+"""',
\t'size'	=> 20,
\t'value' => isset($a['""" +field[f]['name']+"'])?$a['"+field[f]['name']+"""']:''
);\n"""

# view edit fields
fg_fields = ''
for f in field:
	if field[f]['name'] not in special_fields :
		if field[f]['type'] == 'text':
			fg_fields = fg_fields + """\t<tr>
		<td valign="top"><div class="form-label"><?php echo form_label('"""+field[f]['label']+"', $"+field[f]['name']+"""['id']); ?></div><div class="form-sublabel"><!-- sublabel goes here --></div></td>
		<td><textarea name=\""""+field[f]['name']+"""\" rows="8" class="input-xxlarge"><?php echo $"""+field[f]['name']+"""['value'] ?></textarea></td>
		<td style="color: red;"><?php echo form_error($"""+field[f]['name']+"""['name']); ?><?php echo isset($errors[$"""+field[f]['name']+"""['name']])?$errors[$"""+field[f]['name']+"""['name']]:''; ?></td>
	</tr>\n"""
		else:
			fg_fields = fg_fields + """\t<tr>
		<td width="150"><?php echo form_label('"""+field[f]['label']+"', $"+field[f]['name']+"""['id']); ?></td>
		<td><?php echo form_input($"""+field[f]['name']+"""); ?></td>
		<td style="color: red;"><?php echo form_error($"""+field[f]['name']+"['name']); ?><?php echo isset($errors[$"+field[f]['name']+"['name']])?$errors[$"+field[f]['name']+"""['name']]:''; ?></td>
	</tr>\n"""

# view list fields
fg_table_headings = ''
headingcount = 0
commentout = ''
commentout2 = ''
for f in field:
	if( headingcount > 6 ) :
		commentout = '<!--'
		commentout2 = '-->'
	fg_table_headings = fg_table_headings + commentout + "<td class=\"heading\">"+field[f]['label']+"</td>\n" + commentout2
	headingcount = headingcount + 1

fg_table_data = ''
fieldcount = 0
commentout = ''
for f in field:
	if( fieldcount > 6 ) :
		commentout = '#'
	fg_table_data = fg_table_data + commentout + "$thetable .= '<td>'.$row['"+field[f]['name']+"'].'</td>';\n"
	fieldcount = fieldcount + 1


### generate the files

# open model and do find replace
with open('templates/t_model.txt') as f:
	content = f.readlines()

mf = open(OUTPUT_FOLDER+"/models/"+tablename+'s.php','w')
for line in content: 
	line = re.sub('<fg_time>',generation_time,line)
	line = re.sub('<fg_nice_name>',nicetablename,line)
	line = re.sub('<fg_model_name>',modelname,line)
	line = re.sub('<fg_table_name>',tablename,line)
	line = re.sub('<fg_new_arguments>',fg_new_arguments,line)
        tabs = re.search(r"^\t\t+<",line)
        if tabs:  
		line = line.lstrip()
		line = re.sub('<fg_form_fields>',fg_form_fields,line)
		line = re.sub('<fg_new_field_sets>',fg_new_field_sets,line)
	#line = line.rstrip()
	mf.write(line)
mf.close()

# open controller and do find replace
with open('templates/t_controller.txt') as f:
	content = f.readlines()

cf = open(OUTPUT_FOLDER+"/controllers/"+tablename+'.php','w')
for line in content: 
	line = re.sub('<fg_time>',generation_time,line)
	line = re.sub('<fg_nice_name>',nicetablename,line)
	line = re.sub('<fg_controller_name>',controllername,line)
	line = re.sub('<fg_model_name>',modelname,line)
	line = re.sub('<fg_table_name>',tablename,line)
	line = re.sub('<fg_new_arguments>',fg_new_arguments,line)
        tabs = re.search(r"^\t\t+<",line)
        if tabs:  
		line = line.lstrip()
		line = re.sub('<fg_form_validation_rules>',fg_form_validation_rules,line)
		line = re.sub('<fg_form_validation_values>',fg_form_validation_values,line)
	#line = line.rstrip()
	cf.write(line)
cf.close()

# open edit view and do find replace
with open('templates/t_view_edit.txt') as f:
	content = f.readlines()

vf = open(OUTPUT_FOLDER+"/views/edit_"+tablename+'.php','w')
for line in content: 
	line = re.sub('%fg_time%',generation_time,line)
	line = re.sub('%fg_nice_name%',nicetablename,line)
	line = re.sub('%fg_controller_name%',controllername,line)
	line = re.sub('%fg_table_name%',tablename,line)
	line = re.sub('%fg_field_definitions\%',fg_field_definitions,line)
        tabs = re.search(r"^\t+%",line)
        if tabs:  
		line = line.lstrip()
		line = re.sub('%fg_fields%',fg_fields,line)
	#line = line.rstrip()
	vf.write(line)
vf.close()

# open list view and do find replace
with open('templates/t_view_list.txt') as f:
	content = f.readlines()

vf = open(OUTPUT_FOLDER+"/views/list_"+tablename+'.php','w')
for line in content: 
	line = re.sub('%fg_time%',generation_time,line)
	line = re.sub('%fg_nice_name%',nicetablename,line)
	line = re.sub('%fg_controller_name%',controllername,line)
	line = re.sub('%fg_model_name%',modelname,line)
	line = re.sub('%fg_table_name%',tablename,line)
	line = re.sub('%fg_field_definitions\%',fg_field_definitions,line)
	line = re.sub('%fg_table_headings%',fg_table_headings,line)
	line = re.sub('%fg_table_data%',fg_table_data,line)
	vf.write(line)
vf.close()
