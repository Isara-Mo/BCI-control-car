import sys
from pylsl import StreamInfo, StreamOutlet
import argparse
import os
import string
import atexit
import threading
import sys
import random
import serial
import struct
import numpy as np
import time
import timeit
import atexit
import logging
import pdb
import glob

header = {}
sample_count = 0
rawData_dict = dict(channel1= 0,channel2= 0,channel3= 0,channel4= 0,channel5= 0,channel6= 0,channel7= 0,channel8= 0,refer1 =0,refer2 = 0)          
data_ = []
PORT = 'COM7'
SAMPLE_RATE = 250#500.0 # or 250 
START_BYTE = 0xA0  # start of data packet
END_BYTE = 0xC0  # end of data packet
ADS1299_Vref = 4.5  #reference voltage for ADC in ADS1299.  set by its hardware
ADS1299_gain = 24.0  #assumed gain setting for ADS1299.
scale_fac_uVolts_per_count = ADS1299_Vref/float((pow(2,23)-1))/ADS1299_gain*1000000.
scale_fac_accel_G_per_count = 0.002 /(pow(2,4)) #assume set to +/4G, so 2 mG 
c = ''
'''

command_stop = "s";
command_startText = "x";
command_startBinary = "b";
command_startBinary_wAux = "n";
command_startBinary_4chan = "v";
command_activateFilters = "F";
command_deactivateFilters = "g";
command_deactivate_channel = {"1", "2", "3", "4", "5", "6", "7", "8"};
command_activate_channel = {"q", "w", "e", "r", "t", "y", "u", "i"};
command_activate_leadoffP_channel = {"!", "@", "#", "$", "%", "^", "&", "*"};  //shift + 1-8
command_deactivate_leadoffP_channel = {"Q", "W", "E", "R", "T", "Y", "U", "I"};   //letters (plus shift) right below 1-8
command_activate_leadoffN_channel = {"A", "S", "D", "F", "G", "H", "J", "K"}; //letters (plus shift) below the letters below 1-8
command_deactivate_leadoffN_channel = {"Z", "X", "C", "V", "B", "N", "M", "<"};   //letters (plus shift) below the letters below the letters below 1-8
command_biasAuto = "`";
command_biasFixed = "~";
'''

class BCIduinoSample(object):
  """Object encapulsating a single sample from the BCIduino board."""
  def __init__(self, packet_id, channel_data, aux_data):
    self.id = packet_id
    self.channel_data = channel_data
    self.aux_data = aux_data

class BCIduinoBoard(object):
  """

  Handle a connection to an BCIduino board.

  Args:
    port: The port to connect to.
    baud: The baud of the serial connection.
    
  """

  def __init__(self, port=None, baud=256000, filter_data=True,
    scaled_output=True, daisy=False, log=True, timeout=None):
    self.log = log 
    self.streaming = False
    self.baudrate = baud
    self.timeout = 10
    if not port:
      port = PORT#'COM3'
    self.port = port
    print("Connecting to BCIduino at port %s" %(port))
    self.ser = serial.Serial(port= port, baudrate = baud, timeout=timeout)

    print("Serial established...")

    #time.sleep(2)
    #Initialize 32-bit board, doesn't affect 8bit board
    #self.ser.write(b'v')


    #wait for device to be ready
    time.sleep(1)
    #self.print_incoming_text()

    self.streaming = False
    self.filtering_data = filter_data
    self.scaling_output = scaled_output
    self.eeg_channels_per_sample = 8 # number of EEG channels per sample *from the board*
    self.aux_channels_per_sample = 3 # number of AUX channels per sample *from the board*
    self.read_state = 0
    self.daisy = daisy
    self.last_odd_sample = BCIduinoSample(-1, [], []) # used for daisy
    self.log_packet_count = 0
    self.attempt_reconnect = False
    self.last_reconnect = 0
    self.reconnect_freq = 5
    self.packets_dropped = 0

    #Disconnects from board when terminated
    atexit.register(self.disconnect)
  
  def getSampleRate(self):
    if self.daisy:
      return SAMPLE_RATE/2
    else:
      return SAMPLE_RATE
  
  def getNbEEGChannels(self):
    if self.daisy:
      return self.eeg_channels_per_sample*2
    else:
      return self.eeg_channels_per_sample
  
  def getNbAUXChannels(self):
    return  self.aux_channels_per_sample

  def start_streaming(self, callback, lapse=-1):
    """
    Start handling streaming data from the board. Call a provided callback
    for every single sample that is processed (every two samples with daisy module).

    Args:
      callback: A callback function -- or a list of functions -- that will receive a single argument of the
          BCIduinoSample object captured.
    """
    if not self.streaming:
      self.ser.write(b'~5')
      time.sleep(2)
      self.ser.write(b'b')
      self.streaming = True

    start_time = timeit.default_timer()

    # Enclose callback funtion in a list if it comes alone
    if not isinstance(callback, list):
      callback = [callback]
    

    #Initialize check connection
    self.check_connection()

    while self.streaming:

      # read current sample
      sample = self._read_serial_binary()
      # if a daisy module is attached, wait to concatenate two samples (main board + daisy) before passing it to callback
      if self.daisy:
        # odd sample: daisy sample, save for later
        if ~sample.id % 2:
          self.last_odd_sample = sample
        # even sample: concatenate and send if last sample was the fist part, otherwise drop the packet
        elif sample.id - 1 == self.last_odd_sample.id:
          # the aux data will be the average between the two samples, as the channel samples themselves have been averaged by the board
          avg_aux_data = list((np.array(sample.aux_data) + np.array(self.last_odd_sample.aux_data))/2)
          whole_sample = BCIduinoSample(sample.id, sample.channel_data + self.last_odd_sample.channel_data, avg_aux_data)
          for call in callback:
            call(whole_sample)
      else:
        for call in callback:
          call(sample)
      
      if(lapse > 0 and timeit.default_timer() - start_time > lapse):
        self.stop()
      if self.log:
        self.log_packet_count = self.log_packet_count 
  
  
  """
    PARSER:
    Parses incoming data packet into BCIduinoSample.
    Incoming Packet Structure:
    Start Byte(1)|Sample ID(1)|Channel Data(24)|Aux Data(6)|End Byte(1)
    0xA0|0-255|8, 3-byte signed ints|3 2-byte signed ints|0xC0

    START_BYTE = 0xA0  # start of data packet
    END_BYTE = 0xC0  # end of data packet
    

  """
  def _read_serial_binary(self, max_bytes_to_skip=3000):
    def read(n):
      b = self.ser.read(n)
      if not b:
        #self.warn('Device appears to be stalled. Quitting...')
        sys.exit()
        raise Exception('Device Stalled')
        sys.exit()
        return '\xFF'
      else:
        return b

    for rep in range(max_bytes_to_skip):

      #---------Start Byte & ID---------
      if self.read_state == 0:
        
        b = read(1)
        
        if struct.unpack('B', b)[0] == START_BYTE:
          if(rep != 0):
            #self.warn('Skipped %d bytes before start found' %(rep))
            rep = 0
          packet_id = struct.unpack('B', read(1))[0] #packet id goes from 0-255
          log_bytes_in = str(packet_id)

          self.read_state = 1

      #---------Channel Data---------
      elif self.read_state == 1:
        channel_data = []
        for c in range(self.eeg_channels_per_sample):

          #3 byte ints
          literal_read = read(3)
          #print("len")
          #print(len(literal_read))
          while(len(literal_read)!=3):
            literal_read = read(3)

          unpacked = struct.unpack('3B', literal_read)
          log_bytes_in = log_bytes_in + '|' + str(literal_read)

          #3byte int in 2s compliment
          if (unpacked[0] >= 127):
            pre_fix = bytes(bytearray.fromhex('FF')) 
          else:
            pre_fix = bytes(bytearray.fromhex('00'))


          literal_read = pre_fix + literal_read

          #unpack little endian(>) signed integer(i) (makes unpacking platform independent)
          myInt = struct.unpack('>i', literal_read)[0]

          if self.scaling_output:
            channel_data.append(myInt*scale_fac_uVolts_per_count)
          else:
            channel_data.append(myInt)

        self.read_state = 2

      #---------Accelerometer Data---------
      elif self.read_state == 2:
        aux_data = []
        for a in range(self.aux_channels_per_sample):

          #short = h
          acc_ = read(2)
          while(len(acc_)!=2):
            acc_ = read(2)
          acc = struct.unpack('>h', acc_)[0]
          log_bytes_in = log_bytes_in + '|' + str(acc)

          if self.scaling_output:
            aux_data.append(acc*scale_fac_accel_G_per_count)
          else:
              aux_data.append(acc)

        self.read_state = 3
      #---------End Byte---------
      elif self.read_state == 3:
        val = struct.unpack('B', read(1))[0]
        log_bytes_in = log_bytes_in + '|' + str(val)
        self.read_state = 0 #read next packet
        if (val == END_BYTE):
          sample = BCIduinoSample(packet_id, channel_data, aux_data)
          self.packets_dropped = 0
          return sample
        else:
          #self.warn("ID:<%d> <Unexpected END_BYTE found <%s> instead of <%s>"      
            #%(packet_id, val, END_BYTE))
          logging.debug(log_bytes_in)
          self.packets_dropped = self.packets_dropped
  
  """

  Clean Up (atexit)

  """
  def stop(self):
    print("Stopping streaming...\nWait for buffer to flush...")
    self.streaming = False
    self.ser.write(b's')
    if self.log:
      logging.warning('sent <s>: stopped streaming')

  def disconnect(self):
    if(self.streaming == True):
      self.stop()
    if (self.ser.isOpen()):
      print("Closing Serial...")
      self.ser.close()
      logging.warning('serial closed')
       

  """

      SETTINGS AND HELPERS

  """
  def warn(self, text):
    if self.log==0:
      #log how many packets where sent succesfully in between warnings
      if self.log_packet_count ==1:
        logging.info('Data packets received:'+str(self.log_packet_count))
        self.log_packet_count = 0
      logging.warning(text)
    print("Warning: %s" % text)


  def print_incoming_text(self):
    """

    When starting the connection, print all the debug data until
    we get to a line with the end sequence '$$$'.

    """
    line = ''
    #Wait for device to send data
    time.sleep(1)
    
    if self.ser.inWaiting():
      line = ''
      c = ''
     #Look for end sequence $$$
      while '$$$' not in line:
      #while True:# not in line:
        c = self.ser.read()#.decode('utf-8')#.decode('utf-8',errors='replace')# errors='ignore')
        #line += c
        print(hex(int(c)))
        #print("waiting")
      print(line)
    #else:
      #self.warn("No Message")
      #continue

  def BCIduino_id(self, serial):
    """

    When automatically detecting port, parse the serial
    return for the "BCIduino" ID.

    """
    line = ''
    #Wait for device to send data
    time.sleep(2)
    
    if serial.inWaiting():
      line = ''
      c = ''
     #Look for end sequence $$$
      while '$$$' not in line:
        c = serial.read().decode('utf-8')
        line += c
      if "BCIduino" in line:
        return True
    return False

  def print_register_settings(self):
    self.ser.write(b'?')
    time.sleep(0.5)
    self.print_incoming_text()
  #DEBBUGING: Prints individual incoming bytes
  def print_bytes_in(self):
    if not self.streaming:
      self.ser.write(b'b')
      self.streaming = True
    while self.streaming:
      self.c = struct.unpack('B',self.ser.read())[0]
      print(self.c)
      '''Incoming Packet Structure:
    Start Byte(1)|Sample ID(1)|Channel Data(24)|Aux Data(6)|End Byte(1)
    0xA0|0-255|8, 3-byte signed ints|3 2-byte signed ints|0xC0'''

  def print_packets_in(self):
    print ("csvdbjh")
    skipped_str = ''
    if not self.streaming:
      self.ser.write(b'b')
      self.streaming = True
      
    #while self.streaming:
    
    while self.streaming:
      #print "ing"
      data_ = []
      b = struct.unpack('B', self.ser.read())[0]
      data_.append(b)
      if b == START_BYTE:
        self.attempt_reconnect = False
        if skipped_str:
          #logging.debug('SKIPPED\n' + skipped_str + '\nSKIPPED')
          skipped_str = ''

        packet_str = "%03d"%(b) + '|'
        b = struct.unpack('B', self.ser.read())[0]
        packet_str = packet_str + "%03d"%(b) + '|'
        data_.append(b)
        
        #data channels
        for i in range(24-1):
          b = struct.unpack('B', self.ser.read())[0]
          packet_str = packet_str + '.' + "%03d"%(b)
          data_.append(b)

        b = struct.unpack('B', self.ser.read())[0]
        packet_str = packet_str + '.' + "%03d"%(b) + '|'
        data_.append(b)
        
        #aux channels
        for i in range(6-1):
          b = struct.unpack('B', self.ser.read())[0]
          packet_str = packet_str + '.' + "%03d"%(b)
          data_.append(b)
          
        b = struct.unpack('B', self.ser.read())[0]
        packet_str = packet_str + '.' + "%03d"%(b) + '|'
        data_.append(b)

        #end byte
        b = struct.unpack('B', self.ser.read())[0]
        data_.append(b)
        #Valid Packet
        if b == END_BYTE:
          sample_count = data_[1]
          print('the',sample_count,'th sample')
          packet_str = packet_str + '.' + "%03d"%(b) + '|VAL'
          print("//packet///")
          print(packet_str)
          print("/channals//")
          #print("/channals//")
          rawData_dict['channel1'] = data_[2]
          rawData_dict['channel1'] <<= 8
          rawData_dict['channel1'] |= data_[3]
          rawData_dict['channel1'] <<= 8
          rawData_dict['channel1'] |= data_[4]
          #rawData_dict.get('ch1')

          rawData_dict['channel2'] = data_[5]
          rawData_dict['channel2'] <<= 8
          rawData_dict['channel2'] |= data_[6]
          rawData_dict['channel2'] <<= 8
          rawData_dict['channel2'] |= data_[7]
          

          rawData_dict['channel3'] = data_[8]
          rawData_dict['channel3'] <<= 8
          rawData_dict['channel3'] |= data_[9]
          rawData_dict['channel3'] <<= 8
          rawData_dict['channel3'] |= data_[10]
          
          rawData_dict['channel4'] = data_[11]
          rawData_dict['channel4'] <<= 8
          rawData_dict['channel4'] |= data_[12]
          rawData_dict['channel4'] <<= 8
          rawData_dict['channel4'] |= data_[13]
          #channel1 <<= 8

          rawData_dict['channel5'] = data_[14]
          rawData_dict['channel5'] <<= 8
          rawData_dict['channel5'] |= data_[15]
          rawData_dict['channel5'] <<= 8
          rawData_dict['channel5'] |= data_[16]
          #channel1 <<= 8

          rawData_dict['channel6'] = data_[17]
          rawData_dict['channel6'] <<= 8
          rawData_dict['channel6'] |= data_[18]
          rawData_dict['channel6'] <<= 8
          rawData_dict['channel6'] |= data_[19]
          #channel1 <<= 8

          rawData_dict['channel7'] = data_[20]
          rawData_dict['channel7'] <<= 8
          rawData_dict['channel7'] |= data_[21]
          rawData_dict['channel7'] <<= 8
          rawData_dict['channel7'] |= data_[22]
          #channel1 <<= 8

          rawData_dict['channel8'] = data_[23]
          rawData_dict['channel8'] <<= 8
          rawData_dict['channel8'] |= data_[24]
          rawData_dict['channel8'] <<= 8
          rawData_dict['channel8'] |= data_[25]


          rawData_dict['refer1'] = data_[26]
          rawData_dict['refer1'] <<= 8
          rawData_dict['refer1'] |= data_[27]
          rawData_dict['refer1'] <<= 8
          rawData_dict['refer1'] |= data_[28]

          rawData_dict['refer2'] = data_[29]
          rawData_dict['refer2'] <<= 8
          rawData_dict['refer2'] |= data_[30]
          rawData_dict['refer2'] <<= 8
          rawData_dict['refer2'] |= data_[31]

          #for each in data_:
            #print each
            
          print('channel1 =',rawData_dict.get('channel1'))
          print('channel2 =',rawData_dict.get('channel2'))
          print('channel3 =',rawData_dict.get('channel3'))
          print('channel4 =',rawData_dict.get('channel4'))
          print('channel5 =',rawData_dict.get('channel5'))
          print('channel6 =',rawData_dict.get('channel6'))
          print('channel7 =',rawData_dict.get('channel7'))
          print('channel8 =',rawData_dict.get('channel8'))
          print('refer1 =',rawData_dict.get('refer1'))
          print('refer2 =',rawData_dict.get('refer2'))
         
        #Invalid Packet
        else:
          packet_str = packet_str + '.' + "%03d"%(b) + '|INV'
          #Reset
          self.attempt_reconnect = True
          
      
      else:
        print(b)
        if b == END_BYTE:
          skipped_str = skipped_str + '|END|'
        else:
          skipped_str = skipped_str + "%03d"%(b) + '.'

      
      
      if self.attempt_reconnect and (timeit.default_timer()-self.last_reconnect) > self.reconnect_freq:
        self.last_reconnect = timeit.default_timer()
        #self.warn('Reconnecting')
        self.reconnect()
     
       
    print ("stopped") 


  def check_connection(self, interval = 2, max_packets_to_skip=10):
    #check number of dropped packages and establish connection problem if too large
    if self.packets_dropped > max_packets_to_skip:
      #if error, attempt to reconect
      self.reconnect()
    # check again again in 2 seconds
    threading.Timer(interval, self.check_connection).start()

  def reconnect(self):
    self.packets_dropped = 0
    #self.warn('Reconnecting')
    self.stop()
    time.sleep(0.5)
    self.ser.write(b'v')
    time.sleep(0.5)
    self.ser.write(b'b')
    time.sleep(0.5)
    self.streaming = True
    #self.attempt_reconnect = False


  #Adds a filter at 60hz to cancel out ambient electrical noise
  def enable_filters(self):
    self.ser.write(b'f')
    self.filtering_data = True

  def disable_filters(self):
    self.ser.write(b'g')
    self.filtering_data = False

  def test_signal(self, signal):
    if signal == 0:
      self.ser.write(b'0')
      #self.warn("Connecting all pins to ground")
    elif signal == 1:
      self.ser.write(b'p')
      #self.warn("Connecting all pins to Vcc")
    elif signal == 2:
      self.ser.write(b'-')
      #self.warn("Connecting pins to low frequency 1x amp signal")
    elif signal == 3:
      self.ser.write(b'=')
      #self.warn("Connecting pins to high frequency 1x amp signal")
    elif signal == 4:
      self.ser.write(b'[')
      #self.warn("Connecting pins to low frequency 2x amp signal")
    elif signal == 5:
      self.ser.write(b']')
      #self.warn("Connecting pins to high frequency 2x amp signal")
    #else:
      #self.warn("%s is not a known test signal. Valid signals go from 0-5" %(signal))
      #continue

  def set_channel(self, channel, toggle_position):
    #Commands to set toggle to on position
    if toggle_position == 1:
      if channel is 1:
        self.ser.write(b'!')
      if channel is 2:
        self.ser.write(b'@')
      if channel is 3:
        self.ser.write(b'#')
      if channel is 4:
        self.ser.write(b'$')
      if channel is 5:
        self.ser.write(b'%')
      if channel is 6:
        self.ser.write(b'^')
      if channel is 7:
        self.ser.write(b'&')
      if channel is 8:
        self.ser.write(b'*')
      if channel is 9 and self.daisy:
        self.ser.write(b'Q')
      if channel is 10 and self.daisy:
        self.ser.write(b'W')
      if channel is 11 and self.daisy:
        self.ser.write(b'E')
      if channel is 12 and self.daisy:
        self.ser.write(b'R')
      if channel is 13 and self.daisy:
        self.ser.write(b'T')
      if channel is 14 and self.daisy:
        self.ser.write(b'Y')
      if channel is 15 and self.daisy:
        self.ser.write(b'U')
      if channel is 16 and self.daisy:
        self.ser.write(b'I')
    #Commands to set toggle to off position
    elif toggle_position == 0:
      if channel is 1:
        self.ser.write(b'1')
      if channel is 2:
        self.ser.write(b'2')
      if channel is 3:
        self.ser.write(b'3')
      if channel is 4:
        self.ser.write(b'4')
      if channel is 5:
        self.ser.write(b'5')
      if channel is 6:
        self.ser.write(b'6')
      if channel is 7:
        self.ser.write(b'7')
      if channel is 8:
        self.ser.write(b'8')
      if channel is 9 and self.daisy:
        self.ser.write(b'q')
      if channel is 10 and self.daisy:
        self.ser.write(b'w')
      if channel is 11 and self.daisy:
        self.ser.write(b'e')
      if channel is 12 and self.daisy:
        self.ser.write(b'r')
      if channel is 13 and self.daisy:
        self.ser.write(b't')
      if channel is 14 and self.daisy:
        self.ser.write(b'y')
      if channel is 15 and self.daisy:
        self.ser.write(b'u')
      if channel is 16 and self.daisy:
        self.ser.write(b'i')
  
  def find_port(self):
    # Finds the serial port names
    if sys.platform.startswith('win'):
      ports = ['COM%s' % (i+1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
      ports = glob.glob('/dev/ttyUSB*')
    elif sys.platform.startswith('darwin'):
      ports = glob.glob('/dev/tty.usbserial*')
    else:
      raise EnvironmentError('Error finding ports on your operating system')
    BCIduino_port = ''
    for port in ports:
      try:
        s = serial.Serial(port= port, baudrate = self.baudrate, timeout=self.timeout)
        s.write(b'v')
        BCIduino_serial = self.BCIduino_id(s)
        s.close()
        if BCIduino_serial:
          BCIduino_port = port
      except (OSError, serial.SerialException):
        pass
    if BCIduino_port == '':
      raise OSError('Cannot find BCIduino port')
    else:
      return BCIduino_port

class StreamerLSL():
    
    def __init__(self,daisy=False):
        '''parser = argparse.ArgumentParser(description="BCIduino 'user'")
        parser.add_argument('-p', '--port',
                        help="Port to connect to BCIduino Dongle " +
                        "( ex /dev/ttyUSB0 or /dev/tty.usbserial-* )")
        parser.add_argument('-d', action="store_true",
                        help="Enable Daisy Module " +
                        "-d")
        args = parser.parse_args()'''
        port = None#args.port
        print ("\n-------BCIDUINO BOARD-------")
        print ("\n-------www.bciduino.cn-------")
        #print("\n")
        self.board = BCIduinoBoard(port, daisy=False)#args.d)
        #print(self.board)
        self.eeg_channels = self.board.getNbEEGChannels()
        self.sample_rate = self.board.getSampleRate()
        #print('{} EEG channels at {} Hz'.format(self.eeg_channels,self.sample_rate))

    def send(self,sample):
        data = sample.channel_data
        #print ( data )
        self.outlet_eeg.push_sample(data)

    def create_lsl(self):
        info_eeg = StreamInfo("BCIduino", 'EEG', self.eeg_channels, self.sample_rate, 'float32', "buaawyz")
        self.outlet_eeg = StreamOutlet(info_eeg)

    def cleanUp():
        board.disconnect()
        print ("Disconnecting...")
        atexit.register(cleanUp)

    def begin(self):
        '''print ("--------------INFO---------------")
        print ("User serial interface enabled...\n" + \
            "View command map at http://docs.BCIduino.com.\n" + \
            "Type /start to run -- and /stop before issuing new commands afterwards.\n" + \
            "Type /exit to exit. \n" + \
            "Board outputs are automatically printed as: \n" +  \
            "%  <tab>  message\n" + \
            "$$$ signals end of message")'''
        print("\n-------------BEGIN---------------")
        # Init board state
        # s: stop board streaming; v: soft reset of the 32-bit board (no effect with 8bit board)
        s = 'sv'
        # Tell the board to enable or not daisy module
        #print(self.board.daisy)
        if self.board.daisy:
            s = s + 'C'
        else:
            s = s + 'c'
        # d: Channels settings back to default
        s = s + 'd'

        while(s != "/exit"):
            # Send char and wait for registers to set
            if (not s):
                pass
            elif("help" in s):
                print ("View command map at:" + \
                    "http://docs.BCIduino.com/software/01-BCIduino_SDK.\n" +\
                    "For user interface: read README or view" + \
                    "https://github.com/BCIduino/BCIduino_Python")

            elif self.board.streaming and s != "/stop":
                print ("Error: the board is currently streaming data, please type '/stop' before issuing new commands.")
            else:
                # read silently incoming packet if set (used when stream is stopped)
                flush = False

                #if('/' == s[0]):
                if(True):
                    s = s[1:]
                    rec = False  # current command is recognized or fot

                    if("T:" in s):
                        lapse = int(s[string.find(s, "T:")+2:])
                        rec = True
                    elif("t:" in s):
                        lapse = int(s[string.find(s, "t:")+2:])
                        rec = True
                    else:
                        lapse = -1

                    #if("start" in s):
                    if(True):
                        # start streaming in a separate thread so we could always send commands in here 
                        boardThread = threading.Thread(target=self.board.start_streaming,args=(self.send,-1))
                        boardThread.daemon = True # will stop on exit
                        try:
                            boardThread.start()
                            #print("Streaming data now...")
                        except:
                                raise
                        rec = True
                    elif('test' in s):
                        test = int(s[s.find("test")+4:])
                        self.board.test_signal(test)
                        rec = True
                    elif('stop' in s):
                        self.board.stop()
                        rec = True
                        flush = True
                    if rec == False:
                        print("Command not recognized...")

                elif s:
                    for c in s:
                        if sys.hexversion > 0x03000000:
                            self.board.ser.write(bytes(c, 'utf-8'))
                        else:
                            self.board.ser.write(bytes(c))
                        time.sleep(0.100)

                line = ''
                time.sleep(0.1) #Wait to see if the board has anything to report
                while self.board.ser.inWaiting():
                    c = self.board.ser.read().decode('utf-8', errors='replace')
                    line += c
                    time.sleep(0.001)
                    if (c == '\n') and not flush:
                        # print('%\t'+line[:-1])
                        line = ''

                #if not flush:
                    #print(line)

            # Take user input
            #s = input('--> ')
            if sys.hexversion > 0x03000000:
                #print('输入/stop可以停止')
                #s = input('--> ')
                s = input('Streaming data now...')
                
            else:
                #print('输入/stop可以停止')
                #s = raw_input('--> ')
                s = raw_input('Streaming data now...')
                

def main():
    lsl = StreamerLSL()
    #print("create lsl")
    lsl.create_lsl()
    #print("begin")
    lsl.begin()

if __name__ == '__main__':
    main()

