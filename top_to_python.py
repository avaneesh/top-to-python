#
# Author: Avaneesh Kadam (avaneesh.kadam@gmail.com)
#
# Copyright (c) 2012-2014 by Avaneesh Kadam <avaneesh.kadam@gmail.com>
#
# You are free to copy/change/distribute this code as long as
# this copyright notice is kept intact. Yeah?
#

import re, os, sys, datetime

watch_list = []


class WatchFor:
    'Watch for this processes'

    def __init__(self, p_name, p_display_name):
        self.p_name = p_name
        self.p_display_name = p_display_name


class TopData:
    'Hold data about one sample of "top" output'

    def __init__(self, timestamp):
        self.timestamp = timestamp
        self.p_list = []
        self.p_watch_list = []
        self.switch_state = "unset"
        self.sso_state = "unset"
        for p in watch_list:
            new_p = ProcessData(p.p_name, -1)
            self.p_watch_list.append(new_p)

    def add_process(self, p_data):
        self.p_list.append(p_data)
        self.populate_watch_list(p_data)

    def populate_watch_list(self, p_data):
        for p in self.p_watch_list:
            if p.name == p_data.name:
                p.cpu = p_data.cpu

    def render(self, rec_num, out_template, out_file):
        'Render template into output file'
        p_list = self.p_list
        out_data = out_template % (rec_num, self.timestamp,
                                   self.p_watch_list[0].cpu, p_list[0],
                                   p_list[1], p_list[2], p_list[3])
        out_file.write(out_data)


class ProcessData:
    'Hold "top" info about one process'

    def __init__(self, p_name, p_cpu):
        self.name = p_name
        self.cpu = p_cpu

    def is_in_watchFor_list(self):
        for p in watch_list:
            if self.name == p.p_name:
                return True
                return False

    def __repr__(self):
        return '%s(%s)' % (self.name, self.cpu)


def parse_top_line(process_line, c_top_rec):
    'Parse one line from top command and extract fields'
    # work, with . or : or - or /
    process_data = re.findall(r"[\w.:\-/]+", process_line)
    p_name = process_data[11]
    p_cpu = process_data[8]

    # Create process data object
    p_data = ProcessData(p_name, p_cpu)

    # Add this to top_record
    c_top_rec.add_process(p_data)
    print "Process name: " + p_name + " CPU: " + p_cpu

#def add_top_record(c_top_rec):
#    'Parsing of one top record is completed, add it in specific output format'
#     top_record_list.append(c_top_rec)


# Reads the file generated by 'top_recorder' program
def parse_file(file_name, rec_list):
    current_parse_state = "looking_for_start_marker"
    skip_line = 0
    record_start_pattern = "^================= "
    record_end_pattern = "^=============================================================================="
    top_process_info_starts_at_line = 8
    NUM_PROCESSES_TO_PARSE = 4
    parsed_processes = 0
    top_file_name = file_name
    top_record_list = rec_list

    try:
        top_file = open(top_file_name)
    except:
        print 'Could not open file:', top_file_name
        sys.exit()

    # Parse top output file and create data model
    for l in top_file:
        l = l.rstrip('\n')
        if re.findall(record_start_pattern, l):
            timestamp = l.rsplit(' ')[4]
            print "Date " + l.rsplit(' ')[4]
            current_parse_state = "looking_for_process_info_start"
            current_top_record = TopData(timestamp)
        elif re.findall(record_end_pattern, l):
            # Ready for next iteration
            skip_line = 0
            parsed_processes = 0
            #add_top_record(current_top_record)
            top_record_list.append(current_top_record)
            current_parse_state = "looking_for_start_marker"
            print ">>>>>>>>>>>>> Parsed, exiting... <<<<<<<<<<"
        else:
            if current_parse_state == "looking_for_process_info_start":
                skip_line += 1
                if skip_line == top_process_info_starts_at_line:
                    current_parse_state = "parsing_process_info"
            # continue, so we parse this line as well, so no elif
            if current_parse_state == "parsing_process_info":
                if parsed_processes == NUM_PROCESSES_TO_PARSE:
                    current_parse_state = "looking_for_end_marker"
                else:
                    parse_top_line(l, current_top_record)
                    parsed_processes += 1

    # Now analyse the data model
    # Here we will find out any specifics Eg. CPU share of IOS process
    #    for r in top_record_list:
    #        r.populate_watch_list()

    try:
        f = open(file_name + '.template')
        stats_template = f.read()
        # Lets do output formatting now
        record_num = 1
        with open(file_name + '.info', 'w') as f:
            for r in top_record_list:
                r.render(record_num, stats_template, f)
                record_num += 1
    except:
        print 'Template file not found, not generating any template'


def init_data(watch_list_arg):
    global watch_list
    watch_list = watch_list_arg
