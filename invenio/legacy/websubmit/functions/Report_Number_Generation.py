# This file is part of Invenio.
# Copyright (C) 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
"""Description:   function Report_Number_Generation
                   This function creates a reference for the submitted
                  document and saves it in the specified file.
    Author:         T.Baron"""
__revision__ = "$Id$"

import os
import re
import time
import fcntl
import errno

from invenio.config import CFG_WEBSUBMIT_COUNTERSDIR
from invenio.legacy.websubmit.config import InvenioWebSubmitFunctionError
from invenio.utils.shell import mymkdir

def Report_Number_Generation(parameters, curdir, form, user_info=None):
    """
    This function creates a reference for the submitted
    document and saves it in the specified 'edsrn' file.

    After generating the reference, also sets the global variable 'rn'
    containing this reference.

    Parameters:

      * edsrn: name of the file in which the reference is saved

      * autorngen: one of "A", "N", "Y"
                   "A": The reference is the submission number
                   "N": The reference is taken from a file [edsrn]
                   "Y": The reference is generated

      * rnin: name of the file containing the category

      * counterpath: path to the counter file note you can use:
                     <PA>yy</PA> to include year
                     <PA>categ</PA> to include category of the
                        submission
                     <PA>file[re]:name_of_file[regular expression to match]</PA> first line of file
                        generated by submission, matching [re]
                     <PA>file*[re]:name_of_file [regular expression to match]</PA> all the lines of
                        a file genereated during submission, matching [re]
                        separated by - (dash) char .

      * rnformat: format for the generated reference. You can use:
                     <PA>yy</PA> to include year
                     <PA>categ</PA> to include category of the
                        submission
                    <PA>file[re]:name_of_file[regular expression to match]</PA> first line of file
                        generated by submission, matching [re]
                    <PA>file*[re]:name_of_file [regular expression to match]</PA> all the lines of
                        a file genereated during submission, matching [re]
                        separated by - (dash) char .

      * yeargen: if "AUTO", current year, else the year is
                 extracted from the file [yeargen]

                 * nblength: the number of digits for the report
                  number. Eg: '3' for XXX-YYYY-025 or '4'
                  for XXX-YYYY-0025. If more are needed
                  (all available digits have been used),
                  the length is automatically
                  extended. Choose 1 to never have leading
                  zeros. Default length: 3.

      * initialvalue: Initial value for the counter, 0 by default
    """
    global doctype, access, act, dir, rn
    # The program must automatically generate the report number

    # What is the length of the generated report number?
    nb_length = 3
    if 'nblength' in parameters and parameters['nblength'].isdigit():
        nb_length = int(parameters['nblength'])

    # Generate Year
    if parameters['autorngen'] == "Y":
        if parameters['yeargen'] == "AUTO":
            # Current year is used
            yy = time.strftime("%Y")
        else :
            # If yeargen != auto then the contents of the file named 'yeargen' is used
            # Assumes file uses DD-MM-YYYY format
            fp = open("%s/%s" % (curdir, parameters['yeargen']), "r")
            mydate = fp.read()
            fp.close()
            yy = re.sub("^......", "", mydate)
        # Evaluate category - Category is read from the file named 'rnin
        if os.path.isfile("%s/%s" % (curdir,parameters['rnin'])):
            fp = open("%s/%s" % (curdir,parameters['rnin']), "r")
            category = fp.read()
            category =  category.replace("\n", "")
        else:
            category = ""

        def get_pa_tag_content(pa_content):
            """Get content for <PA>XXX</PA>.
            @param pa_content: MatchObject for <PA>(.*)</PA>.
            return: if pa_content=yy => 4 digits year
                    if pa_content=categ =>category
                    if pa_content=file[re]:a_file => first line of file a_file matching re
                    if pa_content=file*p[re]:a_file => all lines of file a_file, matching re,
                                                  separated by - (dash) char.
            """
            pa_content=pa_content.groupdict()['content']
            sep = '-'
            out = ''
            if pa_content=='yy':
                out = yy
            elif pa_content=='categ':
                out = category
            elif pa_content.startswith('file'):
                filename = ""
                with_regexp = 0
                regexp = ""
                if "[" in pa_content:
                    with_regexp = 1
                    split_index_start = pa_content.find("[")
                    split_index_stop =  pa_content.rfind("]")
                    regexp = pa_content[split_index_start+1:split_index_stop]
                    filename = pa_content[split_index_stop+2:]#]:
                else :
                    filename = pa_content.split(":")[1]
                if os.path.exists(os.path.join(curdir, filename)):
                    fp = open(os.path.join(curdir, filename), 'r')
                    if pa_content[:5]=="file*":
                        out = sep.join(map(lambda x: re.split(regexp,x.strip())[-1], fp.readlines()))
                    else:
                        out = re.split(regexp, fp.readline().strip())[-1]
                    fp.close()
            return out

        counter_path = re.sub('<PA>(?P<content>[^<]*)</PA>',
                              get_pa_tag_content,
                              parameters['counterpath'])
        counter_path = counter_path.replace(" ", "")
        counter_path = counter_path.replace("\n", "")

        rn_format = re.sub('<PA>(?P<content>[^<]*)</PA>',
                           get_pa_tag_content,
                           parameters['rnformat'])
        # Check if the report number does not already exists
        if os.path.exists("%s/%s" % (curdir, parameters['edsrn'])):
            fp = open("%s/%s" % (curdir, parameters['edsrn']), "r")
            oldrn = fp.read()
            fp.close()
            if oldrn != "" and not re.search("\?\?\?", oldrn):
                rn = oldrn
                return ""
        # What is the initial value, if any, of the generated report number?
        initial_value = 0
        if 'initialvalue' in parameters and parameters['initialvalue'].isdigit():
            initial_value = int(parameters['initialvalue'])-1
        # create it
        rn = create_reference(counter_path, rn_format, nb_length, initial_value)
        rn = rn.replace("\n", "")
        rn = rn.replace("\r", "")
        rn = rn.replace("\015", "")
        rn = rn.replace("\013", "")
        rn = rn.replace("\012", "")

        # The file edsrn is created in the submission directory, and it stores the report number
        fp = open("%s/%s" % (curdir, parameters['edsrn']), "w")
        fp.write(rn)
        fp.close()
    # The report number is just read from a specified file
    elif parameters['autorngen'] == "N":
        fp = open("%s/%s" % (curdir, parameters['edsrn']), "r")
        rn = fp.read()
        fp.close()
    # Some documents are really annoying and insist on a totally different way of doing things
    # This code is for documents which have the access number in the report
    # number (instead of using a counter)
    elif parameters['autorngen'] == "A":
        rn = parameters['rnformat'].replace("<PA>access</PA>", access)
    # The file accessno/edsrn is created, and it stores the report number
    fp = open("%s/%s" % (curdir, parameters['edsrn']), "w")
    fp.write(rn)
    fp.close()
    return ""

def create_reference(counter_path, ref_format, nb_length=3, initial_value=0):
    """From the counter-file for this document submission, get the next
       reference number and create the reference.
    """
    ## Does the WebSubmit CFG_WEBSUBMIT_COUNTERSDIR directory exist? Create it if not.
    full_path = os.path.split(os.path.join(CFG_WEBSUBMIT_COUNTERSDIR, counter_path))[0]
    try:
        mymkdir(full_path)
    except:
        ## Unable to create the CFG_WEBSUBMIT_COUNTERSDIR Dir.
        msg = "File System: Cannot create counters directory %s" % full_path
        raise InvenioWebSubmitFunctionError(msg)

    counter = os.path.join(CFG_WEBSUBMIT_COUNTERSDIR, counter_path)

    ## Now, if the counter-file itself doesn't exist, create it:
    if not os.path.exists(counter):
        fp = open(counter, "a+", 0)
        try:
            fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as err:
            ## See: http://docs.python.org/library/fcntl.html#fcntl.lockf
            ## This might mean that some other process is already creating
            ## the file, so no need to initialized as well.
            if err.errno not in (errno.EACCES, errno.EAGAIN):
                raise
        else:
            try:
                if not fp.read():
                    fp.write(str(initial_value))
            finally:
                fp.flush()
                fcntl.lockf(fp, fcntl.LOCK_UN)
                fp.close()

    fp = open(counter, "r+", 0)
    fcntl.lockf(fp, fcntl.LOCK_EX)
    try:
        id_value = fp.read()
        if id_value.strip() == '':
            id_value = initial_value
        else:
            id_value = int(id_value)
        id_value += 1
        fp.seek(0)
        fp.write(str(id_value))
        ## create final value
        reference = ("%s-%0" + str(nb_length) + "d") % (ref_format,id_value)
        ## Return the report number prelude with the id_value concatenated on at the end
        return reference
    finally:
        fp.flush()
        fcntl.lockf(fp, fcntl.LOCK_UN)
        fp.close()

