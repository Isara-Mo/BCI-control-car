import os
import time
import numpy as np
import pandas as pd
from pylsl import StreamInlet, resolve_stream
def lsl_received(queue,path):
    while True:
        streams = resolve_stream('type', 'EEG')
        inlet = StreamInlet(streams[0])
        eeg_data = []
        content = queue.get()
        if content.startswith("st"):
            flag=0
            while True:
                sample, timestamp = inlet.pull_sample()
                eeg_data.append(sample)
                if not queue.empty():
                    content= queue.get()
                    if content == "ending":
                        break
            eeg_data = np.array(eeg_data)
            pd.DataFrame(eeg_data).to_csv(os.path.join(path, "{}.csv".format("temp")))
        elif content == "del":
            print("quit")
            break

