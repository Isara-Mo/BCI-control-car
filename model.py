import numpy as np
import math
from scipy import signal
from sklearn.cross_decomposition import CCA
from scipy.signal import  resample
###author:Richong pang
##time:2024/7/25
def resample_eeg_data(x, fs):
    resample_list = []
    for channel in range(x.shape[0]):
        resample_list.append(resample(x[channel], fs))
    return np.array(resample_list)
class FBCCA():
    def __init__(self,Num_haimonics,fs,sample_len,Num_fb,n_components):
        self.Num_haimonics=Num_haimonics#设置滤波器组
        self.fs=fs#设置信号频率
        self.sample_len=sample_len#样本长度
        self.Num_fb=Num_fb#滤波器组
        self.n_components=n_components#CCA的主成分
    def Filter_Bank(self,data):
        filter_data = np.zeros((self.Num_fb, data.shape[0], data.shape[1]))
        nyq = self.fs / 2
        passband = [6, 14, 22, 30, 38, 46, 54, 62, 70, 78]
        stopband = [4, 10, 16, 24, 32, 40, 48, 56, 64, 72]
        high_pass, high_stop = 80, 90
        gp, gs, Rp = 3, 40, 0.5
        for i in range(self.Num_fb):
            Wp = [passband[i] / nyq, high_pass / nyq]
            Ws = [stopband[i] / nyq, high_stop / nyq]
            [N, Wn] = signal.cheb1ord(Wp, Ws, gp, gs)
            [B, A] = signal.cheby1(N, Rp, Wn, 'bandpass')
            data = signal.filtfilt(B, A, data, padlen=3 * (max(len(B), len(A)) - 1)).copy()
            filter_data[i, :, :] = data
        return filter_data
    def Reference_Signal(self,targets,phases):
        reference_signals = []
        t = np.arange(0, (self.sample_len / self.fs), step=1.0 / self.fs)
        for i in range(len(targets)):
            ref = []
            for j in range(1, self.Num_haimonics + 1):
                ref.append(np.sin(2 * np.pi * j * targets[i] * t+np.pi * phases[i]))
                ref.append(np.cos(2 * np.pi * j * targets[i] * t+np.pi * phases[i]))
            reference_signals.append(np.array(ref))
        reference_signals = np.array(reference_signals)
        return reference_signals
    def Target_Matching(self,data,ref):
        cca = CCA(self.n_components)
        corr = np.zeros(self.n_components)
        targets_num = ref.shape[0]
        result = np.zeros(targets_num)
        for i in range(0,targets_num):
            cca.fit(data.T, ref[i].T)
            x_a, y_b = cca.transform(data.T, ref[i].T)
            for j in range(0, 1):
                corr[j] = np.corrcoef(x_a[:, j], y_b[:, j])[0, 1]
                result[i] = np.max(corr)
        return result
    def Classify(self,data,target,phases):
        ref = self.Reference_Signal(targets=target,phases=phases)
        data =self.Filter_Bank(data)
        fb_coefs = [math.pow(i, -1.25) + 0.25 for i in range(1,self.Num_fb + 1)]
        result = np.zeros(len(target))
        for fb_i in range(0, self.Num_fb):
            x = data[fb_i, :, :]
            w = fb_coefs[fb_i]
            result += (w * (self.Target_Matching(x, ref) ** 2))
        predicted = np.argmax(result) + 1
        return predicted





import numpy as np
import math
from scipy import signal
from sklearn.cross_decomposition import CCA
import scipy.io
# eeg:channels*points
Fs = 250
T = 1000


def filter_bank(eeg):
    Nm = 3
    result = np.zeros((Nm, eeg.shape[0], eeg.shape[1]))
    nyq = Fs / 2
    passband = [6, 14, 22, 30, 38, 46, 54, 62, 70, 78]
    stopband = [4, 10, 16, 24, 32, 40, 48, 56, 64, 72]
    highcut_pass, highcut_stop = 80, 90
    gpass, gstop, Rp = 3, 40, 0.5

    for i in range(Nm):
        Wp = [passband[i] / nyq, highcut_pass / nyq]
        Ws = [stopband[i] / nyq, highcut_stop / nyq]
        [N, Wn] = signal.cheb1ord(Wp, Ws, gpass, gstop)
        [B, A] = signal.cheby1(N, Rp, Wn, 'bandpass')
        data = signal.filtfilt(B, A, eeg, padlen=3 * (max(len(B), len(A)) - 1)).copy()
        result[i, :, :] = data

    return result


def get_Reference_Signal(num_harmonics=4):
    targets = [8, 9, 10, 11, 12, 13]
    reference_signals = []
    t = np.arange(0, (T / Fs), step=1.0 / Fs)
    for f in targets:
        reference_f = []
        for h in range(1, num_harmonics + 1):
            reference_f.append(np.sin(2 * np.pi * h * f * t)[0:T])
            reference_f.append(np.cos(2 * np.pi * h * f * t)[0:T])
        reference_signals.append(reference_f)
    reference_signals = np.asarray(reference_signals)
    return reference_signals


def find_correlation(X, Y):
    cca = CCA(1)
    corr = np.zeros(1)
    num_freq = Y.shape[0]
    result = np.zeros(num_freq)
    for freq_idx in range(0, num_freq):
        matched_X = X
        cca.fit(matched_X.T, Y[freq_idx].T)
        # cca.fit(X.T, Y[freq_idx].T)
        x_a, y_b = cca.transform(matched_X.T, Y[freq_idx].T)
        for i in range(0, 1):
            corr[i] = np.corrcoef(x_a[:, i], y_b[:, i])[0, 1]
            result[freq_idx] = np.max(corr)
    return result


def fbcca_classify(data):
    reference_signals = get_Reference_Signal()
    data = filter_bank(data)
    predicted_class = []
    labels = []
    Nm = 3
    fb_coefs = [math.pow(i, -1.25) + 0.25 for i in range(1, Nm + 1)]  # w(n) = n^(-0.5) + 1.25
    result = np.zeros(6)
    for fb_i in range(0, Nm):
        x = data[fb_i, :, :]
        y = reference_signals
        w = fb_coefs[fb_i]
        result += (w * (find_correlation(x, y) ** 2))

    predicted = np.argmax(result) + 1
    return predicted
