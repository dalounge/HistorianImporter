import csv
import os
import re

class HistorianImport():
    '''
    Initialize import by calling init() function
    '''
    def __init__(self, historianpath, dbfiles, tempfiles):
        self.historian_path = historianpath # Path of complete files
        self.db_files = dbfiles # Path of DB files to parse
        self.temp_files = tempfiles # Temp space

    def accessNamesMod(self, prefix):
        '''
        from accessNames() goes through file and adds the prefix of the DB.CSV file to the access names
        '''
        modify_list = []

        with open(os.path.join(self.temp_files, 'IOAccess_mod.csv'), 'w', newline='') as f:
            w = csv.writer(f)

            with open(os.path.join(self.temp_files, 'IOAccess.csv')) as f:
                c = csv.reader(f)

                for line in c:
                    if prefix == None:
                        w.writerow(line)
                        modify_list.append(line)
                    else:
                        line[1] = line[1] + f'_{prefix}'
                        w.writerow(line)
                        modify_list.append(line)

        return modify_list

    def accessNames(self):
        '''
        Builds access names list.  In Historian indexes the access name to the
        IDAS name inside Historian config.
        '''

        with open(os.path.join(self.temp_files, 'IOAccess_mod.csv')) as f:
            c = csv.reader(f)
            access_names= []
            for line in c:
                if re.search('(:IOAccess)|(OPC)|(Galaxy)|(OPCUA)', line[0]):
                    continue
                else:
                    access_names.append(line)

        return access_names

    def findAccess(self, aName):
        '''
        Returns all the access name to build the Historian csv file
        '''
        access_list = self.accessNames()
        for x in access_list:
            if x[0] == aName:
                return x

    def createAccess(self):
        '''
        Gathers access names in list for writing to access name file
        '''
        with open(os.path.join(self.temp_files, 'IOAccess_mod.csv'), 'r') as f:
            c = csv.reader(f)
            io_servers = []
            topic = []
            master_io_servers = []
            master_topic = []
            for line in c:
                if re.search('(:IOAccess)|(OPC)|(Galaxy)|(OPCUA)', line[0]):
                    continue
                else:
                    if line[4] == 'No':
                        DDEProtocol = 'SuiteLink'

                    else:
                        DDEProtocol = 'DDE'

                    io_servers = [
                        '$local', # ComputerName
                        line[1], # ApplicationName
                        '', # AltComputerName
                        '$local', # IDASComponent
                        DDEProtocol # ProtocolType
                    ]

                    topic = [
                        line[2], # Topic
                        line[1], # ApplicationName
                        '$local', # ComputerName
                        60000, # TimeOut
                        'No', # LateData
                        60, # IdleDuration
                        120 # Processing Interval
                    ]

                    master_io_servers.append(io_servers)
                    master_topic.append(topic)
        return master_io_servers, master_topic

    def splitFiles(self, file_path):
        '''
        Split the DB dumps into chunks into Temp folder for processing
        '''

        new_file = False

        with open(file_path, 'r') as f:
            c = csv.reader(f)

            for line in c:
                if new_file == False:
                    if re.search(':', line[0]):
                        split_file = open(os.path.join(self.temp_files, line[0][1:] + '.csv'), 'w', newline='')
                        sf = csv.writer(split_file)
                        sf.writerow(line)
                        new_file = True

                elif new_file:
                    if re.search(':', line[0]):
                        split_file.close()
                        split_file = open(os.path.join(self.temp_files, line[0][1:] + '.csv'), 'w', newline='')
                        sf = csv.writer(split_file)
                        sf.writerow(line)
                    else:
                        sf.writerow(line)

            split_file.close()

    '''
    Start writing out to Historian Dump file with correct format
    '''
    def euFormat(self, eu_syntax):
        '''
        Fills out the Engineering Unit.  If blank sets none.  Strips out double quotes
        Should be used to format engineer units for special instances
        '''
        if len(eu_syntax) == 0:
            return 'None'
        else:
            return str(eu_syntax.replace("\"", '').lstrip())

    def euSuffix(self, suffix, tag):
        '''
        If EU has suffix write out in tagname
        '''
        if suffix == None:
            return tag
        else:
            return f'{suffix}_{tag}'

    def writeHist(self, filename, suffix):
        '''
        Begin writing out each row to historian file.
        Revision:  For analogs only.  Adding writeHistDisc for Flint
        '''

        # Historian import, main category columns
        historian_col = [
            ':(AnalogTag)TagName',
            'Description',
            'IOServerComputerName',
            'IOServerAppName',
            'TopicName',
            'ItemName',
            'AcquisitionType',
            'StorageType',
            'AcquisitionRate',
            'StorageRate',
            'TimeDeadband',
            'SamplesInAI',
            'AIMode',
            'EngUnits',
            'MinEU',
            'MaxEU',
            'MinRaw',
            'MaxRaw',
            'Scaling',
            'RawType',
            'IntegerSize',
            'Sign',
            'ValueDeadband',
            'InitialValue',
            'CurrentEditor',
            'RateDeadband',
            'InterpolationType',
            'RolloverValue',
            'ServerTimeStamp',
            'DeadbandType',
            'TagId',
            'ChannelStatus',
            'AITag',
            'AIHistory',
            'SourceTag',
            'SourceServer',
            'SourceTagId',
            'ShardId'
        ]

        # Opens the new file to write out to
        with open(os.path.join(self.historian_path, f"{filename.split('.')[0]}.txt" if suffix == None else suffix + '_DB.txt'), 'w', newline='') as f:
            c = csv.writer(f, delimiter='\t')
            c.writerow([':(Mode)update'])
            c.writerow(historian_col)

            with open(os.path.join(self.temp_files, 'IOInt.csv'), 'r') as db:
                d = csv.reader(db)
                hist_list = []

                for r in d:
                    if r[3] == 'Yes':
                        hist_list = [
                            self.euSuffix(suffix, r[0]), # Tagname
                            r[2], # Description
                            '$local', # IOServerComputerName
                            self.findAccess(r[42])[1], # IOServerAppName
                            self.findAccess(r[42])[2], # Topic
                            r[44], # ItemName
                            'IOServer', # Acquisition
                            'Delta', # Storage Type
                            0, # Acquisition Rate
                            0, # Storage Rate
                            0, # TimeDeadband
                            0, # SamplesInAI
                            'All', # AIMode
                            self.euFormat(r[10]), # EngUnits
                            r[12], # MinEU
                            r[13], # MaxEU
                            r[39], # MinRaw
                            r[40], # MaxRaw
                            'Linear', # Scaling
                            'Integer', # RawType
                            32, # IntegerSize
                            'Signed', # Sign
                            r[15], # ValueDeadband
                            r[11], # InitialValue
                            0, # CurrentEditor
                            0, # RateDeadband
                            'System Default', # InterpolationType
                            0, # RolloverValue
                            'No', # ServerTimeStamp
                            'TimeValue', # DeadbandType
                            '', # TagId
                            1, # ChannelStatus
                            0, # AITag
                            'True', # AIHistory
                            '', # SourceTag
                            '', # SourceServer
                            '', # SourceTagId
                            '{00000000-0000-0000-0000-000000000000}', # ShardId
                        ]

                        c.writerow(hist_list)

                        hist_list = []

            with open(os.path.join(self.temp_files, 'IOReal.csv'), 'r') as db:
                d = csv.reader(db)
                hist_list = []

                for r in d:
                    if r[3] == 'Yes':
                        hist_list = [
                            self.euSuffix(suffix, r[0]), # Tagname
                            r[2], # Description
                            '$local', # IOServerComputerName
                            self.findAccess(r[42])[1], # IOServerAppName
                            self.findAccess(r[42])[2], # Topic
                            r[44], # ItemName
                            'IOServer', # Acquisition
                            'Delta', # Storage Type
                            0, # Acquisition Rate
                            0, # Storage Rate
                            0, # TimeDeadband
                            0, # SamplesInAI
                            'All', # AIMode
                            self.euFormat(r[10]), # EngUnits
                            r[12], # MinEU
                            r[13], # MaxEU
                            r[39], # MinRaw
                            r[40], # MaxRaw
                            'Linear', # Scaling
                            'MSFloat', # RawType
                            0, # IntegerSize
                            '', # Sign
                            r[15], # ValueDeadband
                            r[11], # InitialValue
                            0, # CurrentEditor
                            0, # RateDeadband
                            'System Default', # InterpolationType
                            0, # RolloverValue
                            'No', # ServerTimeStamp
                            'TimeValue', # DeadbandType
                            '', # TagId
                            1, # ChannelStatus
                            0, # AITag
                            'True', # AIHistory
                            '', # SourceTag
                            '', # SourceServer
                            '', # SourceTagId
                            '{00000000-0000-0000-0000-000000000000}', # ShardId
                        ]

                        c.writerow(hist_list)

                        hist_list = []

                    '''
        Writing out discrete portion of DB Dump.  This was added later.
        Merge with writeHist
        '''
        # Historian import, main category columsn discrete
        historian_col = [
            ':(DiscreteTag)TagName',
            'Description',
            'IOServerComputerName',
            'IOServerAppName',
            'TopicName',
            'ItemName',
            'AcquisitionType',
            'StorageType',
            'AcquisitionRate',
            'TimeDeadband',
            'SamplesInAI',
            'AIMode',
            'Message0',
            'Message1',
            'InitialValue',
            'CurrentEditor',
            'ServerTimeStamp',
            'TagId',
            'ChannelStatus',
            'AITag',
            'AIHistory',
            'StorageRate',
            'SourceTag',
            'SourceServer',
            'SourceTagId',
            'ShardId'
        ]

        with open(os.path.join(self.historian_path, f"{filename.split('.')[0]}Disc.txt" if suffix == None else suffix + '_DBDisc.txt'), 'w', newline='') as f:
            c = csv.writer(f, delimiter='\t')
            c.writerow([':(Mode)update'])
            c.writerow(historian_col)

            with open(os.path.join(self.temp_files, 'IODisc.csv'), 'r') as db:
                    d = csv.reader(db)
                    hist_list = []

                    for r in d:
                        if r[3] == 'Yes':
                            hist_list = [
                                self.euSuffix(suffix, r[0]), # Tagname
                                r[2], # Description
                                '$local', # IOServerComputerName
                                self.findAccess(r[13])[1], # IOServerAppName
                                self.findAccess(r[13])[2], # Topic
                                r[15], # ItemName
                                'IOServer', # Acquisition
                                'Delta', # Storage Type
                                0, # Acquisition Rate
                                0, # TimeDead
                                0, # SamplesInAI
                                'All', # AIMode
                                'OFF', # Message0
                                'ON', # Message1
                                0, # InitialValue
                                0, # CurrentEditor
                                'No', # ServerTimeStamp
                                '', # TagId
                                1, # ChannelStatus
                                0, # AITag
                                'True', # AIHistory
                                0, # StorageRate
                                '', # SourceTag
                                '', # SourceServer
                                '', # SourceTagID
                                '{00000000-0000-0000-0000-000000000000}', # ShardId

                            ]

                            c.writerow(hist_list)

                            hist_list = []


    def buildAcessConfig(self, m_servers, m_topics):
        '''
        Build out the base access names for Historian
        '''

        iodriver_header = [
            ':(IODriver)ComputerName',
            'AltComputerName',
            'StoreForwardMode',
            'StoreForwardPath',
            'MinMBThreshold',
            'Enabled',
            'StoreForwardDuration',
            'AutonomousStartupTimeout',
            'BufferCount',
            'FileChunkSize',
            'ForwardingDelay',
            'ConnectionTimeout',
            'CompressionEnabled',
            'TCPPort',
            'IntegratedSecurity',
            'ConnectionDetails'
        ]

        iodriver_body = [
            '$local',
            '',
            'Off',
            '',
            16,
            'Yes',
            180,
            60,
            128,
            65536,
            0,
            60,
            'FALSE',
            32568,
            'TRUE',
            '',
        ]

        ioserver_header = [
            ':(IOServer)ComputerName',
            'ApplicationName',
            'AltComputerName',
            'IDASComputerName',
            'ProtocolType'
        ]

        topic_header = [
            ':(Topic)Name',
            'ApplicationName',
            'ComputerName',
            'TimeOut',
            'LateData',
            'IdleDuration',
            'ProcessingInterval'
        ]

        '''
        Write out the access names
        '''
        with open(os.path.join(self.historian_path, 'access_names.txt'), 'w', newline='') as f:
            c = csv.writer(f, delimiter='\t')

            c.writerow([':(Mode)update'])
            c.writerow(iodriver_header)
            c.writerow(iodriver_body)
            c.writerow(ioserver_header)
            for i in m_servers:
                for el in i:
                    c.writerow(el)
            c.writerow(topic_header)
            for i in m_topics:
                for el in i:
                    c.writerow(el)

    '''
    Check and create EU
    '''

    def cacheSplit(self, data_list):
        '''
        Generator to split files and process
        '''
        for d_file in data_list:
            yield str(os.path.join(self.db_files, d_file))

    def grabEU(self):
        '''
        Releases set of the EU from DB Dumps
        '''
        eu_list = []
        with open(os.path.join(self.temp_files, 'IOInt.csv')) as f:
            c = csv.reader(f)
            for row in c:
                if row[10]=='EngUnits' or len(row[10])==0:
                    continue
                else:
                    eu_list.append(row[10])

            with open(os.path.join(self.temp_files, 'IOReal.csv')) as f:
                c = csv.reader(f)
                for row in c:
                    if row[10]=='EngUnits' or len(row[10])==0:
                        continue
                    else:
                        eu_list.append(row[10].replace("\"", '').lstrip())
        eu_set = set(eu_list)

        return list(eu_set)

    def buildEU(self):
        '''
        Write out engineering units .txt file for import
        '''
        eu_files = []

        for folders, subfolders, filenames in os.walk(self.db_files):
            for filename in filenames:
                eu_files.append(filename)

        cache = self.cacheSplit(eu_files)
        master_eu = []
        for c in cache:
            self.splitFiles(c)
            master_eu.append(self.grabEU())

        flatten = [f for sub in master_eu for f in sub]
        set_flat = set(flatten)

        eu_col = [
            ':(EngineeringUnit)Unit',
            'DefaultTagRate',
            'IntegralDivisor'
        ]

        with open(os.path.join(self.historian_path, 'eu.txt'), 'w', newline='') as f:
            c = csv.writer(f, delimiter='\t')
            c.writerow([':(Mode)update'])
            c.writerow(eu_col)

            for el in list(set_flat):
                c.writerow([el, 10000, 1])

    def init(self):
        '''
        Initialize code
        '''
        m_servers = []
        m_topics = []

        # Start reading each file in EU folder to parse and create
        for folders, subfolders, filenames in os.walk(self.db_files):
            for filename in filenames:
                # Parses out _ and prefix for each file name
                if re.search('_', filename):
                    pre = filename.split('_')[0]
                else:
                    pre = None
                # Starts the splitting files in temp folder
                self.splitFiles(os.path.join(folders, filename))
                # Modifies the access names
                self.accessNamesMod(pre)
                # Write out the Historian files now
                self.writeHist(filename, pre)
                # Start creating access name file
                append_access = self.createAccess()
                # Builds list to send to access name function to write application and topics
                m_servers.append(append_access[0])
                m_topics.append(append_access[1])

        self.buildAcessConfig(m_servers, m_topics)
        self.buildEU()


