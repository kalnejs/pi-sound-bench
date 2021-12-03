
import os
import subprocess
import select
import threading
import time
import sys
import pty

class GPIO:

    BASE_PATH          = '/sys/class/gpio'
    EXPORT_PATH        = BASE_PATH + '/export'

    PATH               = BASE_PATH + '/gpio%d'
    DIRECTION_PATH     = PATH + '/direction'
    EDGE_PATH          = PATH + '/edge'
    VALUE_PATH         = PATH + '/value'

    EDGE_NONE          = 'none'
    EDGE_RISING        = 'rising'
    EDGE_FALLING       = 'falling'

    DIRECTION_IN       = 'in'
    DIRECTION_OUT      = 'out'

    DIRECTIONS = (DIRECTION_IN, DIRECTION_OUT)
    EDGES = (EDGE_NONE, EDGE_RISING, EDGE_FALLING)

    def __init__(self, number, direction, callback=None, edge=EDGE_NONE):

        assert(direction in GPIO.DIRECTIONS)
        assert(edge in GPIO.EDGES)
        assert(number > 0 and number < 28)

        self.skip = 3
        self.number = number
        self.direction = direction
        self.callback  = callback
        # self.timer = None
        self.lock = threading.Lock()

        if(not os.path.isdir(GPIO.PATH % self.number)):
            print("GPIO: exporting...")
            with open(GPIO.EXPORT_PATH, 'w') as file:
                        file.write('%d' % self.number)

        time.sleep(1)

        self.value_file = open(GPIO.VALUE_PATH % self.number, 'r+')

        print("GPIO: setting direction...")
        with open(GPIO.DIRECTION_PATH % self.number, 'w') as file:
                    file.write(direction)

        time.sleep(1)

        if(edge != GPIO.EDGE_NONE):
            print("GPIO: setting edge...")
            with open(GPIO.EDGE_PATH % self.number, 'w') as file:
                file.write(edge)  

            self.epoll = select.epoll(1)
            self.epoll.register(self.value_file.fileno(), select.EPOLLIN | select.EPOLLET)
            # self.proc = multiprocessing.Process(target=self.event_loop)
            self.proc = threading.Thread(target=self.event_loop)
            self.proc.start()

    def set(self, value):
        if(value):
            print("GPIO: write 1...")
            self.value_file.write('1')
            self.value_file.seek(0)
        else:
            print("GPIO: write 0...")
            self.value_file.write('0')
            self.value_file.seek(0)           

    def get(self):
        val = self.value_file.read()
        self.value_file.seek(0)
        return int(val)

    def check_and_call(self):
        # print("event_loop: checking...")
        if(self.get() and callable(self.callback)):
            self.callback()

        self.lock.release()

    def event_loop(self):
        print('GPIO: starting event_loop')
        while True:
            events = self.epoll.poll(1)
            for fileno, event in events:
                if fileno == self.value_file.fileno():
                    # print("event_loop: event...")
                    if not self.lock.acquire(blocking=False):
                        # print("event_loop: lock false...")
                        continue

                    # print("event_loop: starting...")
                    t = threading.Timer(0.1, self.check_and_call)
                    t.start()

class StoragePlayer:

    MEDIA_BASE_PATH = '/media/'
    MEDIA_AUDIO_EXTENSIONS = ['.mp3', '.wav']

    def __init__(self, base_folder=''):
        media_path = StoragePlayer.MEDIA_BASE_PATH + os.getlogin() + '/'
        media_list = os.listdir(media_path)

        self.subproc = None

        if(not len(media_list)):
            raise Exception('No media list...')

        self.base_path = media_path + media_list[0]
        self.audio_list = dict()

        if(not self.base_path):
            raise Exception('No media detected...')

        list = os.listdir(self.base_path + base_folder)

        file_list = [item for item in list if os.path.isfile(self.base_path + base_folder+ '/' + item)]

        if(not len(file_list)):
            raise Exception('No files detected in path...')

        audio_list  = [item for item in file_list if [subitem for subitem in StoragePlayer.MEDIA_AUDIO_EXTENSIONS if(subitem in item)]]

        if(not len(audio_list)):
            raise Exception('No audio files detected in path...')

        for item in audio_list:
            self.audio_list[item] = self.base_path + base_folder + '/' + item

        self.pty_master, self.pty_slave = os.openpty()

    def get_audio_list(self, base_folder=''):
        return sorted(self.audio_list.values())


    def play(self, path):
        self.subproc = subprocess.Popen(['mpg123','-C','-f','10000', path], stdin=self.pty_master)

    def stop(self):
        if(not self.subproc):
            return

        # os.write(self.pty_slave, b'q')
        # time.sleep(0.5)
        self.subproc.kill()
        self.subproc = None

if __name__ == '__main__':  
    player = StoragePlayer()
    
    list = player.get_audio_list()

    # print(list)

    # if(not len(list)):
    #     exit()

    # player.play(list[0])

    # time.sleep(3)

    # player.stop()

    def event27():
        player.stop()
        player.play(list[0])
        print('Event27')


    def event22():
        player.stop()
        player.play(list[1])
        print('Event22')

    pin27 = GPIO(27, GPIO.DIRECTION_IN, event27, GPIO.EDGE_RISING)
    pin22 = GPIO(22, GPIO.DIRECTION_IN, event22, GPIO.EDGE_RISING)

    # input = GPIO(21, GPIO.DIRECTION_IN, event, GPIO.EDGE_FALLING)
    
    # for x in range(100):
    #     pin.set(1)
    #     time.sleep(0.5)
    #     pin.set(0)
    #     time.sleep(0.5)