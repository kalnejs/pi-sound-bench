
import os
import subprocess
import select
import multiprocessing
import time


class GPIO:

    BASE_PATH          = "/sys/class/gpio"
    EXPORT_PATH        = BASE_PATH + "/export"

    PATH               = BASE_PATH + "/gpio%d"
    DIRECTION_PATH     = PATH + "/direction"
    EDGE_PATH          = PATH + "/edge"
    VALUE_PATH         = PATH + "/value"

    EDGE_NONE          = "none"
    EDGE_RISING        = "rising"
    EDGE_FALLING       = "falling"

    DIRECTION_IN       = "in"
    DIRECTION_OUT      = "out"

    DIRECTIONS = (DIRECTION_IN, DIRECTION_OUT)
    EDGES = (EDGE_NONE, EDGE_RISING, EDGE_FALLING)

    def __init__(self, number, direction, callback=None, edge=EDGE_NONE):

        assert(direction in GPIO.DIRECTIONS)
        assert(edge in GPIO.EDGES)
        assert(number > 0 and number < 25)

        self.number = number
        self.direction = direction
        self.callback  = callback

        self.value_file = open(GPIO.VALUE_PATH % self.number, 'r+')

        with open(GPIO.EXPORT_PATH, 'w') as file:
                    file.write('%d' % number)

        with open(GPIO.DIRECTION_PATH % self.number, 'w') as file:
                    file.write(direction)

        if(edge != "none"):
            with open(GPIO.EDGE_PATH, 'w') as file:
                file.write(edge)  

            self.epoll = select.epoll(1)
            self.epoll.register(self.value_file.fileno(), select.EPOLLIN | select.EPOLLET)
            self.proc = multiprocessing.Process(target=self.event_loop, args=(self))
            self.proc.start()

    def set(self, value):
        if(value):
            self.value_file.write("1")
            self.value_file.seek(0)
        else:
            self.value_file.write("0")
            self.value_file.seek(0)           

    def event_loop(self):
        print("GPIO: starting event_loop")

        while True:
            events = self.epoll.poll(1)
            for fileno, event in events:
                if fileno == self.value_file.fileno():
                    print("shitme")

class StoragePlayer:

    MEDIA_BASE_PATH = "/media/"
    MEDIA_AUDIO_EXTENSIONS = ['.mp3', '.wav']

    def __init__(self):
        media_path = StoragePlayer.MEDIA_BASE_PATH + os.getlogin() + "/"
        media_list = os.listdir(media_path)

        if(not len(media_list)):
            self.base_path = ""
            return

        self.base_path = media_path + media_list[0]

    def get_audio_list(self, base_folder=""):

        if(not self.base_path):
            print("StoragePlayer: No media detected...")
            return []

        list = os.listdir(self.base_path + base_folder)

        file_list = filter(lambda item: os.path.isfile(self.base_path + base_folder+ "/" + item), list)

        if(not len(file_list)):
            print("StoragePlayer: No files detected in path...")
            return []

        audio_list = filter(lambda item: [ele for ele in StoragePlayer.MEDIA_AUDIO_EXTENSIONS if(ele in item)], file_list)

        if(not len(audio_list)):
            print("StoragePlayer: No audio files detected in path...")
            return []

        return audio_list 




if __name__ == '__main__':  
    player = StoragePlayer()

    print(player.get_audio_list())

    pin2 = GPIO(2, GPIO.DIRECTION_OUT)
    
    for x in range(100):
        pin2.set(1)
        time.sleep(1)
        pin2.set(0)